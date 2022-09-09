## import standard libraries
import logging
from datetime import datetime
from typing import Any, Dict, List, Type, Optional, Set
## import local files
from extractors.ExtractorLoader import ExtractorLoader
from processors.FeatureProcessor import FeatureProcessor
from processors.PopulationProcessor import PopulationProcessor
from processors.PlayerProcessor import PlayerProcessor
from processors.SessionProcessor import SessionProcessor
from schemas.GameSchema import GameSchema
from schemas.Event import Event
from schemas.ExportMode import ExportMode
from utils import Logger, ExportRow

class FeatureManager:
    def __init__(self, LoaderClass:Type[ExtractorLoader], exp_modes:Set[ExportMode], game_schema:GameSchema, feature_overrides:Optional[List[str]]):
        self._exp_types        : Set[ExportMode]           = exp_modes
        self._latest_results   : Dict[str,List[ExportRow]] = {}
        self._up_to_date       : bool                      = True
        self._LoaderClass      : Optional[Type[ExtractorLoader]] = LoaderClass
        self._processor        : FeatureProcessor

        if self.HasLoader():
            # Choose which kind of processor to make based on highest level in set of export modes.
            if ExportMode.POPULATION in exp_modes:
                self._processor = PopulationProcessor(LoaderClass=self._LoaderClass, game_schema=game_schema,
                                                      feature_overrides=feature_overrides)
            elif ExportMode.PLAYER in exp_modes:
                self._processor = PlayerProcessor(LoaderClass=self._LoaderClass, game_schema=game_schema,
                                                  player_id="Player", feature_overrides=feature_overrides)
            elif ExportMode.SESSION in exp_modes:
                self._processor = SessionProcessor(LoaderClass=self._LoaderClass, game_schema=game_schema,
                                                   player_id="Player", session_id="Session", feature_overrides=feature_overrides)
        else:
            Logger.Log("Could not export population/session data, no feature loader given!", logging.WARNING, depth=1)

    def ProcessEvent(self, event:Event) -> None:
        self._processor.ProcessEvent(event=event)
        self._up_to_date = False

    def HasLoader(self) -> bool:
        return self._LoaderClass is not None

    def GetFeatureValues(self, as_str:bool = False) -> Dict[str, List[ExportRow]]:
        start = datetime.now()
        self._try_update(as_str=as_str)
        Logger.Log(f"Time to retrieve all feature values: {datetime.now() - start}", logging.INFO, depth=2)
        return self._latest_results

    def GetPopulationFeatureNames(self) -> List[str]:
        return self._processor.GetExtractorNames() if isinstance(self._processor, PopulationProcessor) else []
    def GetPopulationFeatures(self, as_str:bool = False) -> List[ExportRow]:
        start = datetime.now()
        self._try_update(as_str=as_str)
        ret_val = self._latest_results.get('population', [])
        Logger.Log(f"Time to retrieve Population lines: {datetime.now() - start} to get {len(ret_val)} lines", logging.INFO, depth=2)
        return ret_val

    def GetPlayerFeatureNames(self) -> List[str]:
        if isinstance(self._processor, PopulationProcessor):
            return self._processor.GetPlayerFeatureNames()
        elif isinstance(self._processor, PlayerProcessor):
            return self._processor.GetExtractorNames()
        else:
            return []
    def GetPlayerFeatures(self, slice_num:int, slice_count:int, as_str:bool = False) -> List[ExportRow]:
        start   : datetime = datetime.now()
        self._try_update(as_str=as_str)
        ret_val = self._latest_results.get('players', [])
        Logger.Log(f"Time to retrieve Player lines for slice [{slice_num}/{slice_count}]: {datetime.now() - start} to get {len(ret_val)} lines", logging.INFO, depth=2)
        return ret_val

    def GetSessionFeatureNames(self) -> List[str]:
        if isinstance(self._processor, PopulationProcessor) \
        or isinstance(self._processor, PlayerProcessor):
            return self._processor.GetSessionFeatureNames()
        elif isinstance(self._processor, SessionProcessor):
            return self._processor.GetExtractorNames()
        else:
            return []
    def GetSessionFeatures(self, slice_num:int, slice_count:int, as_str:bool = False) -> List[ExportRow]:
        start   : datetime = datetime.now()
        self._try_update(as_str=as_str)
        ret_val = self._latest_results.get('sessions', [])
        time_delta = datetime.now() - start
        Logger.Log(f"Time to retrieve Session lines for slice [{slice_num}/{slice_count}]: {time_delta} to get {len(ret_val)} lines", logging.INFO, depth=2)
        return ret_val

    def ClearPopulationLines(self) -> None:
        if isinstance(self._processor, PopulationProcessor):
            self._processor.ClearLines()
    def ClearPlayerLines(self) -> None:
        if isinstance(self._processor, PopulationProcessor):
            self._processor.ClearPlayersLines()
        elif isinstance(self._processor, PlayerProcessor):
            self._processor.ClearLines()
    def ClearSessionLines(self) -> None:
        if isinstance(self._processor, PopulationProcessor) \
        or isinstance(self._processor, PlayerProcessor):
            self._processor.ClearSessionsLines()
        elif isinstance(self._processor, SessionProcessor):
            self._processor.ClearLines()

    def _try_update(self, as_str:bool = False):
        if not self._up_to_date:
            self.ProcessFeatureData()
            # for some reason, this didn't work as sum over list of lists, so get sessions manually with a normal loop:
            list_o_lists   : List[List[ExportRow]] = [[session.GetFeatureValues(as_str=as_str) for session in session_list.values()] for player_name,session_list in self._sessions.items()]
            sess_flat_list : List[ExportRow]       = list(itertools.chain.from_iterable(list_o_lists))
            self._latest_values = {
                "population" : [self._population.GetFeatureValues(as_str=as_str)],
                "players" : [player.GetFeatureValues(as_str=as_str) for player in self._players.values()],
                "sessions" : sess_flat_list
            }
            self._up_to_date = True
