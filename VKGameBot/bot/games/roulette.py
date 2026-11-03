"""Russian roulette: 8 chambers, one bullet, players pick numbers in turn."""

from typing import Optional

from ..db import User
from .base import Game, Reply

CHAMBERS = 8
PENALTY = 10
XP_SAFE = 5
XP_SHOT = 2


class Roulette(Game):
    title = "Русская рулетка"

    def __init__(self, db, rng):
        super().__init__(db, rng)
        self.bullet = rng.randint(1, CHAMBERS)
        self.taken: set[int] = set()

    def start_message(self) -> str:
        return (
            f"🔫 Русская рулетка! В барабане {CHAMBERS} гнёзд и один патрон.\n"
            f"Называйте по очереди число от 1 до {CHAMBERS}. "
            "Каждый следующий удачный выстрел приносит больше баллов, "
            f"а попавшийся на патрон теряет {PENALTY}."
        )

    def handle(self, user: User, text: str) -> Optional[Reply]:
        if not text.isdigit():
            return None
        number = int(text)
        if not 1 <= number <= CHAMBERS:
            return Reply([f"Нужно число от 1 до {CHAMBERS}."])
        if number in self.taken:
            return Reply([f"Число {number} уже было, выбери другое."])

        out: list[str] = []
        if number == self.bullet:
            out.append(f"💥 Бах! {user.name} теряет {PENALTY} баллов. Игра окончена.")
            self.pay(user, -PENALTY, XP_SHOT, out)
            return Reply(out, finished=True)

        self.taken.add(number)
        reward = len(self.taken)
        out.append(f"😮‍💨 Щёлк... {user.name} везёт: +{reward}.")
        self.pay(user, reward, XP_SAFE, out)

        if len(self.taken) == CHAMBERS - 1:
            out.append(
                f"Остался только патрон в гнезде {self.bullet}. "
                "Все уцелели, игра окончена!"
            )
            return Reply(out, finished=True)

        out.append("Следующий!")
        return Reply(out)
