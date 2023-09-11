## import standard libraries
import logging
from typing import Dict, List, Set, Union

# import local files
from interfaces.outerfaces.DataOuterface import DataOuterface
from schemas.ExportMode import ExportMode
from schemas.configs.GameSourceMapSchema import GameSourceSchema
from utils.Logger import Logger
from utils.utils import ExportRow

class DictionaryOuterface(DataOuterface):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:GameSourceSchema, export_modes:Set[ExportMode], out_dict:Dict[str, Dict[str, Union[List[str], List[ExportRow]]]]):
        super().__init__(game_id=game_id, config=config, export_modes=export_modes)
        self._out = out_dict
        self._raw_evts : List[ExportRow] = []
        self._all_evts : List[ExportRow] = []
        self._sess     : List[ExportRow] = []
        self._plrs     : List[ExportRow] = []
        self._pops     : List[ExportRow] = []
        # self.Open()

    def __del__(self):
        self.Close()

    # *** IMPLEMENT ABSTRACTS ***

    def _open(self) -> bool:
        self._out['raw_events']  = { "cols" : [], "vals" : self._raw_evts }
        self._out['all_events']  = { "cols" : [], "vals" : self._all_evts }
        self._out['sessions']    = { "cols" : [], "vals" : self._sess }
        self._out['players']     = { "cols" : [], "vals" : self._plrs }
        self._out['populations'] = { "cols" : [], "vals" : self._pops }
        return True

    def _close(self) -> bool:
        return True

    def _destination(self, mode:ExportMode) -> str:
        return "RequestResult"

    def _removeExportMode(self, mode:ExportMode):
        if mode == ExportMode.EVENTS:
            self._raw_evts = []
            self._out['raw_events']  = { "cols" : [], "vals" : self._raw_evts }
        elif mode == ExportMode.DETECTORS:
            self._all_evts = []
            self._out['all_events']  = { "cols" : [], "vals" : self._all_evts }
        elif mode == ExportMode.SESSION:
            self._sess = []
            self._out['sessions']    = { "cols" : [], "vals" : self._sess }
        elif mode == ExportMode.PLAYER:
            self._plrs = []
            self._out['players']     = { "cols" : [], "vals" : self._plrs }
        elif mode == ExportMode.POPULATION:
            self._pops = []
            self._out['populations'] = { "cols" : [], "vals" : self._pops }

    def _writeRawEventsHeader(self, header:List[str]) -> None:
        self._out['raw_events']['cols'] = header

    def _writeProcessedEventsHeader(self, header:List[str]) -> None:
        self._out['all_events']['cols'] = header

    def _writeSessionHeader(self, header:List[str]) -> None:
        self._out['sessions']['cols'] = header

    def _writePlayerHeader(self, header:List[str]) -> None:
        self._out['players']['cols'] = header

    def _writePopulationHeader(self, header:List[str]) -> None:
        self._out['populations']['cols'] = header

    def _writeRawEventLines(self, events:List[ExportRow]) -> None:
        # I'm always a bit fuzzy on when Python will copy vs. store reference,
        # but tests indicate if we just update self._evts, self._out is updated automatically
        # since it maps to self._evts.
        # Similar for the other functions here.
        self._raw_evts += events

    def _writeProcessedEventLines(self, events:List[ExportRow]) -> None:
        # I'm always a bit fuzzy on when Python will copy vs. store reference,
        # but tests indicate if we just update self._evts, self._out is updated automatically
        # since it maps to self._evts.
        # Similar for the other functions here.
        self._all_evts += events

    def _writeSessionLines(self, sessions:List[ExportRow]) -> None:
        self._sess += sessions

    def _writePlayerLines(self, players:List[ExportRow]) -> None:
        self._plrs += players

    def _writePopulationLines(self, populations:List[ExportRow]) -> None:
        self._pops += populations

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
