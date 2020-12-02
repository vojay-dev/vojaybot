import json
import logging
from abc import abstractmethod
from typing import List

import requests

from vojaybot.twitch import CommandHandler

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


class StreamElementsPointsCommandHandler(CommandHandler):
    """
    This Handler can be used to combine any other Handlers with the StreamElements points system. It will only
    call the other handler if the user has enough points. It also adds custom transaction success and failure
    messages to the CommandResult so that they appear as additional chat messages.

    To use this, you have derive from this Class and implement the failed and succeed methods. They should return
    a customized text that fits to your channel.

    This is because you might have different names for your StreamElements points or want to use a different
    language.
    """

    def __init__(self, costs: int, handler: CommandHandler, se_client: StreamElementsClient):
        super().__init__()
        self._costs = costs
        self._handler = handler
        self._se_client = se_client

    @abstractmethod
    def _transaction_failed(self, user: str, points: int):
        pass

    @abstractmethod
    def _transaction_succeed(self, user: str, points_new: int):
        pass

    @CommandHandler.message_processor.setter
    def message_processor(self, processor):
        self._handler.message_processor = processor
        self._message_processor = processor

    def handle(self, user: str, command: str, args: List[str]) -> bool:
        points = self._se_client.get_points(user)
        if points < self._costs:
            self.send_chat_message(self._transaction_failed(user, points))
            return False

        success = self._handler.handle(user, command, args)

        if not success:
            return False

        points_new = self._se_client.reduce_points(user, self._costs)

        self.send_chat_message(self._transaction_succeed(user, points_new))
        return True
