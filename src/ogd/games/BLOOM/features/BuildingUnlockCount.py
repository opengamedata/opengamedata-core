from typing import Any, Dict, List, Optional
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class BuildingUnlockCount(Feature):
    def __init__(self, params: GeneratorParameters):
        super().__init__(params=params)
        self.building_unlocks: Dict[str, int] = {}

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode: ExtractionMode) -> List[str]:
        return ["building_type_unlocked"]

    @classmethod
    def _featureFilter(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event: Event) -> None:
        building_type = event.EventData.get("building_type", None)
        if building_type:
            if building_type not in self.building_unlocks:
                self.building_unlocks[building_type] = 1
            else:
                self.building_unlocks[building_type] += 1

    def _updateFromFeatureData(self, feature: FeatureData):
        pass

    def _getFeatureValues(self) -> List[Any]:
        total_building_unlocks = sum(self.building_unlocks.values())
        return [total_building_unlocks, self.building_unlocks]

    def Subfeatures(self) -> List[str]:
        return ["Breakdown"]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
