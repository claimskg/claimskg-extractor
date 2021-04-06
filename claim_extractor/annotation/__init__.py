import json
import logging
from abc import ABC, abstractmethod

from nerd import nerd_client


class Annotator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def annotate(self, text) -> str:
        pass


class EntityFishingAnnotator(Annotator):
    def __init__(self, api_uri="http://localhost:8090/service/"):
        super().__init__()
        self._api_uri = api_uri
        self._client = nerd_client.NerdClient(apiBase=self._api_uri)

    def annotate(self, text, language="eng") -> str:
        """
        function that can use entity-fishing online: https://github.com/hirmeos/entity-fishing-client-python
        """
        # Disable the logger.debug message
        logging.config.dictConfig({
            'version': 1,
            'disable_existing_loggers': True,
        })

        response = self.client.disambiguate_text(text, language=language)
        return json.dumps(response[0]['entities'])
