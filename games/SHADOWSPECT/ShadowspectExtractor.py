## import standard libraries
import logging
import traceback
from typing import Any, Dict, List, Union
## import local files
from games.SHADOWSPECT.extractors import *
import utils
from extractors.Extractor import Extractor
from extractors.Feature import Feature
from schemas.GameSchema import GameSchema

## @class ShadowspectExtractor
#  Extractor subclass for extracting features from Shadowspects game data.
class ShadowspectExtractor(Extractor):
    ## Constructor for the ShadowspectExtractor class.
    #  Sets a game schema.
    #
    #  @param session_id The id number for the session whose data is being processed
    #                    by this extractor instance.
    #  @param game_schema A dictionary that defines how the game data itself is
    #                     structured.
    def __init__(self, session_id: str, game_schema: GameSchema, feature_overrides:Union[List[str],None]=None):
        self._game_schema = game_schema
        super().__init__(session_id=session_id, game_schema=game_schema, feature_overrides=feature_overrides)

    def _loadFeature(self, feature_type:str, name:str, feature_args:Dict[str,Any], count_index:Union[int,None] = None) -> Feature:
        ret_val : Feature
        if feature_type == "MoveShapeCount":
            ret_val = MoveShapeCount.MoveShapeCount(name=name, description=feature_args["description"])
        elif feature_type == "SessionID":
            ret_val = SessionID.SessionID(name=name, description=feature_args["description"], session_id=self._session_id)
        elif feature_type == "FunnelByUser":
            ret_val = FunnelByUser.FunnelByUser(name=name, description=feature_args["description"])
        elif feature_type == "LevelsOfDifficulty":
            ret_val = LevelsOfDifficulty.LevelsOfDifficulty(name=name, description=feature_args["description"])
        elif feature_type == "SequenceBetweenPuzzles":
            ret_val = SequenceBetweenPuzzles.SequenceBetweenPuzzles(name=name, description=feature_args["description"])
        elif feature_type == "SequenceWithinPuzzles":
            ret_val = SequenceWithinPuzzles.SequenceWithinPuzzles(name=name, description=feature_args["description"])
        else:
            raise NotImplementedError(f"'{feature_type}' is not a valid feature for Shadowspect.")
        return ret_val
