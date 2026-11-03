"""Bot logic: commands, registration and per-chat games.

Independent of VK — takes a message, returns reply texts.
That makes it easy to test (see tests/).
"""

import logging
import random
import re
import time
from typing import Callable, Optional

from .db import START_BALANCE, Database, User
from .games import Blackjack, Game, RockPaperScissors, Roulette
from .levels import xp_to_next_level

log = logging.getLogger(__name__)

BONUS_AMOUNT = 50
BONUS_COOLDOWN = 24 * 60 * 60
NAME_RE = re.compile(r"^[\w\- ]{2,16}$")
MENTION_RE = re.compile(r"^\[club\d+\|[^\]]*\][,\s]*")
GAME_WORDS = re.compile(r"^(\d+|принять.*|камень|ножницы|бумага|ва-банк|еще|хватит|оставить)$")

HELP = """🤖 Команды:
• регистрация <имя> — создать профиль (+100 баллов)
• сменить имя <имя>
• профиль — баланс, уровень и опыт
• бонус — +50 баллов раз в сутки
• топ — рейтинг игроков

🎮 Игры:
• игра 1 / рулетка — русская рулетка
• игра 2 / кнб — камень-ножницы-бумага на ставку
• игра 3 / блэкджек — блэкджек против дилера
• стоп — закончить текущую игру"""


def normalize(text: str) -> tuple[str, str]:
    """Return (clean text, lowercase text) without the bot mention."""
    clean = MENTION_RE.sub("", text or "").strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean, clean.lower().replace("ё", "е")


class GameBot:
    def __init__(
        self,
        db: Database,
        rng: Optional[random.Random] = None,
        clock: Callable[[], float] = time.time,
    ):
        self.db = db
        self.rng = rng or random.Random()
        self.clock = clock
        self.games: dict[int, Game] = {}  # peer_id -> active game

    def handle_message(self, peer_id: int, user_id: int, text: str) -> list[str]:
        raw, msg = normalize(text)
        if not msg:
            return []
        try:
            return self._dispatch(peer_id, user_id, raw, msg)
        except Exception:
            log.exception("Error while handling %r", text)
            return ["Что-то пошло не так 😕 Попробуй ещё раз."]

    # ---------- routing ----------

    def _dispatch(self, peer_id: int, user_id: int, raw: str, msg: str) -> list[str]:
        user = self.db.get_user(user_id)

        if msg in ("помощь", "команды", "начать", "help"):
            return [HELP]
        if msg.startswith("регистрация"):
            return self._register(user_id, user, raw[len("регистрация"):].strip())
        if msg.startswith("сменить имя"):
            return self._rename(user, raw[len("сменить имя"):].strip())
        if msg == "топ":
            return [self._top()]
        if msg in ("автор", "создатель"):
            return ["Меня написал RumVeal — github.com/RumVeal"]

        game_cmd = self._game_for_command(msg)
        if game_cmd or msg in ("профиль", "баланс", "уровень", "бонус"):
            if user is None:
                return ["Сначала зарегистрируйся: «регистрация Имя»."]
            if msg in ("профиль", "баланс", "уровень"):
                return [self._profile(user)]
            if msg == "бонус":
                return [self._bonus(user)]
            return self._start_game(peer_id, user, game_cmd)

        if msg in ("стоп", "закончить игру"):
            return self._stop(peer_id)

        game = self.games.get(peer_id)
        if game is None:
            return []
        if user is None:
            if GAME_WORDS.match(msg):
                return ["Сначала зарегистрируйся: «регистрация Имя»."]
            return []
        reply = game.handle(user, msg)
        if reply is None:
            return []
        if reply.finished:
            del self.games[peer_id]
        return reply.messages

    # ---------- profile ----------

    def _register(self, user_id: int, user: Optional[User], name: str) -> list[str]:
        if user is not None:
            return [f"Ты уже зарегистрирован как {user.name}."]
        error = self._check_name(name)
        if error:
            return [error]
        self.db.register(user_id, name)
        return [
            f"Добро пожаловать, {name}! На счёт зачислено {START_BALANCE} баллов.\n"
            "Список команд — «помощь»."
        ]

    def _rename(self, user: Optional[User], name: str) -> list[str]:
        if user is None:
            return ["Сначала зарегистрируйся: «регистрация Имя»."]
        if name.lower() == user.name.lower():
            return ["Это и так твоё имя."]
        error = self._check_name(name)
        if error:
            return [error]
        self.db.rename(user.user_id, name)
        return [f"Готово, теперь ты {name}."]

    def _check_name(self, name: str) -> Optional[str]:
        if not name:
            return "Напиши имя после команды, например «регистрация Preacher»."
        if not NAME_RE.match(name):
            return "Имя: от 2 до 16 символов — буквы, цифры, пробел, _ или -."
        if self.db.name_taken(name):
            return f"Имя {name} уже занято."
        return None

    def _profile(self, user: User) -> str:
        return (
            f"👤 {user.name}\n"
            f"💰 Баллы: {user.balance}\n"
            f"⭐ Уровень: {user.level} (до следующего {xp_to_next_level(user.xp)} опыта)"
        )

    def _bonus(self, user: User) -> str:
        now = self.clock()
        left = user.last_bonus + BONUS_COOLDOWN - now
        if left > 0:
            hours, minutes = int(left // 3600), int(left % 3600 // 60)
            return f"Бонус уже получен. Следующий через {hours} ч {minutes} мин."
        self.db.set_last_bonus(user.user_id, now)
        balance = self.db.change_balance(user.user_id, BONUS_AMOUNT)
        return f"🎁 +{BONUS_AMOUNT} баллов! Теперь у тебя {balance}."

    def _top(self) -> str:
        users = self.db.top()
        if not users:
            return "Пока никто не зарегистрирован."
        lines = ["🏆 Топ игроков:"]
        for i, u in enumerate(users, 1):
            lines.append(f"{i}. {u.name} — {u.balance} баллов, ур. {u.level}")
        return "\n".join(lines)

    # ---------- games ----------

    @staticmethod
    def _game_for_command(msg: str) -> Optional[str]:
        if msg in ("игра 1", "рулетка"):
            return "roulette"
        if msg in ("игра 2", "кнб"):
            return "rps"
        if msg in ("игра 3", "блэкджек", "блекджек"):
            return "blackjack"
        return None

    def _start_game(self, peer_id: int, user: User, kind: str) -> list[str]:
        current = self.games.get(peer_id)
        if current is not None:
            return [f"Сейчас идёт «{current.title}». Закончите её или напишите «стоп»."]
        if kind == "roulette":
            game: Game = Roulette(self.db, self.rng)
        elif kind == "rps":
            game = RockPaperScissors(self.db, self.rng, user)
        else:
            game = Blackjack(self.db, self.rng)
        self.games[peer_id] = game
        return [game.start_message()]

    def _stop(self, peer_id: int) -> list[str]:
        game = self.games.pop(peer_id, None)
        if game is None:
            return ["Сейчас нет активной игры."]
        return [f"«{game.title}» остановлена."]
