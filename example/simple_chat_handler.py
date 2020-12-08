from vojaybot.handler.chat import register_chat_handlers
from vojaybot.twitch import TwitchBot

if __name__ == '__main__':
    bot_username = 'your_twitch_account'
    channel_name = 'your_twitch_channel'

    # Get token at https://twitchapps.com/tmi/
    oauth_token = 'oauth_token'

    commands = {
        'hi': {'aliases': ['hello'], 'response': 'Hi {user}'},
        'bye': {'aliases': ['cya'], 'response': 'Bye {user}'}
    }

    bot = TwitchBot(bot_username, channel_name, oauth_token)
    register_chat_handlers(commands, bot)

    bot.run()
