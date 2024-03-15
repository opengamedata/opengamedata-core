## import standard libraries
from typing import Any, Callable, Dict, List, Optional
## import local files
from . import features
from ogd.core.extractors.detectors.Detector import Detector
from ogd.core.extractors.Extractor import ExtractorParameters
from ogd.core.extractors.legacy.LegacyLoader import LegacyLoader
from ogd.core.extractors.features.Feature import Feature
from ogd.games.LAKELAND.features.LakelandExtractor import LakelandExtractor
from ogd.core.schemas.Event import Event
from ogd.core.schemas.ExtractionMode import ExtractionMode
from ogd.core.schemas.games.GameSchema import GameSchema

class LakelandLoader(LegacyLoader):

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _loadFeature(self, feature_type:str, extractor_params:ExtractorParameters, schema_args:Dict[str,Any]) -> Feature:
        return LakelandExtractor(params=extractor_params, game_schema=self._game_schema, session_id=self._session_id)

    def _loadDetector(self, detector_type:str, extractor_params:ExtractorParameters, schema_args:Dict[str,Any], trigger_callback:Callable[[Event], None]) -> Detector:
        raise NotImplementedError(f"'{detector_type}' is not a valid feature for Lakeland.")

    @staticmethod
    def _getFeaturesModule():
        return features

    # *** BUILT-INS & PROPERTIES ***

    ## Constructor for the WaveExtractor class.
    def __init__(self, player_id:str, session_id:str, game_schema: GameSchema, mode:ExtractionMode, feature_overrides:Optional[List[str]]):
        """Constructor for the CrystalLoader class.

        :param player_id: _description_
        :type player_id: str
        :param session_id: The id number for the session whose data is being processed by this instance
        :type session_id: str
        :param game_schema: A data structure containing information on how the game events and other data are structured
        :type game_schema: GameSchema
        :param feature_overrides: A list of features to export, overriding the default of exporting all enabled features.
        :type feature_overrides: Optional[List[str]]
        """
        super().__init__(player_id=player_id, session_id=session_id, game_schema=game_schema, mode=mode, feature_overrides=feature_overrides)

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***