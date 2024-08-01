## import standard libraries
import json
import logging
import re
from dateutil import parser
from datetime import datetime, time, timedelta, timezone
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Final, List, Tuple, Optional, Union
## import local files
from ogd.core import schemas
from ogd.core.models.Event import Event, EventSource
from ogd.core.schemas.tables.ColumnMapSchema import ColumnMapSchema
from ogd.core.schemas.tables.ColumnSchema import ColumnSchema
from ogd.core.utils import utils
from ogd.core.utils.Logger import Logger
from ogd.core.utils.typing import Map

## @class TableSchema
#  Dumb struct to hold useful info about the structure of database data
#  for a particular game.
#  This includes the indices of several important database columns, the names
#  of the database columns, the max and min levels in the game, and a list of
#  IDs for the game sessions in the given requested date range.
class TableSchema:

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
        # declare and initialize vars
        self._schema            : Optional[Dict[str, Any]]
        self._column_map        : ColumnMapSchema
        self._columns           : List[ColumnSchema] = []
        self._table_format_name : str                    = schema_name

        if not self._table_format_name.lower().endswith(".json"):
            self._table_format_name += ".json"
        self._schema = utils.loadJSONFile(filename=self._table_format_name, path=schema_path)

        # after loading the file, take the stuff we need and store.
        if self._schema is not None:
            self._columns    = [ColumnSchema(column_details) for column_details in self._schema.get('columns', [])]
            self._column_map = ColumnMapSchema(map=self._schema.get('column_map', {}), column_names=self.ColumnNames)
        else:
            Logger.Log(f"Could not find event_data_complex schemas at {schema_path}{schema_name}", logging.ERROR)

    @property
    def ColumnNames(self) -> List[str]:
        """Function to get the names of all columns in the schema.

        :return: Names of each column in the schema.
        :rtype: List[str]
        """
        return [col.Name for col in self._columns]

    @property
    def Columns(self) -> List[ColumnSchema]:
        return self._columns

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PRIVATE STATICS ***

    @staticmethod
    def _parse(input:Any, col_schema:ColumnSchema) -> Any:
        """Applies whatever parsing is appropriate based on what type the schema said a column contained.

        :param input: _description_
        :type input: str
        :param col_schema: _description_
        :type col_schema: ColumnSchema
        :return: _description_
        :rtype: Any
        """
        if input is None:
            return None
        if input == "None" or input == "null" or input == "nan":
            return None
        elif col_schema.ValueType == 'str':
            return str(input)
        elif col_schema.ValueType == 'int':
            return int(input)
        elif col_schema.ValueType == 'float':
            return float(input)
        elif col_schema.ValueType == 'datetime':
            return input if isinstance(input, datetime) else TableSchema._convertDateTime(str(input))
        elif col_schema.ValueType == 'timedelta':
            return input if isinstance(input, timedelta) else TableSchema._convertTimedelta(str(input))
        elif col_schema.ValueType == 'timezone':
            return input if isinstance(input, timezone) else TableSchema._convertTimezone(str(input))
        elif col_schema.ValueType == 'json':
            try:
                if isinstance(input, dict):
                    # if input was a dict already, then just give it back. Else, try to load it from string.
                    return input
                elif isinstance(input, str):
                    if input != 'None' and input != '': # watch out for nasty corner cases.
                        return json.loads(input)
                    else:
                        return None
                else:
                    return json.loads(str(input))
            except JSONDecodeError as err:
                Logger.Log(f"Could not parse input '{input}' of type {type(input)} from column {col_schema.Name}, got the following error:\n{str(err)}", logging.WARN)
                return {}
        elif col_schema.ValueType.startswith('enum'):
            # if the column is supposed to be an enum, for now we just stick with the string.
            return str(input)

    @staticmethod
    def _convertDateTime(time_str:str) -> datetime:
        ret_val : datetime

        if time_str == "None" or time_str == "none" or time_str == "null" or time_str == "nan":
            raise ValueError(f"Got a non-timestamp value of {time_str} when converting a datetime column of an Event!")

        formats = ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f"]

        # for fmt in formats:
        try:
            ret_val = parser.isoparse(time_str)
            # ret_val = datetime.strptime(time_str, fmt)
        except ValueError as err:
            Logger.Log(f"Could not parse time string '{time_str}', got error {err}")
            raise err
        else:
            return ret_val
        # raise ValueError(f"Could not parse timestamp {time_str}, it did not match any expected formats.")

    @staticmethod
    def _convertTimedelta(time_str:str) -> Optional[timedelta]:
        ret_val : Optional[timedelta]

        if time_str == "None" or time_str == "none" or time_str == "null" or time_str == "nan":
            return None
        elif re.fullmatch(pattern=r"\d+:\d+:\d+(\.\d+)?", string=time_str):
            try:
                pieces = time_str.split(':')
                seconds_pieces = pieces[2].split('.')
                ret_val = timedelta(hours=int(pieces[0]),
                                    minutes=int(pieces[1]),
                                    seconds=int(seconds_pieces[0]),
                                    milliseconds=int(seconds_pieces[1]) if len(seconds_pieces) > 1 else 0)
            except ValueError as err:
                pass
            except IndexError as err:
                pass
            else:
                return ret_val
        elif re.fullmatch(pattern=r"-?\d+", string=time_str):
            try:
                ret_val = timedelta(seconds=int(time_str))
            except ValueError as err:
                pass
            else:
                return ret_val
        raise ValueError(f"Could not parse timedelta {time_str} of type {type(time_str)}, it did not match any expected formats.")

    @staticmethod
    def _convertTimezone(time_str:str) -> Optional[timezone]:
        ret_val : Optional[timezone]

        if time_str == "None" or time_str == "none" or time_str == "null" or time_str == "nan":
            return None
        elif re.fullmatch(pattern=r"UTC[+-]\d+:\d+", string=time_str):
            try:
                pieces = time_str.removeprefix("UTC").split(":")
                ret_val = timezone(timedelta(hours=int(pieces[0]), minutes=int(pieces[1])))
            except ValueError as err:
                pass
            else:
                return ret_val
        raise ValueError(f"Could not parse timezone {time_str} of type {type(time_str)}, it did not match any expected formats.")

    # *** PRIVATE METHODS ***

    def _getValueFromRow(self, row:Tuple, indices:Union[int, List[int], Dict[str, int], None], concatenator:str, fallback:Any) -> Any:
        ret_val : Any
        if indices is not None:
            if isinstance(indices, int):
                # if there's a single index, use parse to get the value it is stated to be
                # print(f"About to parse value {row[indices]} as type {self.Columns[indices]},\nFull list from row is {row},\nFull list of columns is {self.Columns},\nwith names {self.ColumnNames}")
                ret_val = TableSchema._parse(input=row[indices], col_schema=self.Columns[indices])
            elif isinstance(indices, list):
                ret_val = concatenator.join([str(row[index]) for index in indices])
            elif isinstance(indices, dict):
                ret_val = {}
                for key,column_index in indices.items():
                    if column_index > len(row):
                        Logger.Log(f"Got column index of {column_index} for column {key}, but row only has {len(row)} columns!", logging.ERROR)
                    _val = TableSchema._parse(input=row[column_index], col_schema=self._columns[column_index])
                    ret_val.update(_val if isinstance(_val, dict) else {key:_val})
        else:
            ret_val = fallback
        return ret_val
