# global imports
import logging
from statistics import stdev
from typing import Any, List, Union
# local imports
import utils
from features.Feature import Feature
from features.FeatureData import FeatureData
from schemas.Event import Event

class JobsAttempted(Feature):

    def __init__(self, name:str, description:str, job_num:int, job_map:dict):
        self._job_map = job_map
        super().__init__(name=name, description=description, count_index=job_num)
        self._user_code = None

        # Subfeatures
        self._job_id = job_num
        self._job_name = list(job_map.keys())[job_num]
        self._num_starts = 0
        self._num_completes = 0
        self._percent_complete = 0
        self._avg_time_complete = 0
        self._std_dev_complete = 0

        # Time
        self._times = []
        self._job_start_time = None

    # *** Implement abstract functions ***
    def _getEventDependencies(self) -> List[str]:
        return ["accept_job", "complete_job"]

    def _getFeatureDependencies(self) -> List[str]:
        return []

    def _extractFromEvent(self, event:Event) -> None:
        user_code = event.user_id
        job_name = event.event_data["job_name"]["string_value"]
        job_id = self._job_map[job_name]

        if event.event_name == "accept_job" and job_id == self._job_id:
            self._num_starts += 1
            self._user_code = user_code
            self._job_start_time = event.timestamp

        elif event.event_name == "complete_job" and job_id == self._job_id and user_code == self._user_code:
            self._num_completes += 1

            if self._job_start_time:
                self._times.append((event.timestamp - self._job_start_time).total_seconds())
                self._job_start_time = None

    def _extractFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        if self._num_starts > 0:
            self._percent_complete = (self._num_completes / self._num_starts) * 100
        
        if len(self._times) > 0:
            self._avg_time_complete = sum(self._times) / len(self._times)

        if len(self._times) > 1:
            self._std_dev_complete = stdev(self._times)

        return [self._job_id, self._job_name, self._num_starts, self._num_completes, self._percent_complete, self._avg_time_complete, self._std_dev_complete]

    # *** Optionally override public functions. ***
    def Subfeatures(self) -> List[str]:
        return ["job-name", "num-starts", "num-completes", "percent-complete", "avg-time-complete", "std-dev-complete"]

    def MinVersion(self) -> Union[str,None]:
        return "1"

    # *** Other local functions
    def _validate_job(self, job_data):
        ret_val : bool = False
        if job_data['string_value'] is not None:
            if self._job_map[job_data['string_value']] == self._count_index:
                ret_val = True
        else:
            utils.Logger.Log(f"Got invalid job_name data in JobsAttempted", logging.WARNING)
        return ret_val
