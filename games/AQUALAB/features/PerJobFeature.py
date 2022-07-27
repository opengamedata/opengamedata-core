# import libraries
import logging
from typing import Optional
# import locals
from utils import Logger
from extractors.Extractor import ExtractorParameters
from extractors.features.PerCountFeature import PerCountFeature
from schemas.Event import Event

class PerJobFeature(PerCountFeature):
    def __init__(self, params:ExtractorParameters, job_map:dict):
        super().__init__(params=params,)
        self._job_map = job_map

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _validateEventCountIndex(self, event:Event):
        ret_val : bool = False

        job_data = event.EventData["job_name"]['string_value']
        if job_data is not None:
            if job_data in self._job_map and self._job_map[job_data] == self.CountIndex:
                ret_val = True
        else:
            Logger.Log(f"Got invalid job_name data in {type(self).__name__}", logging.WARNING)

        return ret_val

    # *** Optionally override public functions. ***

    @staticmethod
    def MinVersion(self) -> Optional[str]:
        return "1"
