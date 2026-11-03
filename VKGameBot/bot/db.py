"""SQLite storage for players."""

import sqlite3
from dataclasses import dataclass
from typing import Optional

from .levels import level_for_xp

START_BALANCE = 100


@dataclass
class User:
    user_id: int
    name: str
    balance: int
    xp: int
    last_bonus: float

    @property
    def level(self) -> int:
        return level_for_xp(self.xp)


class Database:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                name       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
                balance    INTEGER NOT NULL,
                xp         INTEGER NOT NULL DEFAULT 0,
                last_bonus REAL    NOT NULL DEFAULT 0
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _to_user(row: Optional[sqlite3.Row]) -> Optional[User]:
        return User(**dict(row)) if row else None

    def get_user(self, user_id: int) -> Optional[User]:
        row = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return self._to_user(row)

    def name_taken(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM users WHERE name = ?", (name,)
        ).fetchone()
        return row is not None

    def register(self, user_id: int, name: str) -> User:
        self.conn.execute(
            "INSERT INTO users (user_id, name, balance) VALUES (?, ?, ?)",
            (user_id, name, START_BALANCE),
        )
        self.conn.commit()
        return self.get_user(user_id)

    def rename(self, user_id: int, name: str) -> None:
        self.conn.execute(
            "UPDATE users SET name = ? WHERE user_id = ?", (name, user_id)
        )
        self.conn.commit()

    def change_balance(self, user_id: int, delta: int) -> int:
        """Add delta to the balance (it never goes below zero). Returns the new balance."""
        self.conn.execute(
            "UPDATE users SET balance = MAX(balance + ?, 0) WHERE user_id = ?",
            (delta, user_id),
        )
        self.conn.commit()
        return self.get_user(user_id).balance

    def add_xp(self, user_id: int, amount: int) -> tuple[int, int]:
        """Add experience. Returns (old_level, new_level)."""
        old = self.get_user(user_id).level
        self.conn.execute(
            "UPDATE users SET xp = xp + ? WHERE user_id = ?", (amount, user_id)
        )
        self.conn.commit()
        return old, self.get_user(user_id).level

    def set_last_bonus(self, user_id: int, timestamp: float) -> None:
        self.conn.execute(
            "UPDATE users SET last_bonus = ? WHERE user_id = ?", (timestamp, user_id)
        )
        self.conn.commit()

    def top(self, limit: int = 10) -> list[User]:
        rows = self.conn.execute(
            "SELECT * FROM users ORDER BY balance DESC, xp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._to_user(r) for r in rows]
