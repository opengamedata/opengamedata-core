## import standard libraries
import abc
import logging
from datetime import datetime
from pprint import pformat
from typing import Any, Dict, List, Tuple, Optional, Union

# import local files
from ogd.core.interfaces.Interface import Interface
from ogd.core.models.Event import Event
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.schemas.tables.TableSchema import TableSchema
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.utils.Logger import Logger

class DataInterface(Interface):

    # *** ABSTRACTS ***

    @abc.abstractmethod
    def _allIDs(self) -> List[str]:
        pass

    @abc.abstractmethod
    def _fullDateRange(self) -> Dict[str,datetime]:
        pass

    @abc.abstractmethod
    def _rowsFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]] = None, exclude_rows:Optional[List[str]] = None) -> List[Tuple]:
        pass

    @abc.abstractmethod
    def _IDsFromDates(self, min:datetime, max:datetime, versions:Optional[List[int]] = None) -> List[str]:
        pass

    @abc.abstractmethod
    def _datesFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]] = None) -> Dict[str,datetime]:
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

    def AllIDs(self) -> Optional[List[str]]:
        ret_val = None
        if self.IsOpen():
            ret_val = self._allIDs()
        else:
            Logger.Log("Can't retrieve list of all session IDs, the source interface is not open!", logging.WARNING, depth=3)
        return ret_val

    def FullDateRange(self) -> Union[Dict[str,datetime], Dict[str,None]]:
        ret_val = {'min':None, 'max':None}
        if self.IsOpen():
            ret_val = self._fullDateRange()
        else:
            Logger.Log(f"Could not get full date range, the source interface is not open!", logging.WARNING, depth=3)
        return ret_val

    def EventsFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]]=None, exclude_rows:Optional[List[str]]=None) -> Optional[List[Event]]:
        ret_val = None

        _curr_sess : str      = ""
        _evt_sess_index : int = 1
        print("HERE!")
        if self.IsOpen():
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

    def IDsFromDates(self, min:datetime, max:datetime, versions:Optional[List[int]]=None) -> Optional[List[str]]:
        ret_val = None
        if not self.IsOpen():
            str_min, str_max = min.strftime("%Y%m%d"), max.strftime("%Y%m%d")
            Logger.Log(f"Could not retrieve IDs for {str_min}-{str_max}, the source interface is not open!", logging.WARNING, depth=3)
        else:
            ret_val = self._IDsFromDates(min=min, max=max, versions=versions)
        return ret_val

    def DatesFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]]=None) -> Union[Dict[str,datetime], Dict[str,None]]:
        ret_val = {'min':None, 'max':None}
        if not self.IsOpen():
            Logger.Log(f"Could not retrieve date range {len(id_list)} session IDs, the source interface is not open!", logging.WARNING, depth=3)
        else:
            Logger.Log(f"Retrieving date range from IDs with {id_mode.name} ID mode.", logging.DEBUG, depth=3)
            ret_val = self._datesFromIDs(id_list=id_list, id_mode=id_mode, versions=versions)
        return ret_val

    # *** PROPERTIES ***

    @property
    def _TableSchema(self) -> TableSchema:
        return self._table_schema

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
