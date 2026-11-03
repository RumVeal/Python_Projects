import random

import pytest

from bot.core import BONUS_AMOUNT, BONUS_COOLDOWN, GameBot
from bot.db import START_BALANCE, Database
from bot.games.blackjack import Blackjack, hand_value
from bot.games.roulette import PENALTY, Roulette

CHAT = 2000000001
ALICE = 1
BOB = 2


class FakeClock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def bot(clock):
    return GameBot(Database(), rng=random.Random(42), clock=clock)


def say(bot, user, text):
    return "\n".join(bot.handle_message(CHAT, user, text))


def register(bot, user, name):
    assert "Добро пожаловать" in say(bot, user, f"регистрация {name}")


def balance(bot, user):
    return bot.db.get_user(user).balance


# ---------- registration and profile ----------

def test_register_keeps_full_name(bot):
    register(bot, ALICE, "PrEaChEr")
    assert bot.db.get_user(ALICE).name == "PrEaChEr"
    assert balance(bot, ALICE) == START_BALANCE


def test_register_twice_and_taken_name(bot):
    register(bot, ALICE, "Timur")
    assert "уже зарегистрирован" in say(bot, ALICE, "регистрация Other")
    assert "занято" in say(bot, BOB, "регистрация timur")


def test_bad_name(bot):
    assert "от 2 до 16" in say(bot, ALICE, "регистрация [id1|x]")
    assert "Напиши имя" in say(bot, ALICE, "регистрация")


def test_rename_keeps_balance(bot):
    register(bot, ALICE, "Old")
    bot.db.change_balance(ALICE, 23)
    assert "теперь ты New Name" in say(bot, ALICE, "сменить имя New Name")
    user = bot.db.get_user(ALICE)
    assert (user.name, user.balance) == ("New Name", START_BALANCE + 23)


def test_unregistered_user_is_asked_to_register(bot):
    assert "зарегистрируйся" in say(bot, ALICE, "профиль")
    assert "зарегистрируйся" in say(bot, ALICE, "игра 1")


def test_unknown_messages_are_ignored(bot):
    register(bot, ALICE, "Timur")
    assert bot.handle_message(CHAT, ALICE, "привет всем") == []
    assert bot.handle_message(CHAT, ALICE, "") == []


def test_mention_prefix_is_stripped(bot):
    register(bot, ALICE, "Timur")
    assert "Баллы" in say(bot, ALICE, "[club209623454|@bot], профиль")


def test_bonus_once_per_day(bot, clock):
    register(bot, ALICE, "Timur")
    assert f"+{BONUS_AMOUNT}" in say(bot, ALICE, "бонус")
    assert "уже получен" in say(bot, ALICE, "бонус")
    clock.now += BONUS_COOLDOWN
    assert f"+{BONUS_AMOUNT}" in say(bot, ALICE, "бонус")
    assert balance(bot, ALICE) == START_BALANCE + 2 * BONUS_AMOUNT


def test_top(bot):
    register(bot, ALICE, "Alice")
    register(bot, BOB, "Bob")
    bot.db.change_balance(BOB, 50)
    top = say(bot, ALICE, "топ")
    assert top.index("Bob") < top.index("Alice")


def test_balance_never_negative(bot):
    register(bot, ALICE, "Timur")
    bot.db.change_balance(ALICE, -1000)
    assert balance(bot, ALICE) == 0


def test_xp_gives_levels(bot):
    register(bot, ALICE, "Timur")
    assert bot.db.add_xp(ALICE, 250) == (0, 2)


# ---------- games management ----------

def test_one_game_per_chat_and_stop(bot):
    register(bot, ALICE, "Timur")
    say(bot, ALICE, "игра 1")
    assert "Сейчас идёт" in say(bot, ALICE, "игра 2")
    assert "остановлена" in say(bot, ALICE, "стоп")
    assert "нет активной игры" in say(bot, ALICE, "стоп")


def test_games_in_different_chats_are_independent(bot):
    register(bot, ALICE, "Timur")
    bot.handle_message(CHAT, ALICE, "игра 1")
    reply = bot.handle_message(CHAT + 1, ALICE, "игра 3")
    assert "Блэкджек" in reply[0]


# ---------- roulette ----------

def start_roulette(bot, bullet):
    say(bot, ALICE, "игра 1")
    game = bot.games[CHAT]
    assert isinstance(game, Roulette)
    game.bullet = bullet
    return game


def test_roulette_shot(bot):
    register(bot, ALICE, "Timur")
    start_roulette(bot, bullet=3)
    assert "+1" in say(bot, ALICE, "1")
    assert "уже было" in say(bot, ALICE, "1")
    assert "+2" in say(bot, ALICE, "2")
    assert "Бах" in say(bot, ALICE, "3")
    assert balance(bot, ALICE) == START_BALANCE + 1 + 2 - PENALTY
    assert CHAT not in bot.games


