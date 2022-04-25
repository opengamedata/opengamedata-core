from typing import Any, Dict, List, Union

from games.SHIPWRECKS.features import *
from extractors.ExtractorLoader import ExtractorLoader
from features.Feature import Feature
from schemas.GameSchema import GameSchema

## @class ShipwrecksLoader
#  Extractor subclass for extracting features from Shipwrecks game data.
class ShipwrecksLoader(ExtractorLoader):
    ## Constructor for the ShipwrecksLoader class.
    #  Initializes some custom private data (not present in base class) for use
    #  when calculating some features.
    #  Sets the sessionID feature.
    #  Further, initializes all Q&A features to -1, representing unanswered questions.
    #
    #  @param session_id The id number for the session whose data is being processed
    #                    by this extractor instance.
    #  @param game_table A data structure containing information on how the db
    #                    table assiciated with this game is structured. 
    #  @param game_schema A dictionary that defines how the game data itself is
    #                     structured.
    def __init__(self, player_id:str, session_id:str, game_schema: GameSchema, feature_overrides:Union[List[str],None]):
        super().__init__(player_id=player_id, session_id=session_id, game_schema=game_schema, feature_overrides=feature_overrides)

    def LoadFeature(self, feature_type:str, name:str, feature_args:Dict[str,Any], count_index:Union[int,None] = None) -> Feature:
        ret_val : Feature
        if feature_type == "ActiveJobs":
            ret_val = ActiveJobs.ActiveJobs(name=name, description=feature_args["description"])
        elif feature_type == "MissionDiveTime":
            if count_index is None:
                raise TypeError("Got None for count_index, should have a value!")
            ret_val = MissionDiveTime.MissionDiveTime(name=name, description=feature_args["description"], job_num=count_index)
        elif feature_type == "JobsAttempted":
            if count_index is None:
                raise TypeError("Got None for count_index, should have a value!")
            ret_val = JobsAttempted.JobsAttempted(name=name, description=feature_args["description"], mission_num=count_index, mission_map=self._game_schema["mission_map"])
        elif feature_type == "MissionSonarTimeToComplete":
            if count_index is None:
                raise TypeError("Got None for count_index, should have a value!")
            ret_val = MissionSonarTimeToComplete.MissionSonarTimeToComplete(name=name, description=feature_args["description"], job_num=count_index)
        elif feature_type == "EvidenceBoardCompleteCount":
            ret_val = EvidenceBoardCompleteCount.EvidenceBoardCompleteCount(name=name, description=feature_args["description"])
        elif feature_type == "SessionID":
            ret_val = SessionID.SessionID(name=name, description=feature_args["description"], session_id=self._session_id)
        elif feature_type == "TopJobCompletionDestinations":
            ret_val = TopJobCompletionDestinations.TopJobCompletionDestinations(name=name, description=feature_args["description"])
        elif feature_type == "TopJobSwitchDestinations":
            ret_val = TopJobSwitchDestinations.TopJobSwitchDestinations(name=name, description=feature_args["description"])
        elif feature_type == "TotalDiveTime":
            ret_val = TotalDiveTime.TotalDiveTime(name=name, description=feature_args["description"])
        else:
            raise NotImplementedError(f"'{feature_type}' is not a valid feature for Shipwrecks.")
        return ret_val

    def LoadDetector(self, detector_type: str, name: str, detector_args: Dict[str, Any], count_index: Union[int, None] = None) -> Feature:
        raise NotImplementedError(f"'{detector_type}' is not a valid feature for Shipwrecks.")
