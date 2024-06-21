# import libraries
import logging
from typing import Optional
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.PerCountFeature import PerCountFeature
from ogd.core.models.Event import Event

class PerJobFeature(PerCountFeature):
    def __init__(self, params:GeneratorParameters, job_map:dict):
        super().__init__(params=params,)
        self._job_map = job_map


    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _validateEventCountIndex(self, event:Event):
        ret_val : bool = False


        if event.AppVersion == 'Aqualab' or event.AppVersion == 'None':
            job_name = event.GameState.get('job_name', event.EventData.get('job_name', "JOB NAME NOT FOUND"))
        else:
            job_name = job_name

        if type(job_name) is dict:
            job_name = job_name['string_value']
        
        
        if job_name is not None:
            if job_name in self._job_map and self._job_map[job_name] == self.CountIndex:
                ret_val = True
        else:
            self.WarningMessage(f"Got invalid job_name data in {type(self).__name__}")

        return ret_val

    # *** Optionally override public functions. ***

    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
