## import standard libraries
import json
import logging
import typing
## import local files
import GameTable
from schemas.Schema import Schema

""" Class to manage data for a raw csv file. """
class RawManager:
    def __init__(self, game_table: GameTable, game_schema: Schema,
                 raw_csv_file: typing.IO.writable):
        ## define instance vars
        self._lines:              typing.List[typing.List]
        self._game_table:         GameTable
        self._db_columns:         typing.List[str]
        self._JSON_columns:       typing.List[str]
        self._all_columns:        typing.List[str]
        self._columns_to_indices: typing.Dict
        self._raw_file          : typing.IO.writable
        ## set instance vars
        self._lines = []
        self._game_table = game_table
        self._db_columns = game_schema.db_columns()
        self._JSON_columns = RawManager._generateJSONColumns(game_schema)
        self._all_columns = game_table.column_names[:game_table.complex_data_index] + self._JSON_columns + game_table.column_names[game_table.complex_data_index+1:]
        ## Not the nicest thing ever, but this function creates a dictionary that maps column names
        ## to indices, so we can store each line for raw csv as a list with guaranteed consistent order.
        self._columns_to_indices = {name:index for index,name in enumerate(self._all_columns)}
        self._raw_file = raw_csv_file

    def ProcessRow(self, row_with_complex_parsed: typing.Tuple):
        line = [None] * len(self._all_columns)
        for i,col in enumerate(row_with_complex_parsed):
            # So, I'm only using columns_to_indices for the JSON stuff,
            # since the other stuff comes in tuples, which have a consistent order.
            # A little inconsistent, but... whatever.
            # I don't know of a good way to get column names with the row data.
            if i < self._game_table.complex_data_index:
                line[i] = f"\"{col}\"" if type(col) == str else col
            elif i > self._game_table.complex_data_index:
                index = i + len(self._JSON_columns) - 1
                line[index] = f"\"{col}\"" if type(col) == str else col
            else: # must be at complex_data_index
                complex_data_parsed = row_with_complex_parsed[self._game_table.complex_data_index]
                for key in complex_data_parsed.keys():
                    index = self._columns_to_indices[key]
                    item = complex_data_parsed[key]
                    line[index] = f"\"{str(item)}\"" if (type(item) == type({}) or type(item) == str) \
                             else item
        self._lines.append(",".join([str(item) for item in line]) + "\n")

    """ Empty the list of lines stored by the RawManager.
        This is helpful if we're processing a lot of data and want to avoid
        Eating too much memory. """
    def ClearLines(self):
        logging.debug(f"Clearing {len(self._lines)} entries from RawManager.")
        self._lines = []

    def WriteRawCSVHeader(self):
        self._raw_file.write(",".join(self._all_columns) + "\n")

    def WriteRawCSVLines(self):
        for line in self._lines:
            self._raw_file.write(line)

    @staticmethod
    def _generateJSONColumns(game_schema: Schema):
        JSON_columns = []
        for event_type in game_schema.event_types():
            JSON_columns.extend([col for col in game_schema.events()[event_type].keys() if col not in JSON_columns])
        return JSON_columns