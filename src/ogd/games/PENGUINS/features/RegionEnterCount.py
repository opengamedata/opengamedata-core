# import libraries
import logging
from typing import Any, Dict, List, Optional
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.games.PENGUINS.features.PerRegionFeature import PerRegionFeature
from ogd.core.schemas.Event import Event
from ogd.core.schemas.ExtractionMode import ExtractionMode
from ogd.core.schemas.FeatureData import FeatureData
from ogd.core.generators.extractors.PerCountFeature import PerCountFeature


class RegionEnterCount(PerCountFeature):

    def __init__(self, params:GeneratorParameters, region_map:List[Dict[str, Any]]):
        super().__init__(params=params)
        self._region_map = region_map
        self._current_count : int = 0

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["enter_region"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event:Event) -> None:
        self._current_count += 1

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self._current_count]

    # *** Optionally override public functions. ***
    def _validateEventCountIndex(self, event: Event):
        ret_val : bool = False
        region_data = event.EventData.get("region_name")
        if region_data is not None:
            if region_data in region_map and region_map[region_data] == self.CountIndex:
                ret_val = True
        else:
            Logger.Log(f"Got invalid region data in {type(self).__name__}", logging.WARNING)

        return ret_val