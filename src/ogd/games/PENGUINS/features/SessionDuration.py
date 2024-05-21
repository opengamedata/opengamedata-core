# import libraries
import logging
from typing import Any, List
# import locals
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.SessionFeature import SessionFeature
from ogd.core.schemas.Event import Event
from ogd.core.schemas.ExtractionMode import ExtractionMode
from ogd.core.schemas.FeatureData import FeatureData
from ogd.core.utils.Logger import Logger

# import libraries
import logging
from typing import Any, List, Optional
from datetime import datetime, timedelta
# import locals
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.SessionFeature import SessionFeature
from ogd.core.schemas.Event import Event
from ogd.core.schemas.ExtractionMode import ExtractionMode
from ogd.core.schemas.FeatureData import FeatureData
from ogd.core.utils.Logger import Logger

class SessionDuration(SessionFeature):
    """Template file to serve as a guide for creating custom Feature subclasses for games.

    :param Feature: Base class for a Custom Feature class.
    :type Feature: _type_
    """
    def __init__(self, params:GeneratorParameters, session_id:str):
        self._session_id = session_id
        super().__init__(params=params)
        self._start_time = None
        self._start_index = None
        self._end_time = None
        self._end_index = None
        # self._session_duration = 0

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["all_events"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event:Event) -> None:
        # if this was earliest event, make it the start time.
        if not self._start_time:
            self._start_time = event.Timestamp
            self._start_index = event.EventSequenceIndex
        if self._start_time > event.Timestamp:
            Logger.Log(f"Got out-of-order events in SessionDuration; event {event.EventName}:{event.EventSequenceIndex} for player {event.UserID}:{event.SessionID} had timestamp {event.Timestamp} earlier than start event, with time {self._start_time}, index {self._start_index}!", logging.WARN)
            self._start_time = event.Timestamp
            self._start_index = event.EventSequenceIndex
        # if this was the latest event, make it the end time, otherwise output error.
        if self._end_time is not None and self._end_time > event.Timestamp:
            Logger.Log(f"Got out-of-order events in SessionDuration; event {event.EventName}:{event.EventSequenceIndex} for player {event.UserID}:{event.SessionID} had timestamp {event.Timestamp} earlier than end event, with time {self._end_time}, index {self._end_index}!", logging.WARN)
        else:
            self._end_time = event.Timestamp
            self._end_index = event.EventSequenceIndex
        # self._session_duration = (event.Timestamp - self._client_start_time).total_seconds()

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        if self._start_time and self._end_time:
            return [self._end_time - self._start_time]
        else:
            return ["No events"]

    # *** Optionally override public functions. ***

    @staticmethod
    def AvailableModes() -> List[ExtractionMode]:
        return [ExtractionMode.SESSION]