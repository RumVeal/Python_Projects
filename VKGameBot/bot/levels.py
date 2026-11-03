"""Experience and levels."""

XP_PER_LEVEL = 100


def level_for_xp(xp: int) -> int:
    return xp // XP_PER_LEVEL


def xp_to_next_level(xp: int) -> int:
    return XP_PER_LEVEL - xp % XP_PER_LEVEL
