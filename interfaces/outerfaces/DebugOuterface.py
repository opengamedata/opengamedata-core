## import standard libraries
import logging
from typing import List, Set

# import local files
from interfaces.outerfaces.DataOuterface import DataOuterface
from schemas.Event import Event
from schemas.ExportMode import ExportMode
from schemas.FeatureData import FeatureData
from schemas.data_sources.GameSourceSchema import GameSourceSchema
from utils.Logger import Logger
from utils.utils import ExportRow

class DebugOuterface(DataOuterface):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:GameSourceSchema, export_modes:Set[ExportMode]):
        super().__init__(game_id=game_id, export_modes=export_modes, config=config)
        # self.Open()

    def __del__(self):
        self.Close()

    # *** IMPLEMENT ABSTRACTS ***

    def _open(self) -> bool:
        self._display(f"Using a debug outerface to view OGD output for {self._game_id}.")
        return True

    def _close(self) -> bool:
        self._display(f"No longer using a debug outerface to view OGD output for {self._game_id}.")
        return True

    def _destination(self, mode:ExportMode) -> str:
        return "Logger.Log"

    def _removeExportMode(self, mode:ExportMode):
        if mode == ExportMode.EVENTS:
            self._display("No longer outputting raw event data to debug stream.")
        if mode == ExportMode.DETECTORS:
            self._display("No longer outputting processed event data to debug stream.")
        elif mode == ExportMode.SESSION:
            self._display("No longer outputting session data to debug stream.")
        elif mode == ExportMode.PLAYER:
            self._display("No longer outputting player data to debug stream.")
        elif mode == ExportMode.POPULATION:
            self._display("No longer outputting population data to debug stream.")

    def _writeRawEventsHeader(self, header:List[str]) -> None:
        self._display("Raw events header:")
        self._display(header)

    def _writeProcessedEventsHeader(self, header:List[str]) -> None:
        self._display("Processed events header:")
        self._display(header)

    def _writeSessionHeader(self, header:List[str]) -> None:
        self._display("Sessions header:")
        self._display(header)

    def _writePlayerHeader(self, header:List[str]) -> None:
        self._display("Player header:")
        self._display(header)

    def _writePopulationHeader(self, header:List[str]) -> None:
        self._display("Population header:")
        self._display(header)

    def _writeRawEventLines(self, events:List[Event]) -> None:
        self._display("Raw event data:")
        _lengths = [len(elem) for elem in events]
        self._display(f"{len(events)} raw events, average length {sum(_lengths) / len(_lengths) if len(_lengths) > 0 else 'N/A'}")

    def _writeProcessedEventLines(self, events:List[Event]) -> None:
        self._display("Processed event data:")
        _lengths = [len(elem) for elem in events]
        self._display(f"{len(events)} processed events, average length {sum(_lengths) / len(_lengths) if len(_lengths) > 0 else 'N/A'}")

    def _writeSessionLines(self, sessions:List[List[FeatureData]]) -> None:
        self._display("Session data:")
        _lengths = [len(elem) for elem in sessions]
        self._display(f"{len(sessions)} events, average length {sum(_lengths) / len(_lengths) if len(_lengths) > 0 else 'N/A'}")

    def _writePlayerLines(self, players:List[List[FeatureData]]) -> None:
        self._display("Player data:")
        _lengths = [len(elem) for elem in players]
        self._display(f"{len(players)} events, average length {sum(_lengths) / len(_lengths) if len(_lengths) > 0 else 'N/A'}")

    def _writePopulationLines(self, populations:List[List[FeatureData]]) -> None:
        self._display("Population data:")
        _lengths = [len(elem) for elem in populations]
        self._display(f"{len(populations)} events, average length {sum(_lengths) / len(_lengths) if len(_lengths) > 0 else 'N/A'}")

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***

    def _display(self, msg):
        Logger.Log(f"DebugOuterface: {msg}", logging.DEBUG)
