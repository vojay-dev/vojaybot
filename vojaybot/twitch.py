import logging
import socket
import ssl
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from queue import Queue
from typing import List, Dict

from rich import box
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.progress import Progress, BarColumn
from rich.table import Table

console = Console(color_system='windows', record=True)
console.print(Markdown('# Vojay Bot'))

# https://youtrack.jetbrains.com/issue/PY-39762
# noinspection PyArgumentList
logging.basicConfig(
    format='%(message)s',
    datefmt='[%X]',
    level=logging.INFO,
    handlers=[RichHandler(console=console)]
)

logger = logging.getLogger(__name__)

# This queue is used to process messages that should be send back to Twitch
twitch_send_message_queue = Queue()


class CommandHandler(ABC):

    @abstractmethod
    def handle(self, user: str, command: str, args: List[str]) -> bool:
        pass

    @staticmethod
    def _send_chat_message(message: str) -> None:
        twitch_send_message_queue.put(message)


class CommandHandlerDecorator(CommandHandler, ABC):

    @abstractmethod
    def _pre_handle(self, user: str, command: str, args: List[str]) -> bool:
        pass

    @abstractmethod
    def _post_handle(self, user: str, command: str, args: List[str]) -> bool:
        pass

    def __init__(self, handler: CommandHandler):
        self._command_handler = handler

    def handle(self, user: str, command: str, args: List[str]) -> bool:
        pre_success = self._pre_handle(user, command, args)

        if not pre_success:
            return False

        handler_success = self._command_handler.handle(user, command, args)

        if not handler_success:
            return False

        post_success = self._post_handle(user, command, args)

        return pre_success and handler_success and post_success


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
            # All user input is converted to lower case to simplify handling in command handlers
            message_components = chat_message.lower().split()

            command = message_components[0][1:].lower()
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

    def __init__(self, bot_username, channel_name, oauth_token, command_handling_thread_pool_size=4):
        self._bot_username = bot_username
        self._channel_name = channel_name
        self._oauth_token = oauth_token

        # Incoming commands are handled by threads in this ThreadPoolExecutor
        self._executor = ThreadPoolExecutor(command_handling_thread_pool_size)

        self._handlers: Dict[str, CommandHandler] = {}

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        self._irc = context.wrap_socket(sock)

    def register_handler(self, command: str, handler: CommandHandler, *aliases: str):
        handler.message_processor = self._send_chat_message

        # Commands are registered as lower case strings to make it more easy for users to use them
        self._handlers[command.lower()] = handler

        for alias in aliases:
            self._handlers[alias] = handler

    def _read(self):
        while True:
            data = self._irc.recv(1024)
            raw_message = data.decode('UTF-8')

            for line in raw_message.splitlines():
                logger.debug(line)

                # Keep in mind that due to the global interpreter lock (GIL) only one thread at a time can be
                # executed. This is not multiprocessing, however it is still useful because Python can
                # switch between the threads whenever one of them is ready to do some work. It hardly depends on
                # what the commands are actually doing but this way, we at least offer the possibility to
                # utilize this feature. In the future this might be replaced with actual multiprocessing.
                self._executor.submit(self._handle, line)

    def _write(self):
        while True:
            # Handlers are able to access the message queue instance, whenever they want to send a message to Twitch,
            # they can simply add it to the queue and this function then takes care of actually sending it.
            message = twitch_send_message_queue.get()
            self._send_chat_message(message)

    def _connect(self):
        with Progress(
                'Connecting to Twitch IRC',
                '|',
                BarColumn(bar_width=None),
                '|',
                auto_refresh=True,
                console=console
        ) as progress:
            connection_task = progress.add_task('', total=4)
            self._irc.connect(('irc.chat.twitch.tv', 6697))
            time.sleep(0.1)
            progress.update(connection_task, advance=1)

            self._send(f'PASS {self._oauth_token}')
            time.sleep(0.1)
            progress.update(connection_task, advance=1)

            self._send(f'NICK {self._bot_username}')
            time.sleep(0.1)
            progress.update(connection_task, advance=1)

            self._send(f'JOIN #{self._channel_name}')
            time.sleep(0.1)
            progress.update(connection_task, advance=1)

    def run(self):
        console.print(Markdown('Starting bot with the following `handlers` registered...'))
        console.print(Markdown('## Registered Handler'))

        table = Table(show_header=True, header_style='bold magenta', expand=True, box=box.SIMPLE_HEAVY)

        table.add_column('command', style='cyan')
        table.add_column('handler')

        for command, handler in self._handlers.items():
            table.add_row(command, type(handler).__name__)

        console.print(table)

        self._connect()

        console.print(Markdown('Twitch connection successful and bot started! `Have fun`!'))
        console.print(Markdown('## Log'))

        read_thread = threading.Thread(target=self._read)
        write_thread = threading.Thread(target=self._write)

        read_thread.start()
        write_thread.start()

        read_thread.join()
        write_thread.join()
