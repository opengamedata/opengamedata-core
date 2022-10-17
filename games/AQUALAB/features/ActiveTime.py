# import libraries
from datetime import datetime, timedelta
import logging, warnings
from typing import Any, List, Optional
# import locals
from utils import Logger
from extractors.Extractor import ExtractorParameters
from extractors.features.Feature import Feature
from schemas.Event import Event
from schemas.ExtractionMode import ExtractionMode
from schemas.FeatureData import FeatureData

class ActiveTime(Feature):
    IDLE_LEVEL = 30

    def __init__(self, params:ExtractorParameters, job_map:dict, active_threads:float = None):
        self._job_map = job_map
        super().__init__(params=params)
        self._Idle_time: float = 0
        self.active_level:float = active_threads if active_threads else ActiveTime.IDLE_LEVEL
        self._sess_duration: Optional[timedelta] = None
        self._client_start_time: Optional[datetime] = None
        self._client_end_time: Optional[datetime] = None
        

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _getEventDependencies(cls, mode:ExtractionMode) -> List[str]:
        return ["all_events"]

    @classmethod
    def _getFeatureDependencies(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _extractFromEvent(self, event:Event) -> None:
        if not self._client_start_time:
            self._client_start_time = event.Timestamp
        self._client_end_time = event.Timestamp
        
        if event.EventName != "Idle":
            return

        if not self.active_level:
            self.active_level = event.EventData.get("level")
        else:
            if self.active_level != event.EventData.get("level"):
                warnings.warn("The idle event has a different threshold!")
                return
        self._Idle_time += event.EventData.get("time")
        

    def _extractFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        if self._client_start_time and self._client_end_time:
            return [self._client_end_time - self._client_start_time - timedelta(seconds=self._Idle_time)]
        else:
            return ["No events"]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"