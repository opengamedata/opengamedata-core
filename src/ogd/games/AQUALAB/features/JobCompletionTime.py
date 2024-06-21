# import libraries
import inspect
import logging
from datetime import timedelta
from typing import Any, List, Optional
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.Generator import GeneratorParameters
from ogd.games.AQUALAB.features.PerJobFeature import PerJobFeature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class JobCompletionTime(PerJobFeature):

    def __init__(self, params:GeneratorParameters, job_map:dict):
        super().__init__(params=params, job_map=job_map)
        self._session_id = None
        self._job_start_time = None
        self._prev_timestamp = None
        self._time = 0

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["accept_job", "complete_job"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event:Event) -> None:
        if event.SessionID != self._session_id:
            self._session_id = event.SessionID
            # if we jumped to a new session, we only want to count time up to last event, not the time between sessions.
            if self._job_start_time and self._prev_timestamp:
                self._time += (self._prev_timestamp - self._job_start_time).total_seconds()
                self._job_start_time = event.timestamp

        def _getFilename(full_path:str):
            return full_path.split('\\')[-1].split('.')[0]

        if event.event_name == "accept_job":
            self._job_start_time = event.timestamp
        elif event.event_name == "complete_job":
            if self._job_start_time:
                self._time += (event.timestamp - self._job_start_time).total_seconds()
                self._job_start_time = None
            else:
                _completed_job = event.GameState.get('job_name', event.EventData.get('job_name', "JOB NAME NOT FOUND"))['string_value']
                callstack = [f"{_getFilename(inspect.stack()[i].filename)}.{inspect.stack()[i].function}" for i in range(min(11, len(inspect.stack())))]
                Logger.Log(f"In {callstack}:\n  {event.user_id} ({event.session_id}) completed job {_completed_job} with no active start time!", logging.DEBUG)

        self._prev_timestamp = event.timestamp

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [timedelta(seconds=self._time)]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
