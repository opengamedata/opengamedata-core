"""Outerface Module
"""
## import standard libraries
import abc
import logging
from typing import Any, Dict, List, Set

# import local files
from ogd.core.connectors.StorageConnector import StorageConnector
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.models.enums.ExportMode import ExportMode
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.utils.Logger import Logger
from ogd.core.utils.utils import ExportRow

class Outerface(StorageConnector):
    """Base class for feature and event output.

    :param Interface: _description_
    :type Interface: _type_
    :return: _description_
    :rtype: _type_
    """

    # *** ABSTRACTS ***

    @abc.abstractmethod
    def _destination(self, mode:ExportMode) -> str:
        pass

    @abc.abstractmethod
    def _removeExportMode(self, mode:ExportMode) -> str:
        pass

    @abc.abstractmethod
    def _writeRawEventsHeader(self, header:List[str]) -> None:
        pass

    @abc.abstractmethod
    def _writeProcessedEventsHeader(self, header:List[str]) -> None:
        pass

    @abc.abstractmethod
    def _writeSessionHeader(self, header:List[str]) -> None:
        pass

    @abc.abstractmethod
    def _writePlayerHeader(self, header:List[str]) -> None:
        pass

    @abc.abstractmethod
    def _writePopulationHeader(self, header:List[str]) -> None:
        pass

    @abc.abstractmethod
    def _writeRawEventLines(self, events:List[ExportRow]) -> None:
        pass

    @abc.abstractmethod
    def _writeProcessedEventLines(self, events:List[ExportRow]) -> None:
        pass

    @abc.abstractmethod
    def _writeSessionLines(self, sessions:List[ExportRow]) -> None:
        pass

    @abc.abstractmethod
    def _writePlayerLines(self, players:List[ExportRow]) -> None:
        pass

    @abc.abstractmethod
    def _writePopulationLines(self, populations:List[ExportRow]) -> None:
        pass

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id, config:GameSourceSchema, export_modes:Set[ExportMode]):
        super().__init__(config=config)
        self._game_id : str  = game_id
        self._modes   : Set[ExportMode] = export_modes
        self._session_ct : int = 0

    def __del__(self):
        self.Close()

    @property
    def ExportModes(self) -> Set[ExportMode]:
        return self._modes

    @property
    def SessionCount(self) -> int:
        return self._session_ct
    @SessionCount.setter
    def SessionCount(self, new_val) -> None:
        self._session_ct = new_val

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def Destination(self, mode:ExportMode):
        return self._destination(mode=mode)

    def RemoveExportMode(self, mode:ExportMode):
        self._removeExportMode(mode)
        self._modes.discard(mode)
        Logger.Log(f"Removed mode {mode} from {type(self).__name__} output.", logging.INFO)

    def WriteHeader(self, header:List[str], mode:ExportMode):
        if mode in self.ExportModes:
            match (mode):
                case ExportMode.EVENTS: 
                    self._writeRawEventsHeader(header=header)
                    Logger.Log(f"Wrote event header for {self._game_id} events", depth=3)
                case ExportMode.DETECTORS:
                    self._writeProcessedEventsHeader(header=header)
                    Logger.Log(f"Wrote processed event header for {self._game_id} events", depth=3)
                case ExportMode.SESSION:
                    self._writeSessionHeader(header=header)
                    Logger.Log(f"Wrote session feature header for {self._game_id} sessions", depth=3)
                case ExportMode.PLAYER:
                    self._writePlayerHeader(header=header)
                    Logger.Log(f"Wrote player feature header for {self._game_id} players", depth=3)
                case ExportMode.POPULATION:
                    self._writePopulationHeader(header=header)
                    Logger.Log(f"Wrote population feature header for {self._game_id} populations", depth=3)
                case _:
                    Logger.Log(f"Failed to write header for unrecognized export mode {mode}!", level=logging.WARN, depth=3)
        else:
            Logger.Log(f"Skipping WriteLines in {type(self).__name__}, export mode {mode} is not enabled for this outerface", depth=3)

    def WriteLines(self, lines:List[ExportRow], mode:ExportMode) -> None:
        if mode in self.ExportModes:
            match (mode):
                case ExportMode.EVENTS:
                    self._writeRawEventLines(events=lines)
                    Logger.Log(f"Wrote {len(lines)} {self._game_id} events", depth=3)
                case ExportMode.DETECTORS:
                    self._writeProcessedEventLines(events=lines)
                    Logger.Log(f"Wrote {len(lines)} {self._game_id} processed events", depth=3)
                case ExportMode.SESSION:
                    self._writeSessionLines(sessions=lines)
                    Logger.Log(f"Wrote {len(lines)} {self._game_id} session lines", depth=3)
                case ExportMode.PLAYER:
                    self._writePlayerLines(players=lines)
                    Logger.Log(f"Wrote {len(lines)} {self._game_id} player lines", depth=3)
                case ExportMode.POPULATION:
                    self._writePopulationLines(populations=lines)
                    Logger.Log(f"Wrote {len(lines)} {self._game_id} population lines", depth=3)
                case _:
                    Logger.Log(f"Failed to write lines for unrecognized export mode {mode}!", level=logging.WARN, depth=3)
        else:
            Logger.Log(f"Skipping WriteLines in {type(self).__name__}, export mode {mode} is not enabled for this outerface", depth=3)

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
