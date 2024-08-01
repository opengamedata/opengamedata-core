"""EventTableSchema Module"""
# import standard libraries
import logging
import re
from datetime import datetime, timedelta, timezone
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

# import 3rd-party libraries
from dateutil import parser

# import local files
from ogd.core import schemas
from ogd.core.schemas.tables.TableSchema import TableSchema
from ogd.core.models.Event import Event, EventSource
from ogd.core.utils import utils
from ogd.core.utils.Logger import Logger
from ogd.core.utils.typing import Map

## @class TableSchema
#  Dumb struct to hold useful info about the structure of database data
#  for a particular game.
#  This includes the indices of several important database columns, the names
#  of the database columns, the max and min levels in the game, and a list of
#  IDs for the game sessions in the given requested date range.
class EventTableSchema(TableSchema):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, schema_name:str, schema_path:Path = Path(schemas.__file__).parent / "table_schemas/"):
        """Constructor for the TableSchema class.
        Given a database connection and a game data request,
        this retrieves a bit of information from the database to fill in the
        class variables.

        :param schema_name: The filename for the table schema JSON.
        :type schema_name: str
        :param schema_path: Path to find the given table schema file, defaults to "./schemas/table_schemas/"
        :type schema_path: str, optional
        :param is_legacy: [description], defaults to False
        :type is_legacy: bool, optional
        """
        super().__init__(schema_name=schema_name, schema_path=schema_path)

    @property
    def AsMarkdown(self) -> str:
        ret_val = "\n\n".join([
            "## Database Columns",
            "The individual columns recorded in the database for this game.",
            "\n".join([item.AsMarkdown for item in self.Columns]),
            "## Event Object Elements",
            "The elements (member variables) of each Event object, available to programmers when writing feature extractors. The right-hand side shows which database column(s) are mapped to a given element.",
            self._column_map.AsMarkdown,
            ""])
        return ret_val

    @property
    def SessionIDColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.SessionID, int):
            ret_val = self.ColumnNames[self._column_map.SessionID]
        elif isinstance(self._column_map.SessionID, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.SessionID])
        return ret_val

    @property
    def AppIDColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.AppID, int):
            ret_val = self.ColumnNames[self._column_map.AppID]
        elif isinstance(self._column_map.AppID, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.AppID])
        return ret_val

    @property
    def TimestampColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.Timestamp, int):
            ret_val = self.ColumnNames[self._column_map.Timestamp]
        elif isinstance(self._column_map.Timestamp, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.Timestamp])
        return ret_val

    @property
    def EventNameColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.EventName, int):
            ret_val = self.ColumnNames[self._column_map.EventName]
        elif isinstance(self._column_map.EventName, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.EventName])
        return ret_val

    @property
    def EventDataColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.EventData, int):
            ret_val = self.ColumnNames[self._column_map.EventData]
        elif isinstance(self._column_map.EventData, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.EventData])
        return ret_val

    @property
    def EventSourceColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.EventSource, int):
            ret_val = self.ColumnNames[self._column_map.EventSource]
        elif isinstance(self._column_map.EventSource, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.EventSource])
        return ret_val

    @property
    def AppVersionColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.AppVersion, int):
            ret_val = self.ColumnNames[self._column_map.AppVersion]
        elif isinstance(self._column_map.AppVersion, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.AppVersion])
        return ret_val

    @property
    def AppBranchColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.AppBranch, int):
            ret_val = self.ColumnNames[self._column_map.AppBranch]
        elif isinstance(self._column_map.AppBranch, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.AppBranch])
        return ret_val

    @property
    def LogVersionColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.LogVersion, int):
            ret_val = self.ColumnNames[self._column_map.LogVersion]
        elif isinstance(self._column_map.LogVersion, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.LogVersion])
        return ret_val

    @property
    def TimeOffsetColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.TimeOffset, int):
            ret_val = self.ColumnNames[self._column_map.TimeOffset]
        elif isinstance(self._column_map.TimeOffset, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.TimeOffset])
        return ret_val

    @property
    def UserIDColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.UserID, int):
            ret_val = self.ColumnNames[self._column_map.UserID]
        elif isinstance(self._column_map.UserID, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.UserID])
        return ret_val

    @property
    def UserDataColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.UserData, int):
            ret_val = self.ColumnNames[self._column_map.UserData]
        elif isinstance(self._column_map.UserData, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.UserData])
        return ret_val

    @property
    def GameStateColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.GameState, int):
            ret_val = self.ColumnNames[self._column_map.GameState]
        elif isinstance(self._column_map.GameState, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.GameState])
        return ret_val

    @property
    def EventSequenceIndexColumn(self) -> Optional[str]:
        ret_val = None
        if isinstance(self._column_map.EventSequenceIndex, int):
            ret_val = self.ColumnNames[self._column_map.EventSequenceIndex]
        elif isinstance(self._column_map.EventSequenceIndex, list):
            ret_val = ", ".join([self.ColumnNames[idx] for idx in self._column_map.EventSequenceIndex])
        return ret_val

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    _conversion_warnings = []
    def RowToEvent(self, row:Tuple, concatenator:str = '.', fallbacks:utils.map={}):
        """Function to convert a row to an Event, based on the loaded schema.
        In general, columns specified in the schema's column_map are mapped to corresponding elements of the Event.
        If the column_map gave a list, rather than a single column name, the values from each column are concatenated in order with '.' character separators.
        Finally, the concatenated values (or single value) are parsed according to the type required by Event.
        One exception: For event_data, we expect to create a Dict object, so each column in the list will have its value parsed according to the type in 'columns',
            and placed into a dict mapping the original column name to the parsed value (unless the parsed value is a dict, then it is merged into the top-level dict).

        :param row: The raw row data for an event. Generally assumed to be a tuple, though in principle a list would be fine too.
        :type  row: Tuple[str]
        :param concatenator: A string to use as a separator when concatenating multiple columns into a single Event element.
        :type  concatenator: str
        :return: [description]
        :rtype: [type]
        """
        # define vars to be passed as params
        sess_id : str
        app_id  : str
        tstamp  : datetime
        ename   : str
        edata   : Map
        app_ver : str
        app_br  : str
        log_ver : str
        offset  : Optional[timezone]
        uid     : Optional[str]
        udata   : Optional[Map]
        state   : Optional[Map]
        index   : Optional[int]

        # 2) Handle event_data parameter, a special case.
        #    For this case we've got to parse the json, and then fold in whatever other columns were desired.
        # 3) Assign vals to our arg vars and pass to Event ctor.
        sess_id = self._getValueFromRow(row=row, indices=self._column_map.SessionID,   concatenator=concatenator, fallback=fallbacks.get('session_id'))
        if not isinstance(sess_id, str):
            if "sess_id" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set session_id as {type(sess_id)}, but session_id should be a string", logging.WARN)
                EventTableSchema._conversion_warnings.append("sess_id")
            sess_id = str(sess_id)

        app_id  = self._getValueFromRow(row=row, indices=self._column_map.AppID,       concatenator=concatenator, fallback=fallbacks.get('app_id'))
        if not isinstance(app_id, str):
            if "app_id" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set app_id as {type(app_id)}, but app_id should be a string", logging.WARN)
                EventTableSchema._conversion_warnings.append("app_id")
            app_id = str(app_id)

        tstamp  = self._getValueFromRow(row=row, indices=self._column_map.Timestamp,   concatenator=concatenator, fallback=fallbacks.get('timestamp'))
        if not isinstance(tstamp, datetime):
            if "timestamp" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema parsed timestamp as {type(tstamp)}, but timestamp should be a datetime", logging.WARN)
                EventTableSchema._conversion_warnings.append("timestamp")
            tstamp = TableSchema._convertDateTime(tstamp)

        ename   = self._getValueFromRow(row=row, indices=self._column_map.EventName,   concatenator=concatenator, fallback=fallbacks.get('event_name'))
        if not isinstance(ename, str):
            if "ename" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set event_name as {type(ename)}, but event_name should be a string", logging.WARN)
                EventTableSchema._conversion_warnings.append("ename")
            ename = str(ename)

        datas : Dict[str, Any] = self._getValueFromRow(row=row, indices=self._column_map.EventData,   concatenator=concatenator, fallback=fallbacks.get('event_data'))

        # TODO: go bac to isostring function; need 0-padding on ms first, though
        edata   = dict(sorted(datas.items())) # Sort keys alphabetically

        esrc    = self._getValueFromRow(row=row, indices=self._column_map.EventSource, concatenator=concatenator, fallback=fallbacks.get('event_source', EventSource.GAME))
        if not isinstance(esrc, EventSource):
            if "esrc" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set event_source as {type(esrc)}, but event_source should be an EventSource", logging.WARN)
                EventTableSchema._conversion_warnings.append("esrc")
            esrc = EventSource.GENERATED if esrc == "GENERATED" else EventSource.GAME

        app_ver = self._getValueFromRow(row=row, indices=self._column_map.AppVersion,  concatenator=concatenator, fallback=fallbacks.get('app_version', "0"))
        if not isinstance(app_ver, str):
            if "app_ver" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set app_version as {type(app_ver)}, but app_version should be a string", logging.WARN)
                EventTableSchema._conversion_warnings.append("app_ver")
            app_ver = str(app_ver)

        app_br = self._getValueFromRow(row=row, indices=self._column_map.AppBranch,  concatenator=concatenator, fallback=fallbacks.get('app_branch'))
        if not isinstance(app_br, str):
            if "app_br" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set app_branch as {type(app_br)}, but app_branch should be a string", logging.WARN)
                EventTableSchema._conversion_warnings.append("app_br")
            app_br = str(app_br)

        log_ver = self._getValueFromRow(row=row, indices=self._column_map.LogVersion,  concatenator=concatenator, fallback=fallbacks.get('log_version', "0"))
        if not isinstance(log_ver, str):
            if "log_ver" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set log_version as {type(log_ver)}, but log_version should be a string", logging.WARN)
                EventTableSchema._conversion_warnings.append("log_ver")
            log_ver = str(log_ver)

        offset = self._getValueFromRow(row=row, indices=self._column_map.TimeOffset,  concatenator=concatenator, fallback=fallbacks.get('time_offset'))
        if isinstance(offset, timedelta):
            if "offset" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set offset as {type(offset)}, but offset should be a timezone", logging.WARN)
                EventTableSchema._conversion_warnings.append("offset")
            offset = timezone(offset)

        uid     = self._getValueFromRow(row=row, indices=self._column_map.UserID,      concatenator=concatenator, fallback=fallbacks.get('user_id'))
        if uid is not None and not isinstance(uid, str):
            if "uid" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set user_id as {type(uid)}, but user_id should be a string", logging.WARN)
                EventTableSchema._conversion_warnings.append("uid")
            uid = str(uid)

        udata   = self._getValueFromRow(row=row, indices=self._column_map.UserData,    concatenator=concatenator, fallback=fallbacks.get('user_data'))

        state   = self._getValueFromRow(row=row, indices=self._column_map.GameState,   concatenator=concatenator, fallback=fallbacks.get('game_state'))

        index   = self._getValueFromRow(row=row, indices=self._column_map.EventSequenceIndex, concatenator=concatenator, fallback=fallbacks.get('event_sequence_index'))
        if index is not None and not isinstance(index, int):
            if "index" not in EventTableSchema._conversion_warnings:
                Logger.Log(f"{self._table_format_name} table schema set event_sequence_index as {type(index)}, but event_sequence_index should be an int", logging.WARN)
                EventTableSchema._conversion_warnings.append("index")
            index = int(index)

        return Event(session_id=sess_id, app_id=app_id, timestamp=tstamp,
                     event_name=ename, event_data=edata, event_source=esrc,
                     app_version=app_ver, app_branch=app_br, log_version=log_ver,
                     time_offset=offset, user_id=uid, user_data=udata,
                     game_state=state, event_sequence_index=index)

    # *** PRIVATE STATICS ***
