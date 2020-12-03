from typing import List, Optional

from phue import Bridge

from vojaybot.twitch import CommandHandler


class HueLightHandler(CommandHandler):

    # These are hand crafted xy colors, might need adjustments depending on Hue light setup
    COLORS = {
        **dict.fromkeys(['teal', 'türkis'], (0.2581, 0.3904)),
        **dict.fromkeys(['red', 'rot'], (0.6434, 0.3178)),
        **dict.fromkeys(['purple', 'lila'], (0.337, 0.1512)),
        **dict.fromkeys(['blue', 'blau'], (0.1426, 0.1286)),
        **dict.fromkeys(['cyan'], (0.1618, 0.3365)),
        **dict.fromkeys(['green', 'grün'], (0.2094, 0.6713)),
        **dict.fromkeys(['white', 'weiß'], (0.4475, 0.4027)),
        **dict.fromkeys(['orange'], (0.5355, 0.4492)),
    }

    STATE_ON_NAMES = ['on', 'an']
    STATE_OFF_NAMES = ['aus', 'off']

    COLOR_COMMAND_ALIASES = ['colors', 'farben']

    def __init__(self, bridge_ip, lights, usage):
        self._bridge = Bridge(bridge_ip)

        self._lights = lights
        self._usage = usage

    def connect(self):
        """
        If running for the first time, you need to press the Hue bridge button and call this method once.
        After that it is not necessary to run connect again.
        """
        self._bridge.connect()

    def _handle_color(self, color_xy, hue_light_ids):
        for hue_light_id in hue_light_ids:
            self._bridge.set_light(hue_light_id, 'on', True)
            self._bridge.set_light(hue_light_id, 'xy', color_xy)

    def _handle_switch(self, on_state, hue_light_ids):
        for hue_light_id in hue_light_ids:
            self._bridge.set_light(hue_light_id, 'on', on_state)

    def _get_hue_light_id(self, light_name) -> Optional[str]:
        for key in self._lights:
            if light_name == key or light_name in self._lights[key]['aliases']:
                return self._lights[key]['hue_light_id']

        return None

    def _get_hue_light_ids(self):
        ids = []

        for key in self._lights:
            ids.append(self._lights[key]['hue_light_id'])

        return ids

    def _get_color(self, name) -> Optional[str]:
        if name in self.COLORS:
            return self.COLORS[name]

        return None

    @staticmethod
    def _is_valid_state(name):
        return name in HueLightHandler.STATE_ON_NAMES + HueLightHandler.STATE_OFF_NAMES

    @staticmethod
    def _get_state(name):
        """
        true -> light on
        false -> light off
        """
        return name in HueLightHandler.STATE_ON_NAMES

    def handle(self, user: str, command: str, args: List[str]) -> bool:
        if len(args) < 1:
            self._send_chat_message(self._usage)
            return False

        if args[0] in HueLightHandler.COLOR_COMMAND_ALIASES:
            self._send_chat_message(f'''@{user}, {', '.join(self.COLORS.keys())}''')
            return False

        # If first argument is a state (e.g. on, off), switch all lights on or off
        if self._is_valid_state(args[0]):
            state = self._get_state(args[0])
            self._handle_switch(state, self._get_hue_light_ids())
            return True

        # If first argument is a color (e.g. red), colorize all lights
        if color := self._get_color(args[0]):
            self._handle_color(color, self._get_hue_light_ids())
            return True

        # If first argument is a Hue light name, only change that specific light
        if hue_light_id := self._get_hue_light_id(args[0]):
            # If second argument is a state (e.g. on, off) switch that specific light on or off
            if self._is_valid_state(args[1]):
                state = self._get_state(args[1])
                self._handle_switch(state, [hue_light_id])
                return True

            # If second argument is a color (e.g. red) colorize that specific light
            if color := self._get_color(args[1]):
                self._handle_color(color, [hue_light_id])
                return True

        # Invalid arguments
        self._send_chat_message(self._usage)
        return False
