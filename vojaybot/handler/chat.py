from typing import List

import toml

from vojaybot.twitch import CommandHandler


def register_chat_handlers(handlers, bot):
    """
    Register a set of chat handlers that respond with a static message. Those messages can have a {user}
    placeholder and aliases can be defined. The handlers parameter must be a dictionary with the following
    format:

    {
        "hi": {"aliases": ["hello"], "response": "Hi {user}"},
        "bye": {"aliases": ["cya"], "response": "Bye {user}"}
    }

    :param handlers: Dictionary with handler definitions
    :param bot: An instance of vojaybot.twitch.TwitchBot
    :return: None
    """
    for command, meta in handlers.items():
        response = meta['response']
        aliases = meta['aliases']

        bot.register_handler(command, ChatHandler(response), *aliases)


def register_chat_handlers_from_toml_config(config, bot):
    commands_config = toml.load(config)
    commands = commands_config['commands']

    register_chat_handlers(commands, bot)


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
