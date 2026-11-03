"""Rock-paper-scissors against the bot with a bet."""

from typing import Optional

from ..db import User
from .base import Game, Reply

MIN_BET = 1
MAX_BET = 20
ALL_IN = "ва-банк"
XP_PLAY = 5
XP_WIN = 10

# key beats value
BEATS = {"камень": "ножницы", "ножницы": "бумага", "бумага": "камень"}
EMOJI = {"камень": "✊", "ножницы": "✌️", "бумага": "✋"}


class RockPaperScissors(Game):
    title = "Камень-ножницы-бумага"

    def __init__(self, db, rng, owner: User):
        super().__init__(db, rng)
        self.owner_id = owner.user_id
        self.owner_name = owner.name
        self.bet: Optional[int] = None

    def start_message(self) -> str:
        return (
            f"✊✌️✋ Камень-ножницы-бумага!\n"
            f"{self.owner_name}, сделай ставку от {MIN_BET} до {MAX_BET} "
            f"или напиши «{ALL_IN}»."
        )

    def handle(self, user: User, text: str) -> Optional[Reply]:
        if user.user_id != self.owner_id:
            return None
        if self.bet is None:
            return self._take_bet(user, text)
        if text not in BEATS:
            return None
        return self._play(user, text)

    def _take_bet(self, user: User, text: str) -> Optional[Reply]:
        if text in BEATS:
            return Reply(["Сначала сделай ставку."])
        if text == ALL_IN:
            bet = user.balance
        elif text.isdigit():
            bet = int(text)
            if not MIN_BET <= bet <= MAX_BET:
                return Reply([f"Ставка должна быть от {MIN_BET} до {MAX_BET}."])
        else:
            return None

        if user.balance <= 0:
            return Reply(["У тебя нет баллов. Забери «бонус» и возвращайся."], finished=True)
        if bet > user.balance:
            return Reply([f"Не хватает баллов: у тебя {user.balance}."])

        self.bet = bet
        return Reply([f"Ставка {bet} принята. Камень, ножницы или бумага?"])

    def _play(self, user: User, choice: str) -> Reply:
        bot_choice = self.rng.choice(list(BEATS))
        out = [f"{EMOJI[choice]} против {EMOJI[bot_choice]} ({bot_choice})."]

        if choice == bot_choice:
            out.append("Ничья, баллы остаются при тебе.")
            self.pay(user, 0, XP_PLAY, out)
        elif BEATS[choice] == bot_choice:
            out.append(f"Ты выиграл! +{self.bet}.")
            self.pay(user, self.bet, XP_WIN, out)
        else:
            out.append(f"Ты проиграл. −{self.bet}.")
            self.pay(user, -self.bet, XP_PLAY, out)

        out.append("Ещё раз — «игра 2».")
        return Reply(out, finished=True)
