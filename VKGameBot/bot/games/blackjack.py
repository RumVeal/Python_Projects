"""Blackjack for several players against the dealer."""

from dataclasses import dataclass, field
from typing import Optional

from ..db import User
from .base import Game, Reply

MIN_BET = 20
MAX_BET = 50
MAX_PLAYERS = 6
DEALER_STANDS_ON = 17
XP_PLAY = 5
XP_WIN = 15

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "В", "Д", "К", "Т"]
SUITS = ["♠", "♥", "♦", "♣"]

HIT = {"еще", "ещё", "карту"}
STAND = {"хватит", "оставить", "пас"}


def card_value(card: str) -> int:
    rank = card[:-1]
    if rank == "Т":
        return 11
    if rank in ("В", "Д", "К"):
        return 10
    return int(rank)


def hand_value(cards: list[str]) -> int:
    """Hand value; aces count as 11 or 1, whichever is better."""
    total = sum(card_value(c) for c in cards)
    aces = sum(1 for c in cards if c.startswith("Т"))
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_blackjack(cards: list[str]) -> bool:
    return len(cards) == 2 and hand_value(cards) == 21


def show(cards: list[str]) -> str:
    return f"{' '.join(cards)} ({hand_value(cards)})"


@dataclass
class Player:
    user: User
    bet: int
    cards: list[str] = field(default_factory=list)
    done: bool = False


class Blackjack(Game):
    title = "Блэкджек"

    def __init__(self, db, rng):
        super().__init__(db, rng)
        self.players: dict[int, Player] = {}
        self.order: list[int] = []
        self.turn = 0
        self.started = False
        self.deck = [r + s for r in RANKS for s in SUITS]
        rng.shuffle(self.deck)
        self.dealer: list[str] = []

    def start_message(self) -> str:
        return (
            "🃏 Блэкджек! Садитесь за стол: напишите «принять 30» "
            f"(ставка от {MIN_BET} до {MAX_BET}).\n"
            "Когда все сядут — «готово»."
        )

    # ---------- lobby ----------

    def handle(self, user: User, text: str) -> Optional[Reply]:
        if not self.started:
            if text == "принять" or text.startswith("принять "):
                return self._join(user, text)
            if text == "готово":
                return self._deal()
            return None
        return self._turn(user, text)

    def _join(self, user: User, text: str) -> Reply:
        if user.user_id in self.players:
            return Reply([f"{user.name}, ты уже за столом."])
        if len(self.players) >= MAX_PLAYERS:
            return Reply([f"Мест нет, максимум {MAX_PLAYERS} игроков."])
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            return Reply([f"Укажи ставку, например «принять 30»."])
        bet = int(parts[1])
        if not MIN_BET <= bet <= MAX_BET:
            return Reply([f"Ставка должна быть от {MIN_BET} до {MAX_BET}."])
        if bet > user.balance:
            return Reply([f"{user.name}, не хватает баллов: у тебя {user.balance}."])

        self.players[user.user_id] = Player(user, bet)
        self.order.append(user.user_id)
        return Reply([f"{user.name} садится за стол со ставкой {bet}. Игроков: {len(self.players)}."])

    def _draw(self) -> str:
        return self.deck.pop()

    def _deal(self) -> Reply:
        if not self.players:
            return Reply(["За столом никого нет. Напишите «принять 30»."])
        self.started = True
        out = ["Раздаю карты!"]
        for uid in self.order:
            p = self.players[uid]
            p.cards = [self._draw(), self._draw()]
            line = f"{p.user.name}: {show(p.cards)}"
            if is_blackjack(p.cards):
                p.done = True
                line += " — блэкджек!"
            out.append(line)
        self.dealer = [self._draw(), self._draw()]
        out.append(f"Дилер: {self.dealer[0]} 🂠")
        return self._next_turn(out)

    # ---------- players' turns ----------

    def _current(self) -> Player:
        return self.players[self.order[self.turn]]

    def _turn(self, user: User, text: str) -> Optional[Reply]:
        if text not in HIT and text not in STAND:
            return None
        player = self._current()
        if user.user_id != player.user.user_id:
            return Reply([f"Сейчас ходит {player.user.name}."])

        out: list[str] = []
        if text in HIT:
            player.cards.append(self._draw())
            value = hand_value(player.cards)
            if value > 21:
                out.append(f"{player.user.name}: {show(player.cards)} — перебор!")
                player.done = True
            elif value == 21:
                out.append(f"{player.user.name}: {show(player.cards)} — 21!")
                player.done = True
            else:
                out.append(f"{player.user.name}: {show(player.cards)}. Ещё или хватит?")
                return Reply(out)
        else:
            out.append(f"{player.user.name} останавливается на {hand_value(player.cards)}.")
            player.done = True

        self.turn += 1
        return self._next_turn(out)

    def _next_turn(self, out: list[str]) -> Reply:
        while self.turn < len(self.order) and self._current().done:
            self.turn += 1
        if self.turn < len(self.order):
            p = self._current()
            out.append(f"Ход {p.user.name}: {show(p.cards)}. Ещё или хватит?")
            return Reply(out)
        return self._finish(out)

    # ---------- dealer and results ----------

    def _finish(self, out: list[str]) -> Reply:
        alive = [p for p in self.players.values() if hand_value(p.cards) <= 21]
        if alive:
            while hand_value(self.dealer) < DEALER_STANDS_ON:
                self.dealer.append(self._draw())
        dealer_value = hand_value(self.dealer)
        out.append(f"Дилер: {show(self.dealer)}" + (" — перебор!" if dealer_value > 21 else ""))

        for uid in self.order:
            p = self.players[uid]
            value = hand_value(p.cards)
            name = p.user.name
            if value > 21:
                out.append(f"{name}: перебор, −{p.bet}.")
                self.pay(p.user, -p.bet, XP_PLAY, out)
            elif is_blackjack(p.cards) and not is_blackjack(self.dealer):
                win = p.bet * 3 // 2
                out.append(f"{name}: блэкджек, +{win}!")
                self.pay(p.user, win, XP_WIN, out)
            elif dealer_value > 21 or value > dealer_value:
                out.append(f"{name}: победа, +{p.bet}!")
                self.pay(p.user, p.bet, XP_WIN, out)
            elif value == dealer_value:
                out.append(f"{name}: ничья, ставка возвращается.")
                self.pay(p.user, 0, XP_PLAY, out)
            else:
                out.append(f"{name}: проигрыш, −{p.bet}.")
                self.pay(p.user, -p.bet, XP_PLAY, out)

        out.append("Игра окончена. Ещё партию — «игра 3».")
        return Reply(out, finished=True)
