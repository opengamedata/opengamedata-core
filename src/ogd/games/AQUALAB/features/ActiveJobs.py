# import libraries
import json
import logging
from collections import defaultdict
from typing import Any, List, Optional
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class ActiveJobs(Feature):

    def __init__(self, params:GeneratorParameters, job_map:dict):
        self._job_map = job_map
        super().__init__(params=params)
        self._current_user_code = None
        self._last_started_id = None
        self._active_jobs = defaultdict(list)

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["accept_job", "switch_job"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event:Event) -> None:
        _current_job = event.GameState.get('job_name', event.EventData.get('job_name', None))['string_value']
        if self._validate_job(_current_job):
            user_code = event.UserID

            if (self._current_user_code is not None) and (self._current_user_code != user_code) and (self._current_user_code not in self._active_jobs[self._last_started_id]):
                # if we found a new user, then previous user must have left off on whatever their active job was.
                # so, add the user to the list for that job
                self._active_jobs[self._last_started_id].append(self._current_user_code)
            self._current_user_code = user_code # in either case, set latest user as "current"
            self._last_started_id = _current_job # In either case, set latest job name as "current".

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        ret_val = self._active_jobs

        if (self._last_started_id is not None) and (self._current_user_code not in self._active_jobs[self._last_started_id]):
            ret_val[self._last_started_id].append(self._current_user_code) # whatever last event was, assume player left off there.

        return [json.dumps(ret_val)]

    # *** Optionally override public functions. ***
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
