import logging
import socket
import ssl
from abc import ABC, abstractmethod
from typing import List, Dict, Callable

logger = logging.getLogger(__name__)


class CommandHandler(ABC):

    def __init__(self):
        self._message_processor: Callable[[str], None] = lambda message: None

    @abstractmethod
    def handle(self, user: str, command: str, args: List[str]) -> bool:
        pass

    def send_chat_message(self, message: str) -> None:
        self.message_processor(message)

    @property
    def message_processor(self) -> Callable[[str], None]:
        return self._message_processor

    @message_processor.setter
    def message_processor(self, processor: Callable[[str], None]):
        self._message_processor = processor


class TwitchBot:

    @staticmethod
    def _parse(data):
        components = data.split()
        command = components[1]

        if command == 'PRIVMSG':
            # See: https://tools.ietf.org/html/rfc1459#section-2.3.1
            user, host = components[0].split('!')[1].split('@')
            channel = components[2]
            message = ' '.join(components[3:])[1:]

            return {'user': user, 'host': host, 'channel': channel, 'message': message}

        return None

    def _send(self, message):
        self._irc.send(bytes(f'{message}\r\n', 'UTF-8'))

    def _send_chat_message(self, message):
        self._send(f'PRIVMSG #{self._channel_name} :{message}')

    def _handle_ping(self):
        self._irc.send('PONG :tmi.twitch.tv\r\n'.encode('UTF-8'))

    def _handle_chat(self, raw_message):
        parsed_message = self._parse(raw_message)
        logger.info(parsed_message)

        user = parsed_message['user']
        chat_message = parsed_message['message']

        if chat_message.startswith('!'):
            message_components = chat_message.split()

            command = message_components[0][1:]
            args = message_components[1:]

            if command in self._handlers:
                logger.info(f'{user} sent command {command} with args {args}')

                handler = self._handlers[command]
                success = handler.handle(user, command, args)

                logger.info(f'command {command} {"succeeded" if success else "failed"}')
            else:
                logger.info(f'no handler for command {command}')

    def _handle(self, raw_message):
        if raw_message.startswith('PING :tmi.twitch.tv'):
            self._handle_ping()
        else:
            components = raw_message.split()
            command = components[1]

            if command == 'PRIVMSG':
                self._handle_chat(raw_message)

    def __init__(self, bot_username, channel_name, oauth_token):
        self._bot_username = bot_username
        self._channel_name = channel_name
        self._oauth_token = oauth_token

        self._handlers: Dict[str, CommandHandler] = {}

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        self._irc = context.wrap_socket(sock)

    def register_handler(self, command: str, handler: CommandHandler, *aliases: str):
        handler.message_processor = self._send_chat_message
        self._handlers[command] = handler

        for alias in aliases:
            self._handlers[alias] = handler

    def run(self):
        self._irc.connect(('irc.chat.twitch.tv', 6697))

        self._send(f'PASS {self._oauth_token}')
        self._send(f'NICK {self._bot_username}')
        self._send(f'JOIN #{self._channel_name}')

        while True:
            data = self._irc.recv(1024)
            raw_message = data.decode('UTF-8')

            for line in raw_message.splitlines():
                logger.debug(line)
                self._handle(line)
