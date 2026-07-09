# import libraries
from typing import Any, List, Optional

from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.common.models.Event import Event
from ogd.common.models.enums.ExtractionMode import ExtractionMode
from ogd.common.models.FeatureData import FeatureData
from ogd.common.utils.Logger import Logger
import logging

class PlayerLanguageSelected(Feature):
    def __init__(self, params: GeneratorParameters):
        super().__init__(params=params)
        self.player_id = None
        self.player_language = None
    
    @classmethod
    def _eventFilter(cls, mode: ExtractionMode) -> List[str]:
        return ["all_events"]

    @classmethod
    def _featureFilter(cls, mode: ExtractionMode) -> List[str]:
        return ["LanguageSelected"]

    def _updateFromEvent(self, event: Event) -> None:
        if self.player_id is None and event.UserID is not None:
            self.player_id = event.UserID
 
    def _updateFromFeatureData(self, feature: FeatureData):
        if feature.FeatureType == "LanguageSelected":
            player_languages = feature.FeatureValues[0]
            self.player_language = player_languages.get(self.player_id, None)

    def _getFeatureValues(self) -> List[Any]:
        return [self.player_language]

    def Subfeatures(self) -> List[str]:
        return []

    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
    
    @classmethod
    def AvailableModes(cls) -> List[ExtractionMode]:
        return [ExtractionMode.PLAYER]