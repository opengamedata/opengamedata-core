# global imports
from typing import Any, List
# local imports
from features.SessionFeature import SessionFeature
from features.FeatureData import FeatureData
from schemas.Event import Event

class UserAvgSessionDuration(SessionFeature):

    def __init__(self, name:str, description:str, player_id:str):
        self._player_id = player_id
        super().__init__(name=name, description=description)
        self._times = []

    # *** Implement abstract functions ***
    def _getEventDependencies(self) -> List[str]:
        return []

    def _getFeatureDependencies(self) -> List[str]:
        return ["SessionDuration"]

    def _extractFromEvent(self, event:Event) -> None:
        return

    def _extractFromFeatureData(self, feature: FeatureData):
        if feature.PlayerID() == self._player_id:
            self._times.append(feature.FeatureValues()[0])

    def _getFeatureValues(self) -> List[Any]:
        return [sum(self._times) / len(self._times)]

    # *** Optionally override public functions. ***