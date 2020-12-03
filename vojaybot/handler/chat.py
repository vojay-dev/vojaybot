from typing import List

import toml

from vojaybot.twitch import CommandHandler


def register_chat_handlers(config, bot):
    commands_config = toml.load(config)
    commands = commands_config['commands']

    for command, meta in commands.items():
        response = meta['response']
        aliases = meta['aliases']

        bot.register_handler(command, ChatHandler(response), *aliases)


class ChatHandler(CommandHandler):

    def __init__(self, response: str):
        self._response = response

    def handle(self, user: str, command: str, args: List[str]) -> bool:
        message = self._response.format(user=user)

        self._send_chat_message(message)
        return True

    @property
    def response(self):
        return self._response
