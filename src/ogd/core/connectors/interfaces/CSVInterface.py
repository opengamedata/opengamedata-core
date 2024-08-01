import logging
import pandas as pd
from datetime import datetime
from pandas.io.parsers import TextFileReader
from pathlib import Path
from typing import Any, Dict, IO, List, Tuple, Optional
## import local files
from ogd.core.connectors.interfaces.EventInterface import EventInterface
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.schemas.tables.TableSchema import TableSchema
from ogd.core.utils.Logger import Logger

class CSVInterface(EventInterface):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:GameSourceSchema, fail_fast:bool, filepath:Path, delim:str = ','):
        # set up data from params
        self._filepath  : Path = filepath
        self._delimiter : str = delim
        super().__init__(game_id=game_id, config=config, fail_fast=fail_fast)
        # set up data from file
        self._data      : pd.DataFrame = pd.DataFrame()
        self.Open()

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _open(self) -> bool:
        try:
            # TODO should include option for access to the TableSchema in the interface, because obviously it should know what form the table takes.
            target_types = { 'session_id' : 'str' }
            _data = pd.read_csv(filepath_or_buffer=self._filepath, delimiter=self._delimiter, dtype=target_types, parse_dates=['timestamp'])
            # _data = pd.read_csv(filepath_or_buffer=self._filepath, delimiter=self._delimiter)
            Logger.Log(f"Loaded from CSV, columns are: {_data.dtypes}", logging.INFO)
            Logger.Log(f"First few rows are:\n{_data.head(n=3)}")
            self._data = _data.where(_data.notnull(), None)
            self._is_open = True
            return True
        except FileNotFoundError as err:
            Logger.Log(f"Could not find file {self._filepath}.", logging.ERROR)
            return False

    def _close(self) -> bool:
        self._is_open = False
        self._data = pd.DataFrame() # make new dataframe, let old data get garbage collected I assume.
        return True

    def _allIDs(self) -> List[str]:
        return [str(id) for id in self._data['session_id'].unique().tolist()]

    def _fullDateRange(self) -> Dict[str,datetime]:
        min_time = pd.to_datetime(self._data['timestamp'].min())
        max_time = pd.to_datetime(self._data['timestamp'].max())
        return {'min':min_time, 'max':max_time}

    def _rowsFromIDs(self, id_list: List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]]=None, exclude_rows:Optional[List[str]]=None) -> List[Tuple]:
        ret_val : List[Tuple] = []
        if self.IsOpen and not self._data.empty:
            _data : pd.DataFrame
            if id_mode == IDMode.SESSION:
                _data = self._data.loc[self._data['session_id'].isin(id_list)]
            elif id_mode == IDMode.USER:
                _data = self._data.loc[self._data['user_id'].isin(id_list)]
            else:
                _data = self._data.loc[self._data['session_id'].isin(id_list)]
            if exclude_rows is not None:
                _mask = _data['event_name'].isin(exclude_rows)
                _data = _data[~_mask]
            ret_val = list(_data.itertuples(index=False, name=None))
        return ret_val

    def _IDsFromDates(self, min:datetime, max:datetime) -> List[str]:
        if not self._data.empty:
            server_times = pd.to_datetime(self._data['server_time'])
            mask = (server_times >= pd.to_datetime(min)) & (server_times <= pd.to_datetime(max))
            data_masked = self._data.loc[mask]
            return data_masked['session_id'].unique().tolist()
        else:
            return []

    def _datesFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION) -> Dict[str, datetime]:
        if id_mode == IDMode.SESSION:
            min_date = self._data[self._data['session_id'].isin(id_list)]['timestamp'].min()
            max_date = self._data[self._data['session_id'].isin(id_list)]['timestamp'].max()
        elif id_mode == IDMode.USER:
            min_date = self._data[self._data['user_id'].isin(id_list)]['timestamp'].min()
            max_date = self._data[self._data['user_id'].isin(id_list)]['timestamp'].max()
        else:
            min_date = self._data[self._data['session_id'].isin(id_list)]['timestamp'].min()
            max_date = self._data[self._data['session_id'].isin(id_list)]['timestamp'].max()
        return {'min':pd.to_datetime(min_date), 'max':pd.to_datetime(max_date)}

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
