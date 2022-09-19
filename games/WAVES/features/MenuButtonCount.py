# import libraries
from schemas import Event
from typing import Any, List, Optional
# import locals
from schemas.FeatureData import FeatureData
from extractors.features.PerLevelFeature import PerLevelFeature
from extractors.Extractor import ExtractorParameters
from schemas.Event import Event

class MenuButtonCount(PerLevelFeature):
    def __init__(self, params:ExtractorParameters):
        PerLevelFeature.__init__(self, params=params)
        self._menu_btn_count = 0

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
def _getEventDependencies(cls, mode:ExtractionMode) -> List[str]:
        return ["CUSTOM.5"]
        # "events": ["MENU_BUTTON"],

    @classmethod
def _getEventDependencies(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _extractFromEvent(self, event:Event) -> None:
        self._menu_btn_count += 1

    def _extractFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self._menu_btn_count]

    # *** Optionally override public functions. ***
