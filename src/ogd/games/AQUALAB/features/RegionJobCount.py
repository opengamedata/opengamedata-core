# import libraries
import inspect
import logging
from datetime import timedelta
from typing import Any, List, Optional
# import locals
from ogd.common.utils.Logger import Logger
from ogd.core.generators.extractors.Extractor import GeneratorParameters
from ogd.games.AQUALAB.features.PerJobFeature import PerJobFeature
from ogd.common.models.Event import Event
from ogd.common.models.enums.ExtractionMode import ExtractionMode
from ogd.common.models.FeatureData import FeatureData
from ogd.core.generators.extractors.PerCountFeature import PerCountFeature

class RegionJobCount(PerCountFeature):
    def __init__(self, params:GeneratorParameters):
        super().__init__(params=params)
        regions = ['arctic', 'coral', 'bayou', 'kelp', 'other']
        self.attemptedCount = 0
        self.completeCount = 0
        self.region = regions[self.CountIndex]
    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["complete_job", "switch_job"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _validateEventCountIndex(self, event:Event) -> bool:
        job_name = event.GameState.get('job_name')
        return isinstance(job_name, str) and job_name.startswith(self.region)

# 'aqualab' and 'GameState"
    def _updateFromEvent(self, event:Event) -> None:
        if event.EventName == "switch_job":
            self.attemptedCount += 1

        if event.EventName == "complete_job":
            self.completeCount += 1

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self.attemptedCount, self.completeCount]

    def Subfeatures(self) -> List[str]:
        return ["Complete"]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
