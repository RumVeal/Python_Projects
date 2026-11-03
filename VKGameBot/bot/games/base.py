"""Common parts of all games."""

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from ..db import Database, User


@dataclass
class Reply:
    messages: list[str] = field(default_factory=list)
    finished: bool = False


class Game(ABC):
    title: str = ""

    def __init__(self, db: Database, rng: random.Random):
        self.db = db
        self.rng = rng

    @abstractmethod
    def start_message(self) -> str:
        """Text sent when the game starts."""

    @abstractmethod
    def handle(self, user: User, text: str) -> Optional[Reply]:
        """Process a message. Return None if the message is not meant for this game."""

    def pay(self, user: User, amount: int, xp: int, out: list[str]) -> None:
        """Change the player's balance, give experience and announce a level-up."""
        if amount:
            self.db.change_balance(user.user_id, amount)
        if xp:
            old, new = self.db.add_xp(user.user_id, xp)
            if new > old:
                out.append(f"🎉 {user.name} получает {new} уровень!")
