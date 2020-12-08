import random
from typing import List

from vojaybot.twitch import TwitchBot, CommandHandler


class RandomHandler(CommandHandler):

    def handle(self, user: str, command: str, args: List[str]) -> bool:
        self._send_chat_message(f'Hi {user}: {random.randint(1, 6)}')
        return True


if __name__ == '__main__':
    bot_username = 'your_twitch_account'
    channel_name = 'your_twitch_channel'

    # Get token at https://twitchapps.com/tmi/
    oauth_token = 'oauth_token'

    bot = TwitchBot(bot_username, channel_name, oauth_token)
    bot.register_handler('random', RandomHandler(), 'zufall')

    bot.run()
