# import libraries
import logging
from typing import Any, Dict, List, Optional
# import locals
from utils.Logger import Logger
from extractors.Extractor import ExtractorParameters
from extractors.features.Feature import Feature
from games.PENGUINS.features.PerRegionFeature import PerRegionFeature
from schemas.Event import Event
from schemas.ExtractionMode import ExtractionMode
from schemas.FeatureData import FeatureData
from extractors.features.SessionFeature import SessionFeature


class ActivityCount(SessionFeature):
    """Template file to serve as a guide for creating custom Feature subclasses for games.

    :param Feature: Base class for a Custom Feature class.
    :type Feature: _type_
    """
    def __init__(self, params:ExtractorParameters):
        super().__init__(params=params)
        self._session_id = None
        self._activity_start_time = None
        self._prev_timestamp = None
        self._time = 0
        self._object_name = None
        self._activ_dict = dict()

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    @classmethod
    def _getEventDependencies(cls, mode:ExtractionMode) -> List[str]:
        return ["activity_begin", "activity_end"]

    @classmethod
    def _getFeatureDependencies(cls, mode:ExtractionMode) -> List[str]:
        return [] 

    def _extractFromEvent(self, event:Event) -> None:
        if event.SessionID != self._session_id:
            self._session_id = event.SessionID
            # if we jumped to a new session, we only want to count time up to last event, not the time between sessions.
            if self._activity_start_time and self._prev_timestamp:
                self._time += (self._prev_timestamp - self._activity_start_time).total_seconds()
                self._activity_start_time = event.Timestamp

        if event.EventName == "activity_begin":
            self._activity_start_time = event.Timestamp
            self._object_name = event.event_data.get("object_id")
            if not self._object_name in self._activ_dict.keys():
                self._activ_dict[self._object_name] = timedelta(0)
        elif event.EventName == "activity_end":
            if self._activity_start_time is not None:
                self._time += (event.Timestamp - self._activity_start_time).total_seconds()
                self._activ_dict[self._object_name]+=timedelta(seconds=self._time)
                self._activity_start_time = None

        self._prev_timestamp = event.Timestamp



    def _extractFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self._activ_dict.keys()]


    # *** Optionally override public functions. ***
    def Subfeatures(self) -> List[str]:
        return [] 
