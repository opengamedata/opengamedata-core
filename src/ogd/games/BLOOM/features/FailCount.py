# import necessary libraries
from typing import Any, Dict, List, Optional
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class FailCount(Feature):
    def __init__(self, params: GeneratorParameters):
        super().__init__(params=params)
        self.fail_type_counts: Dict[str, int] = {
            "CityFailed": 0,
            "TooManyBlooms": 0,
            "OutOfMoney": 0
        }

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode: ExtractionMode) -> List[str]:
        return ["lose_game"]

    @classmethod
    def _featureFilter(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event: Event) -> None:
        fail_type = event.EventData.get("lose_condition", "")
        if fail_type in self.fail_type_counts:
            self.fail_type_counts[fail_type] += 1

    def _updateFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [
            sum(self.fail_type_counts.values()),
            self.fail_type_counts['CityFailed'],
            self.fail_type_counts['TooManyBlooms'],
            self.fail_type_counts['OutOfMoney']
        ]

    def Subfeatures(self) -> List[str]:
        return ["CityFailed", "TooManyBlooms", "OutOfMoney"]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
