import json
import logging
from typing import List

import requests

from vojaybot.twitch import CommandHandler, CommandHandlerDecorator

logger = logging.getLogger(__name__)


class StreamElementsClient:
    """
    See: https://docs.streamelements.com/reference
    """

    def __init__(self, jwt_token, channel_id, base_uri='https://api.streamelements.com/kappa/v2'):
        self._jwt_token = jwt_token
        self._channel_id = channel_id
        self._base_uri = base_uri

        self._headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {jwt_token}'
        }

    def get_points(self, user: str) -> int:
        url = f'{self._base_uri}/points/{self._channel_id}/{user}'
        response = requests.request('GET', url, headers=self._headers)

        if not response.ok:
            logger.info(f'request to {url} failed with {response.text}')
            return 0

        return int(json.loads(response.text)['points'])

    def reduce_points(self, user: str, points: int) -> int:
        if points < 0:
            raise ValueError('points must be >= 0')

        url = f'{self._base_uri}/points/{self._channel_id}/{user}/-{points}'
        response = requests.request("PUT", url, headers=self._headers)

        if not response.ok:
            logger.info(f'request to {url} failed with {response.text}')
            return 0

        return int(json.loads(response.text)['newAmount'])


class StreamElementsPointsDecorator(CommandHandlerDecorator):
    """
    This Decorator can be used to decorate any CommandHandler with the StreamElements points system. Before the
    decorated handler is executed, the _pre_handle function checks if the viewer has enough points to execute
    the command based on the configured costs.

    If he has not enough points, he receives the transaction_failed_msg. If he has enough points, the decorated
    handler is executed and as soon as this was successful (means: it returned True) the costs are removed from
    his account and he receives the transaction_succeed_msg.

    You can use the following placeholders in transaction_failed_msg and transaction_succeed_msg:

    * user: Name of the viewer that wants to execute the command
    * costs: Configured costs for the command
    * points: Amount of StreamElements points before the transaction
    * points_new: Amount of StreamElements points after the transaction

    Example: Hi {user}, not enough points ({points} < {costs})

    This allows to adjust the messages to your stream configuration (e.g. when the StreamElements points have a custom
    name for you).
    """

    def __init__(
        self,
        handler: CommandHandler,
        costs: int,
        se_client: StreamElementsClient,
        transaction_succeed_msg: str = 'Hi {user}, for {command} you used {costs} points, {points_new} points left',
        transaction_failed_msg: str = 'Hi {user}, not enough points ({points} < {costs})'
    ):
        super().__init__(handler)

        self._costs = costs
        self._se_client = se_client

        self._transaction_succeed_msg = transaction_succeed_msg
        self._transaction_failed_msg = transaction_failed_msg

    def _format_message(self, message, user, command, points, points_new):
        return message.format(user=user, command=command, points=points, points_new=points_new, costs=self._costs)

    def _pre_handle(self, user: str, command: str, args: List[str]) -> bool:
        points = self._se_client.get_points(user)

        if points < self._costs:
            self._send_chat_message(self._format_message(self._transaction_failed_msg, user, command, points, points))
            return False

        return True

    def _post_handle(self, user: str, command: str, args: List[str]) -> bool:
        points = self._se_client.get_points(user)
        points_new = self._se_client.reduce_points(user, self._costs)

        self._send_chat_message(self._format_message(self._transaction_succeed_msg, user, command, points, points_new))
        return True
