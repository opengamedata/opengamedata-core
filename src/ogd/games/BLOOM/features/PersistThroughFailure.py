from typing import Any, Dict, List, Optional
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class PersistThroughFailure(Feature):
    def __init__(self, params: GeneratorParameters):
        super().__init__(params=params)
        self.failed: bool = False
        self.persisted: int = 0

    # Implement abstract functions
    @classmethod
    def _eventFilter(cls, mode: ExtractionMode) -> List[str]:
        # List of player action events + lose_game for failure tracking
        return [
            "game_start", "select_policy_card", "click_build", 
            "click_destroy", "click_undo", "click_execute_build", 
            "click_confirm_destroy", "lose_game"
        ]

    @classmethod
    def _featureFilter(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event: Event) -> None:
        event_type = event.EventName
        if event_type == "lose_game":
            self.failed = True
        elif self.failed and event_type in [
            "game_start", "select_policy_card", "click_build", 
            "click_destroy", "click_undo", "click_execute_build", 
            "click_confirm_destroy"
        ]:
            self.persisted += 1
            self.failed = False

    def _updateFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self.persisted > 0]

    # Subfeature "count"
    def _getSubfeatureValues(self) -> Dict[str, Any]:
        return {"count": self.persisted}

    # Optionally override public functions
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
