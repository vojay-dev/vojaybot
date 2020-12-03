import logging

import toml
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown

from vojaybot.handler.dice import DiceHandler
from vojaybot.handler.hue_light import HueLightHandler
from vojaybot.stream_elements import StreamElementsClient, StreamElementsPointsCommandHandler
from vojaybot.twitch import TwitchBot

console = Console(color_system="windows")

console.print(Markdown('# Vojay Bot'))

logging.basicConfig(
    format='%(message)s',
    datefmt='[%X]',
    level=logging.INFO,
    handlers=[RichHandler(console=console)]
)


class VCoinsHandler(StreamElementsPointsCommandHandler):

    def _transaction_failed(self, user: str, points: int):
        return f'Hi @{user}, du brauchst mindestens {self._costs} vcoins, schaue fleißig weiter :)'

    def _transaction_succeed(self, user: str, points_new: int):
        return f'Hi @{user}, dir wurden {self._costs} vcoins abgezogen, du hast noch {points_new} vcoins :)'


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

    # With your own implementation of the StreamElementsPointsCommandHandler you can easily wrap any other Handler
    # to add costs to it based on the StreamElements points system
    bot.register_handler('waste-points', VCoinsHandler(100, DiceHandler(), se_client))

    # The HueLightHandler allows viewers to control Philips Hue lights, in combination with the previously described
    # StreamElementsPointsCommandHandler it is possible to add costs based on StreamElements points for it.
    # The HueLightHAndler also allows to add a customized usage message in case someone provided invalid arguments.
    costs = 10
    usage = f'Mache mit "!licht an" oder "!licht aus" alle Lichter an oder aus. Mit "!licht blau" änderst du die ' \
            f'Farbe. Du kannst auch nur ein bestimmtes Licht ändern, zum Beispiel mit "!licht rechts grün". Jede ' \
            f'Aktion kostet dich {costs} vcoins, mit "!licht farben" siehst du alle Farben.'

    hue_light_handler = HueLightHandler(bridge_ip, lights, usage)
    # If running for the first time, you need to press the Hue bridge button and call the following method once.
    # After that it is not necessary to run connect again.
    # hue_light_handler.connect()

    light_handler = VCoinsHandler(costs, hue_light_handler, se_client)

    bot.register_handler('light', light_handler, 'licht')

    bot.run()
