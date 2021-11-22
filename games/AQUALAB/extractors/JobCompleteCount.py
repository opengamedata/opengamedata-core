from datetime import timedelta
from typing import Any, List

from extractors.Feature import Feature
from schemas.Event import Event

class JobCompleteCount(Feature):

    def __init__(self, name:str, description:str, job_num:int, job_map:dict):
        self._job_map = job_map
        super().__init__(name=name, description=description, count_index=job_num)
        self._completed = 0

    def GetEventTypes(self) -> List[str]:
        return ["complete_job"]

    def GetFeatureValues(self) -> List[Any]:
        return self._completed

    def _extractFromEvent(self, event:Event) -> None:
        if "job_id" in event.event_data.keys():
            if self._validate_job(event.event_data['job_id']):
                self._completed += 1
        else:
            raise ValueError(f"job_id not found in keys of event type {event.event_name}, the keys were:\n{event.event_data.keys()}")

    def _validate_job(self, job_data):
        ret_val : bool = False
        if job_data['int_value'] is not None:
            if job_data['int_value'] == self._count_index:
                ret_val = True
        elif job_data['string_value'] is not None:
            if self._job_map[job_data['string_value']] == self._count_index:
                ret_val = True
        else:
            print(f"Got invalid job_id data in JobStartCount")
        return ret_val
