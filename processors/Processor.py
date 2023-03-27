## import standard libraries
import abc
import logging
from typing import Any, Dict, List, Type, Optional
# import locals
from extractors.registries.ExtractorRegistry import ExtractorRegistry
from extractors.ExtractorLoader import ExtractorLoader
from schemas.ExtractionMode import ExtractionMode
from schemas.FeatureData import FeatureData
from schemas.GameSchema import GameSchema
from schemas.Event import Event
from utils import Logger

## @class Processor
class Processor(abc.ABC):

    # *** ABSTRACTS ***

    @property
    @abc.abstractmethod
    def _mode(self) -> ExtractionMode:
        pass

    @property
    @abc.abstractmethod
    def _playerID(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def _sessionID(self) -> str:
        pass

    ## Abstract declaration of a function to get the names of all features.
    @abc.abstractmethod
    def _getExtractorNames(self) -> List[str]:
        pass

    ## Abstract declaration of a function to get the calculated value of the feature, given data seen so far.
    @abc.abstractmethod
    def _processEvent(self, event:Event) -> None:
        pass

    # *** BUILT-INS ***

    def __init__(self, game_schema: GameSchema, feature_overrides:Optional[List[str]]=None):
        self._game_schema : GameSchema            = game_schema
        self._overrides   : Optional[List[str]]   = feature_overrides
        self._registry    : Optional[ExtractorRegistry] = None

    def __str__(self):
        return f""

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def GetExtractorNames(self) -> List[str]:
        # TODO: add error handling code, if applicable.
        return self._getExtractorNames()

    def ProcessEvent(self, event:Event) -> None:
        # TODO: add error handling code, if applicable.
        self._processEvent(event=event)

    def ProcessFeatureData(self, feature_list:List[FeatureData]) -> None:
        if self._registry is not None:
            for feature in feature_list:
                self._registry.ExtractFromFeatureData(feature=feature)
        else:
            Logger.Log(f"Processor has no registry, skipping FeatureData.", logging.WARN)

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
