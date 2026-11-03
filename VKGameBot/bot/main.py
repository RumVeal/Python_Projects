"""Entry point: connects to VK and passes messages to GameBot."""

import logging
import time

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id

from .config import load_config
from .core import GameBot
from .db import Database

log = logging.getLogger("bot")

API_VERSION = "5.199"


def run() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    config = load_config()
    session = vk_api.VkApi(token=config.token, api_version=API_VERSION)
    vk = session.get_api()
    bot = GameBot(Database(config.db_path))

    while True:
        try:
            longpoll = VkBotLongPoll(session, config.group_id)
            log.info("Bot started, listening for messages")
            for event in longpoll.listen():
                if event.type != VkBotEventType.MESSAGE_NEW:
                    continue
                # new API versions wrap the message, old ones send it as is
                message = event.message or event.obj
                if message["from_id"] < 0:  # ignore other bots and communities
                    continue
                replies = bot.handle_message(
                    message["peer_id"], message["from_id"], message.get("text", "")
                )
                if replies:
                    vk.messages.send(
                        peer_id=message["peer_id"],
                        message="\n\n".join(replies),
                        random_id=get_random_id(),
                    )
        except KeyboardInterrupt:
            log.info("Stopped")
            break
        except Exception:
            log.exception("Connection error, reconnecting in 5 seconds")
            time.sleep(5)


if __name__ == "__main__":
    run()
