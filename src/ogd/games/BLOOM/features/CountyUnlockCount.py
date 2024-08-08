# import libraries
from typing import Any, Dict, List, Optional, Set
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class CountyUnlockCount(Feature):
    def __init__(self, params: GeneratorParameters):
        super().__init__(params=params)
        self.county_unlocks: Dict[str, int] = {} 
        self.county_set: Set[str] = set()


    @classmethod
    def _eventFilter(cls, mode: ExtractionMode) -> List[str]:
        return ["county_unlocked"]

    @classmethod
    def _featureFilter(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event: Event) -> None:
        county_name = event.EventData.get("county_name", None)
        if county_name:
            if county_name not in self.county_unlocks:
                self.county_unlocks[county_name] = 1
            else:
                self.county_unlocks[county_name] += 1
            
           
            self.county_set.add(county_name)

    def _updateFromFeatureData(self, feature: FeatureData):
        pass

    def _getFeatureValues(self) -> List[Any]:
        total_county_unlocks = sum(self.county_unlocks.values()) 
        unique_county_count = len(self.county_set) 
        
        return [unique_county_count, total_county_unlocks, self.county_unlocks]

    def Subfeatures(self) -> List[str]:
        return ["RawTotal", "Breakdown"]

    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
