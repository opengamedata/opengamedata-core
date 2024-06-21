# import libraries
import logging
from datetime import datetime, timedelta
from statistics import stdev
from typing import Any, List, Optional
from ogd.core.models.enums.ExtractionMode import ExtractionMode
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class JobsAttempted(Feature):

    def __init__(self, params:GeneratorParameters, job_map:dict, diff_map: dict):
        self._player_id = None

        self._job_map = job_map
        self._user_code = None
        self._session_id = None
        super().__init__(params=params)

        # Subfeatures
        if self.CountIndex is not None:
            self._job_id = self.CountIndex
            self._job_name = list(job_map.keys())[self.CountIndex]
            self._difficulties = diff_map[self.CountIndex]
        else:
            raise ValueError("JobsAttempted was not given a count index!")
        self._num_starts = 0
        self._num_completes = 0
        self._percent_complete = 0
        self._avg_time_complete = 0
        self._std_dev_complete = 0

        # Time
        self._times : List[int] = []
        # self._time = 0
        # self._job_start_time : Optional[datetime] = None
        # self._prev_timestamp : Optional[datetime] = None

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["accept_job", "complete_job"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["JobActiveTime"]

    def _updateFromEvent(self, event:Event) -> None:
        if event.UserID != self._player_id:
            self._player_id = event.UserID
        if event.SessionID != self._session_id:
            self._session_id = event.SessionID

            # if self._job_start_time is not None and self._prev_timestamp is not None:
                # self._time += (self._prev_timestamp - self._job_start_time).total_seconds()
                # self._job_start_time = event.Timestamp

        _current_job = event.GameState.get('job_name', event.EventData.get('job_name', None))['string_value']
        if _current_job is None:
            raise KeyError("Could not find key 'job_name' in GameState or EventData!")
        if self._validate_job(_current_job):
            user_code = event.UserID
            job_id = self._job_map[_current_job]

            if event.EventName == "accept_job" and job_id == self._job_id:
                self._num_starts += 1
                self._user_code = user_code
                # self._job_start_time = event.Timestamp

            elif event.EventName == "complete_job" and job_id == self._job_id and user_code == self._user_code:
                self._num_completes += 1

                # if self._job_start_time:
                    # self._time += (event.Timestamp - self._job_start_time).total_seconds()
                    # self._times.append(self._time)
                    # self._time = 0
                    # self._job_start_time = None

        # self._prev_timestamp = event.Timestamp

    def _updateFromFeatureData(self, feature:FeatureData):
        if feature.FeatureType == "JobActiveTime":
            if feature.CountIndex == self.CountIndex:
                _active_time = feature.FeatureValues[0]
                if self.ExtractionMode == ExtractionMode.SESSION \
                and feature.ExportMode == ExtractionMode.SESSION:
                    # session should only have one time, namely the time for the session.
                    self._times = [_active_time]
                    # print(f"JobsAttempted got session-session for player {self._player_id}")
                elif self.ExtractionMode == ExtractionMode.PLAYER \
                and feature.ExportMode   == ExtractionMode.PLAYER:
                    # player should only have one time, namely the time for the player.
                    self._times = [_active_time]
                    # print(f"JobsAttempted got player-player for player {self._player_id}")
                elif self.ExtractionMode == ExtractionMode.POPULATION \
                and feature.ExportMode   == ExtractionMode.PLAYER:
                    # population could have many times. Only add to list if they actually spent time there, though.
                    if _active_time > 0:
                        self._times.append(_active_time)
                    # print(f"JobsAttempted got population-player for player {self._player_id}")
                # else:
                    # print(f"JobsAttempted got a {self.ExtractionMode.name}-{feature.ExportMode.name} matching, not helpful.")
        else:
            print(f"JobsAttempted got a feature of wrong type: {feature.FeatureType}")

    def _getFeatureValues(self) -> List[Any]:
        if self._num_starts > 0:
            self._percent_complete = (self._num_completes / self._num_starts) * 100

        # if self._time != 0:
        #     self._times.append(self._time)
        
        if len(self._times) > 0:
            self._avg_time_complete = sum(self._times) / len(self._times)

        if len(self._times) > 1:
            self._std_dev_complete = stdev(self._times)

        return [self._job_id, self._job_name, self._num_starts, self._num_completes, self._percent_complete, self._avg_time_complete, self._std_dev_complete, self._difficulties]

    # *** Optionally override public functions. ***
    def Subfeatures(self) -> List[str]:
        return ["job-name", "num-starts", "num-completes", "percent-complete", "avg-time-per-attempt", "std-dev-per-attempt", "job-difficulties"]

    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"

    # *** Other local functions
    def _validate_job(self, job_data):
        ret_val : bool = False
        if job_data and job_data in self._job_map:
            ret_val = True
        else:
            self.WarningMessage(f"Got invalid job_name data in JobsAttempted")
        return ret_val
