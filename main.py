import toml

from vojaybot.handler.chat import register_chat_handlers_from_toml_config
from vojaybot.handler.dice import DiceHandler
from vojaybot.handler.hue_light import HueLightHandler
from vojaybot.stream_elements import StreamElementsClient, StreamElementsPointsDecorator
from vojaybot.twitch import TwitchBot

if __name__ == '__main__':
    # See: https://en.wikipedia.org/wiki/TOML
    config = toml.load('config/config.toml')

    bot_username = config['twitch']['bot_username']
    channel_name = config['twitch']['channel_name']
    oauth_token = config['twitch']['oauth_token']

    bridge_ip = config['hue']['bridge_ip']
    lights = config['hue']['lights']

    jwt_token = config['streamelements']['jwt_token']
    channel_id = config['streamelements']['channel_id']

    se_client = StreamElementsClient(jwt_token, channel_id)

    # Get token at https://twitchapps.com/tmi/
    bot = TwitchBot(bot_username, channel_name, oauth_token)

    # Each bot command is basically a handler, handling that command. You can also specify aliases to use the same
    # Handler with multiple commands.
    bot.register_handler('dice', DiceHandler())

    # With the StreamElementsPointsDecorator you can easily wrap any other Handler to add costs to it based on the
    # StreamElements points system
    bot.register_handler('waste-points', StreamElementsPointsDecorator(DiceHandler(), 100, se_client))

    # The HueLightHandler allows viewers to control Philips Hue lights, in combination with the previously described
    # StreamElementsPointsDecorator it is possible to add costs based on StreamElements points for it.
    # The HueLightHAndler also allows to add a customized usage message in case someone provided invalid arguments.
    costs = 10
    usage = f'Mache mit "!licht an" oder "!licht aus" alle Lichter an oder aus. Mit "!licht blau" änderst du die ' \
            f'Farbe. Du kannst auch nur ein bestimmtes Licht ändern, zum Beispiel mit "!licht rechts grün". Jede ' \
            f'Aktion kostet dich {costs} vcoins, mit "!licht farben" siehst du alle Farben.'

    hue_light_handler = HueLightHandler(bridge_ip, lights, usage)

    # If running for the first time, you need to press the Hue bridge button and call the following method once.
    # After that it is not necessary to run connect again.
    # hue_light_handler.connect()

    # This example shows how to use the StreamElementsPointsDecorator in combination with the HueLightHandler.
    # It is also possible to add custom messages to indicate that the transaction was successful or failed.
    transaction_succeed_msg = 'Hi @{user}, dir wurden {costs} vcoins abgezogen, du hast noch {points_new} vcoins :)'
    transaction_failed_msg = 'Hi @{user}, du brauchst mindestens {costs} vcoins, schaue fleißig weiter :)'

    light_handler = StreamElementsPointsDecorator(
        hue_light_handler,
        costs,
        se_client,
        transaction_succeed_msg,
        transaction_failed_msg
    )

    bot.register_handler('light', light_handler, 'licht')

    # With register_chat_handlers we have a quick way to add static, simple chat commands. This can cover all commands
    # which should just respond with a fixed text message. You can easily configure them in a toml file and add all
    # commands at once like this. If you use {user} somewhere in the response text, it automatically gets replaced
    # with the user that sent the command.
    register_chat_handlers_from_toml_config('config/commands.toml', bot)

    bot.run()
