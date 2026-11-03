# VK Game Bot

A game bot for VK group chats: players register, earn points and levels, and play
Russian roulette, rock-paper-scissors and blackjack against each other and the bot.

The first version was one of my first Python projects (~2020). This is a full rewrite
of it: SQLite instead of JSON files, separate game modules, per-chat game state,
error handling and tests.

## Features
- **Profiles** — registration, points, experience and levels, daily bonus, leaderboard
- **Russian roulette** — 8 chambers, one bullet, each lucky shot pays more than the previous one
- **Rock-paper-scissors** — play against the bot with a bet (or go all-in)
- **Blackjack** — up to 6 players vs the dealer, real deck, soft aces, 3:2 payout for a natural blackjack
- Each chat has its own game, so several chats can play at the same time

## Commands (in Russian, as the bot speaks Russian)

| Command | Description |
|---|---|
| `регистрация <имя>` | Create a profile (+100 points) |
| `сменить имя <имя>` | Change name |
| `профиль` | Points, level, experience |
| `бонус` | +50 points once a day |
| `топ` | Leaderboard |
| `игра 1` / `рулетка` | Russian roulette — then send a number 1–8 |
| `игра 2` / `кнб` | Rock-paper-scissors — bet `1`–`20` or `ва-банк`, then `камень` / `ножницы` / `бумага` |
| `игра 3` / `блэкджек` | Blackjack — `принять 30` to join, `готово` to deal, then `ещё` / `хватит` |
| `стоп` | Stop the current game |
| `помощь` | List of commands |

## Project structure
```
bot/
├── main.py        # VK connection (Bots Long Poll)
├── core.py        # command routing, profiles, games per chat
├── db.py          # SQLite storage
├── levels.py      # experience → level
├── config.py      # settings from .env
└── games/
    ├── base.py
    ├── roulette.py
    ├── rps.py
    └── blackjack.py
tests/
└── test_bot.py    # pytest, no VK connection needed
```
The bot logic (`core.py`) doesn't depend on VK: it takes a message and returns reply texts,
so everything can be tested without a real group.

## Setup
1. Create a VK community → **Manage → API usage**:
   - create an access token with the *messages* permission;
   - in **Long Poll API** enable it and turn on the *Message received* event.
2. In **Messages → Bot settings** enable bot features and allow adding the bot to chats.
3. Install and run:
```bash
cd VKGameBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # put your token and group id there
python -m bot
```
4. Add the bot to a chat and give it access to messages (or make it an admin), then write `помощь`.

## Tests
```bash
cd VKGameBot
pip install pytest
python -m pytest
```

## Tech stack
Python 3.10+ · vk_api · SQLite · pytest
