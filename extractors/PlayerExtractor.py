# import standard libraries
import logging
import traceback
import sys
import typing
from typing import Any, List, Dict, IO, Type, Union
# import local files
import utils
from extractors.FeatureLoader import FeatureLoader
from games.LAKELAND.LakelandExtractor import LakelandExtractor
from managers.FileManager import FileManager
from schemas.Event import Event
from schemas.GameSchema import GameSchema

## @class PlayerProcessor
#  Class to extract and manage features for a processed csv file.
class PlayerExtractor:
    ## Constructor for the PlayerProcessor class.
    #  Simply stores some data for use later, including the type of extractor to
    #  use.
    #
    #  @param ExtractorClass The type of data extractor to use for input data.
    #         This should correspond to whatever game_id is in the TableSchema.
    #  @param game_table    A data structure containing information on how the db
    #                       table assiciated with the given game is structured. 
    #  @param game_schema   A dictionary that defines how the game data itself
    #                       is structured.
    #  @param sessions_csv_file The output file, to which we'll write the processed
    #                       feature data.
    def __init__(self, ExtractorClass: Type[FeatureLoader], game_schema: GameSchema, feature_overrides:Union[List[str],None]=None):
        ## Define instance vars
        self._ExtractorClass     : Type[FeatureLoader]      = ExtractorClass
        self._game_schema        : GameSchema               = game_schema
        self._session_extractors : Dict[str, FeatureLoader] = {}
        self._overrides          : Union[List[str],None]    = feature_overrides
        self._template_loader    :FeatureLoader
        if self._ExtractorClass is LakelandExtractor:
            self._template_loader = LakelandExtractor(session_id="", game_schema=self._game_schema, feature_overrides=self._overrides, sessions_file=sys.stdout)
        else:
            self._template_loader = self._ExtractorClass(session_id="",game_schema=self._game_schema, feature_overrides=self._overrides)

    ## Function to handle processing of a single row of data.
    #  Basically just responsible for ensuring an extractor for the session
    #  corresponding to the row already exists, then delegating the processing
    #  to that extractor.
    #  @param row_with_complex_parsed A tuple of the row data. We assume the
    #                      event_data_complex has already been parsed from JSON.
    def ProcessEvent(self, event: Event, session_file:IO[str]=sys.stdout):
        # ensure we have an extractor for the given session:
        if not event.session_id in self._session_extractors.keys():
            if event.app_id == 'LAKELAND' and self._ExtractorClass is LakelandExtractor:
                self._session_extractors[event.session_id] = LakelandExtractor(session_id=event.session_id, game_schema=self._game_schema, feature_overrides=self._overrides, sessions_file=session_file)
            else:
                self._session_extractors[event.session_id] = self._ExtractorClass(session_id=event.session_id, game_schema=self._game_schema, feature_overrides=self._overrides)
        self._session_extractors[event.session_id].ExtractFromEvent(event)

    ## Function to calculate aggregate features of all extractors created by the
    #  PlayerProcessor. Just calls the function once on each extractor.
    def CalculateAggregateFeatures(self):
        for extractor in self._session_extractors.values():
            extractor.CalculateAggregateFeatures()

    def GetPlayerFeatureNames(self) -> List[str]:
        return self._template_loader.GetFeatureNames(self._game_schema, overrides=self._overrides)

    def GetPlayerFeatures(self) -> List[List[Any]]:
        return [extractor.GetFeatureValues() for extractor in self._session_extractors.values()]

    ## Function to write out the header for a processed csv file.
    #  Just runs the header writer for whichever Extractor subclass we were given.
    # def WritePlayerFileHeader(self, file_mgr:FileManager, separator:str = "\t"):
    #     self._template_loader.WriteFileHeader(game_schema=self._game_schema, file=file_mgr.GetPlayersFile(), separator=separator)

    ## Function to write out all data for the extractors created by the
    #  PlayerProcessor. Just calls the "write" function once for each extractor.
    # def WritePlayerFileLines(self, file_mgr:FileManager, separator:str = "\t"):
    #     for extractor in self._session_extractors.values():
    #         extractor.WriteFeatureValues(file=file_mgr.GetPlayersFile(), separator=separator)

    ##  Function to empty the list of lines stored by the PlayerProcessor.
    #   This is helpful if we're processing a lot of data and want to avoid
    #   eating too much memory.
    def ClearLines(self):
        utils.Logger.toStdOut(f"Clearing {len(self._session_extractors)} entries from PlayerProcessor.", logging.DEBUG)
        self._session_extractors = {}