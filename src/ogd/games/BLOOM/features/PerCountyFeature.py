# import libraries
import logging
from typing import Optional
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.PerCountFeature import PerCountFeature
from ogd.core.models.Event import Event

class PerCountyFeature(PerCountFeature):
    def __init__(self, params: GeneratorParameters, county_map: dict):
        super().__init__(params=params)
        self._county_map = county_map

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _validateEventCountIndex(self, event: Event):
        ret_val: bool = False

        county_name = event.GameState.get('county_name', event.EventData.get('county_name', "COUNTY NAME NOT FOUND"))
        if county_name is not None:
            if county_name in self._county_map and self._county_map[county_name] == self.CountIndex:
                ret_val = True
        else:
            self.WarningMessage(f"Got invalid county_name data in {type(self).__name__}")

        return ret_val

    # *** Optionally override public functions. ***

    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
