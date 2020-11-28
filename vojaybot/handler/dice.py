import random
from typing import List, Optional

from vojaybot.twitch import CommandHandler, CommandResult


class DiceHandler(CommandHandler):

    def handle(self, user: str, command: str, args: List[str]) -> CommandResult:
        return CommandResult(True, f'@{user}: {random.randint(1, 6)}')
