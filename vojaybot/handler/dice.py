import random
from typing import List

from vojaybot.twitch import CommandHandler


class DiceHandler(CommandHandler):

    def handle(self, user: str, command: str, args: List[str]) -> bool:
        self.send_chat_message(f'@{user}: {random.randint(1, 6)}')
        return True
