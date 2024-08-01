## import standard libraries
import abc
import logging
from datetime import datetime
from pprint import pformat
from typing import Any, Dict, List, Tuple, Optional, Union

# import local files
from ogd.core.connectors.interfaces.Interface import Interface
from ogd.core.models.Event import Event
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.schemas.tables.TableSchema import TableSchema
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.utils.Logger import Logger

class EventInterface(Interface):

    # *** ABSTRACTS ***

    @abc.abstractmethod
    def _rowsFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]] = None, exclude_rows:Optional[List[str]] = None) -> List[Tuple]:
        """Function to retrieve all rows for a given set of Session or Player IDs, which can be converted to Event objects by a TableSchema

        :param id_list: List of IDs whose events should be retrieved from the database. These are session IDs if id_mode is SESSION, or user IDs if id_mode is USER.
        :type id_list: List[str]
        :param id_mode: The mode of ID to use for interpreting the id_list, defaults to IDMode.SESSION
        :type id_mode: IDMode, optional
        :param versions: List of log_versions to include in the query, any versions not in the list will be ignored. Defaults to None
        :type versions: Optional[List[int]], optional
        :param exclude_rows: List of event names to be excluded from the query, defaults to None
        :type exclude_rows: Optional[List[str]], optional
        :return: A list of raw results from the query.
        :rtype: List[Tuple]
        """
        pass

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:GameSourceSchema, fail_fast:bool):
        super().__init__(config=config)
        self._fail_fast = fail_fast
        self._game_id : str  = game_id
        self._table_schema : TableSchema = TableSchema(schema_name=self._config.TableSchema)

    def __del__(self):
        self.Close()

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def EventsFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]]=None, exclude_rows:Optional[List[str]]=None) -> Optional[List[Event]]:
        ret_val = None

        _curr_sess : str      = ""
        _evt_sess_index : int = 1
        if self.IsOpen:
            Logger.Log(f"Retrieving rows from IDs with {id_mode.name} ID mode.", logging.DEBUG, depth=3)
            _rows   = self._rowsFromIDs(id_list=id_list, id_mode=id_mode, versions=versions, exclude_rows=exclude_rows)
            _fallbacks = {"app_id":self._game_id}
            ret_val = []
            for row in _rows:
                try:
                    next_event = self._table_schema.RowToEvent(row=row, fallbacks=_fallbacks)
                    # in case event index was not given, we should fall back on using the order it came to us.
                    if next_event.SessionID != _curr_sess:
                        _curr_sess = next_event.SessionID
                        _evt_sess_index = 1
                    next_event.FallbackDefaults(index=_evt_sess_index)
                    _evt_sess_index += 1
                except Exception as err:
                    if self._fail_fast:
                        Logger.Log(f"Error while converting row to Event\nFull error: {err}\nRow data: {pformat(row)}", logging.ERROR, depth=2)
                        raise err
                    else:
                        Logger.Log(f"Error while converting row ({row}) to Event. This row will be skipped.\nFull error: {err}", logging.WARNING, depth=2)
                else:
                    ret_val.append(next_event)
        else:
            Logger.Log(f"Could not retrieve rows for {len(id_list)} session IDs, the source interface is not open!", logging.WARNING, depth=3)
        return ret_val

    # *** PROPERTIES ***

    @property
    def _TableSchema(self) -> TableSchema:
        return self._table_schema

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
