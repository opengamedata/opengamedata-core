# import libraries
from typing import Any, List, Optional
from extractors.Extractor import ExtractorParameters
# import local files
from extractors.features.SessionFeature import SessionFeature
from schemas.FeatureData import FeatureData
from schemas.Event import Event

class UserEnabled(SessionFeature):
    """Template file to serve as a guide for creating custom Feature subclasses for games.

    :param Feature: Base class for a Custom Feature class.
    :type Feature: _type_
    """
    def __init__(self, params:ExtractorParameters):
        super().__init__(params=params)
        self._full_screen : Optional[int] = None
        self._music : Optional[int] = None
        self._hq : Optional[int] = None

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _getEventDependencies(self) -> List[str]:
        return ["CUSTOM.1"]

    def _getFeatureDependencies(self) -> List[str]:
        return [] 

    def _extractFromEvent(self, event:Event) -> None:
        _data = event.EventData
        true_values = [1, "1", "true", True]
        for item in ["fullscreen", "music", "hq"]:
            if _data.get(item) is None:
                raise(ValueError(f"Can't find {item} item in the event data!"))
        if _data.get("fullscreen") in true_values:
            self._full_screen = 1
        else:
            self._full_screen = 0

        if _data.get("music") in true_values:
            self._music = 1
        else:
            self._music = 0

        if _data.get("hq") in true_values:
            self._hq = 1
        else:
            self._hq = 0

        return

    def _extractFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self._full_screen, self._music, self._hq]

    # *** Optionally override public functions. ***
    def Subfeatures(self) -> List[str]:
        return ["Music", "HQGraphics"] 

    def BaseFeatureSuffix(self) -> str:
        return "FullScreen"