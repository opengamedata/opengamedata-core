# import libraries
import logging
from datetime import timedelta
from typing import Any, List
# import locals
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.SessionFeature import SessionFeature
from ogd.core.schemas.Event import Event, EventSource
from ogd.core.schemas.ExtractionMode import ExtractionMode
from ogd.core.schemas.FeatureData import FeatureData
from ogd.core.utils.Logger import Logger
from ogd.games.AQUALAB.features.PerJobFeature import PerJobFeature


class SessionDuration(PerJobFeature):

    def __init__(self, params:GeneratorParameters, threshold:int):
        self.threshold = threshold
        super().__init__(params=params)
        self.max_idle = timedelta(0)
        self.previous_time = None
        self.idle_time = timedelta(0)
        self.total_session_time = timedelta(0)
        # self._session_duration = 0
    def Subfeatures(self) -> List[str]:
            return ["Total", "Seconds", "Active", "ActiveSeconds", "Idle" "IdleSeconds", "MaxIdle"]
    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["all_events"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event:Event) -> None:
        if event.EventSource == EventSource.GAME:
            if self.previous_time is not None:
                self.total_session_time += (event.Timestamp - self.previous_time)
                if (event.Timestamp - self.previous_time) > timedelta(minutes=1):
                    self.idle_time += (event.Timestamp - self.previous_time)
                    if self.max_idle < (event.Timestamp - self.previous_time):
                        self.max_idle = event.Timestamp - self.previous_time
            self.previous_time = event.Timestamp
     
        # # if this was earliest event, make it the start time.
        # if not self._client_start_time:
        #     self._client_start_time = event.Timestamp
        #     self._client_start_index = event.EventSequenceIndex
        # if self._client_start_time > event.Timestamp:
        #     Logger.Log(f"Got out-of-order events in SessionDuration for session {self._session_id};\nevent {event.EventName}:{event.EventSequenceIndex} for player {event.UserID}:{event.SessionID} had timestamp {event.Timestamp} earlier than start event, with time {self._client_start_time}, index {self._client_start_index}!", logging.WARN)
        #     self._client_start_time = event.Timestamp
        #     self._client_start_index = event.EventSequenceIndex
        # # if this was the latest event, make it the end time, otherwise output error.
        # if self._client_end_time is not None and self._client_end_time > event.Timestamp:
        #     Logger.Log(f"Got out-of-order events in SessionDuration for session {self._session_id};\nevent {event.EventName}:{event.EventSequenceIndex} for player {event.UserID}:{event.SessionID} had timestamp {event.Timestamp} earlier than end event, with time {self._client_end_time}, index {self._client_end_index}!", logging.WARN)
        # else:
        #     self._client_end_time = event.Timestamp
        #     self._client_end_index = event.EventSequenceIndex
        # # self._session_duration = (event.Timestamp - self._client_start_time).total_seconds()

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        if self.total_session_time is not None:
            return [self.total_session_time, self.total_session_time.total_seconds(), (self.total_session_time - self.idle_time), (self.total_session_time - self.idle_time).total_seconds(), self.idle_time, self.idle_time.total_seconds(), self.max_idle]
        else:
            return ["No events"]

    # *** Optionally override public functions. ***

    @staticmethod
    def AvailableModes() -> List[ExtractionMode]:
        return [ExtractionMode.SESSION]
