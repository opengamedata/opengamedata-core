# import libraries
from typing import Any, Dict, List, Type
# import locals
from detectors.DetectorRegistry import DetectorRegistry
from extractors.ExtractorRegistry import ExtractorRegistry
from features.FeatureData import FeatureData
from extractors.ExtractorLoader import ExtractorLoader
from games.LAKELAND.LakelandLoader import LakelandLoader
from processors.Processor import Processor
from schemas.Event import Event
from schemas.GameSchema import GameSchema
from schemas.Request import ExporterTypes

class EventProcessor(Processor):
    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _prepareRegistry(self) -> ExtractorRegistry:
        return DetectorRegistry()

    def _getExtractorNames(self) -> List[str]:
        return self._registry.GetExtractorNames()

    ## Abstract declaration of a function to get the calculated value of the feature, given data seen so far.
    def _getFeatureValues(self, export_types:ExporterTypes) -> Dict[str,List[Any]]:
        return {}

    def _getFeatureData(self, order:int) -> Dict[str,List[FeatureData]]:
        return {}

    ## Abstract declaration of a function to get the calculated value of the feature, given data seen so far.
    def _processEvent(self, event:Event):
        pass

    def _processFeatureData(self, feature:FeatureData):
        pass

    def _prepareLoader(self) -> ExtractorLoader:
        ret_val : ExtractorLoader
        if self._LoaderClass is LakelandLoader:
            ret_val = LakelandLoader(player_id="events", session_id="events", game_schema=self._game_schema, feature_overrides=self._overrides, output_file=None)
        else:
            ret_val = self._LoaderClass(player_id="events", session_id="events", game_schema=self._game_schema, feature_overrides=self._overrides)
        return ret_val

    # *** PUBLIC BUILT-INS ***

    def __init__(self, LoaderClass: Type[ExtractorLoader], game_schema: GameSchema):
        super().__init__(LoaderClass=LoaderClass, game_schema=game_schema, feature_overrides=None)
        self._registry = DetectorRegistry()

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***