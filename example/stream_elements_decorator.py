from vojaybot.handler.dice import DiceHandler
from vojaybot.stream_elements import StreamElementsClient, StreamElementsPointsDecorator
from vojaybot.twitch import TwitchBot

if __name__ == '__main__':
    bot_username = 'your_twitch_account'
    channel_name = 'your_twitch_channel'

    # Get token at https://twitchapps.com/tmi/
    oauth_token = 'oauth_token'

    bot = TwitchBot(bot_username, channel_name, oauth_token)

    # Apart from the bot, we need a Stream Elements client, the token and channel_id can be seen in your account
    jwt_token = 'stream_elements_jwt_token'
    channel_id = 'stream_elements_channel_id'

    se_client = StreamElementsClient(jwt_token, channel_id)

    stream_elements_dice_handler = StreamElementsPointsDecorator(DiceHandler(), 10, se_client)

    bot.register_handler('dice', stream_elements_dice_handler)
    bot.run()
