from typing import Any, List
from ogd.core.extractors.Extractor import ExtractorParameters
from ogd.core.extractors.features.SessionFeature import SessionFeature
from ogd.core.schemas.Event import Event
from ogd.core.schemas.ExtractionMode import ExtractionMode
from ogd.core.schemas.FeatureData import FeatureData

class PhasesReached(SessionFeature):

    def __init__(self, params: ExtractorParameters):
        self.phases_reached = set()
        super().__init__(params=params)

    @classmethod
    def _getEventDependencies(cls, mode: ExtractionMode) -> List[str]:
        return ["all_events"]

    @classmethod
    def _getFeatureDependencies(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _extractFromEvent(self, event: Event) -> None:
        game_state = event.EventData.get("all_events")
        if game_state:
            region = event.GameState.get("region")
            if region:
                self.phases_reached.add(region)

    def _extractFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [list(self.phases_reached)]
