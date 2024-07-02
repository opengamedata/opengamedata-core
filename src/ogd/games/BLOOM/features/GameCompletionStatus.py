# import libraries
from typing import Any, List, Optional
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class GameCompletionStatus(Feature):
    def __init__(self, params: GeneratorParameters):
        super().__init__(params=params)
        self.status: Optional[str] = "IN_PROGRESS"

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode: ExtractionMode) -> List[str]:
        return ["win_game", "lose_game"]

    @classmethod
    def _featureFilter(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event: Event) -> None:
        if event.EventName == "win_game":
            self.status = "WIN"
        elif event.EventName == "lose_game":
            if self.status != "WIN":
                self.status = "LOSS"

    def _updateFromFeatureData(self, feature: FeatureData):
        pass

    def _getFeatureValues(self) -> List[Any]:
        return [self.status]