def test_roulette_everybody_survives(bot):
    register(bot, ALICE, "Timur")
    start_roulette(bot, bullet=8)
    for n in range(1, 8):
        reply = say(bot, ALICE, str(n))
    assert "Все уцелели" in reply
    assert balance(bot, ALICE) == START_BALANCE + sum(range(1, 8))


# ---------- rock-paper-scissors ----------

def test_rps_needs_bet_first(bot):
    register(bot, ALICE, "Timur")
    say(bot, ALICE, "игра 2")
    assert "Сначала сделай ставку" in say(bot, ALICE, "камень")
    assert "от 1 до 20" in say(bot, ALICE, "50")
    assert "принята" in say(bot, ALICE, "10")


def test_rps_only_owner_plays(bot):
    register(bot, ALICE, "Timur")
    register(bot, BOB, "Bob")
    say(bot, ALICE, "игра 2")
    assert bot.handle_message(CHAT, BOB, "10") == []


@pytest.mark.parametrize("bot_choice,expected", [
    ("ножницы", 10), ("камень", 0), ("бумага", -10),
])
def test_rps_result(bot, bot_choice, expected):
    register(bot, ALICE, "Timur")
    say(bot, ALICE, "игра 2")
    say(bot, ALICE, "10")
    bot.games[CHAT].rng = type("R", (), {"choice": lambda self, seq: bot_choice})()
    say(bot, ALICE, "камень")
    assert balance(bot, ALICE) == START_BALANCE + expected
    assert CHAT not in bot.games


def test_rps_all_in(bot):
    register(bot, ALICE, "Timur")
    say(bot, ALICE, "игра 2")
    assert f"Ставка {START_BALANCE}" in say(bot, ALICE, "ва-банк")


# ---------- blackjack ----------

@pytest.mark.parametrize("cards,value", [
    (["10♠", "7♥"], 17),
    (["Т♠", "К♥"], 21),
    (["Т♠", "Т♥"], 12),
    (["Т♠", "9♥", "5♦"], 15),
    (["К♠", "Д♥", "2♦"], 22),
])
def test_hand_value(cards, value):
    assert hand_value(cards) == value


def start_blackjack(bot, deck):
    """deck is listed in the order the cards are drawn."""
    say(bot, ALICE, "игра 3")
    game = bot.games[CHAT]
    assert isinstance(game, Blackjack)
    game.deck = list(reversed(deck))
    return game


def test_blackjack_join_validation(bot):
    register(bot, ALICE, "Timur")
    say(bot, ALICE, "игра 3")
    assert "Укажи ставку" in say(bot, ALICE, "принять")
    assert "от 20 до 50" in say(bot, ALICE, "принять 100")
    assert "садится" in say(bot, ALICE, "принять 30")
    assert "уже за столом" in say(bot, ALICE, "принять 30")


def test_blackjack_full_round(bot):
    register(bot, ALICE, "Alice")
    register(bot, BOB, "Bob")
    # Alice: 10 6, Bob: 9 8, dealer: 10 6, then Alice hits 4 (=20), dealer draws 5 (=21)
    start_blackjack(bot, ["10♠", "6♠", "9♥", "8♥", "10♦", "6♦", "4♣", "5♣"])
    say(bot, ALICE, "принять 20")
    say(bot, BOB, "принять 30")
    assert "Ход Alice" in say(bot, ALICE, "готово")
    assert "Сейчас ходит Alice" in say(bot, BOB, "хватит")
    assert "(20)" in say(bot, ALICE, "ещё")
    result = say(bot, ALICE, "хватит")
    assert "Ход Bob" in result
    result = say(bot, BOB, "хватит")
    assert "Дилер: 10♦ 6♦ 5♣ (21)" in result
    assert balance(bot, ALICE) == START_BALANCE - 20
    assert balance(bot, BOB) == START_BALANCE - 30
    assert CHAT not in bot.games


def test_blackjack_bust_and_dealer_bust(bot):
    register(bot, ALICE, "Alice")
    register(bot, BOB, "Bob")
    # Alice: 10 6 + К -> bust; Bob: 10 9 stands; dealer: 10 6 + 8 -> bust
    start_blackjack(bot, ["10♠", "6♠", "10♥", "9♥", "10♦", "6♦", "К♣", "8♣"])
    say(bot, ALICE, "принять 20")
    say(bot, BOB, "принять 30")
    say(bot, ALICE, "готово")
    assert "перебор" in say(bot, ALICE, "ещё")
    result = say(bot, BOB, "хватит")
    assert "Bob: победа, +30" in result
    assert balance(bot, ALICE) == START_BALANCE - 20
    assert balance(bot, BOB) == START_BALANCE + 30


def test_blackjack_natural_pays_3_to_2(bot):
    register(bot, ALICE, "Alice")
    # Alice: Т К (blackjack), dealer: 10 7
    start_blackjack(bot, ["Т♠", "К♠", "10♦", "7♦"])
    say(bot, ALICE, "принять 20")
    result = say(bot, ALICE, "готово")
    assert "блэкджек, +30" in result
    assert balance(bot, ALICE) == START_BALANCE + 30
