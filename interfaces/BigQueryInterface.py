import json
import logging
import os
from datetime import datetime, date
from google.cloud import bigquery
from typing import Dict, List, Tuple, Optional
# import locals
from interfaces.DataInterface import DataInterface
from schemas.IDMode import IDMode
from schemas.configs.GameSourceMapSchema import GameSourceSchema
from schemas.configs.data_sources.BigQuerySourceSchema import BigQuerySchema
from utils import Logger

AQUALAB_MIN_VERSION = 6.2

class BigQueryInterface(DataInterface):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:GameSourceSchema, fail_fast:bool):
        super().__init__(game_id=game_id, config=config, fail_fast=fail_fast)
        self.Open()

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _open(self, force_reopen: bool = False) -> bool:
        if force_reopen:
            self.Close()
            self.Open(force_reopen=False)
        if not self._is_open:
            if "GITHUB_ACTIONS" in os.environ:
                self._client = bigquery.Client()
            elif isinstance(self._config.Source, BigQuerySchema):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._config.Source.Credential or "NO CREDENTIAL CONFIGURED!" or f"./{self._game_id}.json"
                self._client = bigquery.Client()
            else:
                raise ValueError("No BigQuery credential available in current configuration!")
            if self._client != None:
                self._is_open = True
                Logger.Log("Connected to BigQuery database.", logging.DEBUG)
                return True
            else:
                Logger.Log("Could not connect to BigQuery Database.", logging.WARN)
                return False
        else:
            return True

    def _close(self) -> bool:
        self._client.close()
        self._is_open = False
        Logger.Log("Closed connection to BigQuery.", logging.DEBUG)
        return True

    def _allIDs(self) -> List[str]:
        query = f"""
            SELECT DISTINCT session_id
            FROM `{self.DBPath()}`,
        """
        Logger.Log(f"Running query for all ids:\n{query}", logging.DEBUG, depth=3)
        data = self._client.query(query)
        ids = [str(row['session_id']) for row in data]
        return ids if ids != None else []

    def _fullDateRange(self) -> Dict[str, datetime]:
        query = f"""
            SELECT MIN(server_time), MAX(server_time)
            FROM `{self.DBPath()}`
        """
        Logger.Log(f"Running query for full date range:\n{query}", logging.DEBUG, depth=3)
        data = list(self._client.query(query))
        return {'min':data[0][0], 'max':data[0][1]}

    def _rowsFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]] = None) -> List[Tuple]:
        # 2) Set up clauses to select based on Session ID or Player ID.
        events = None
        if self._client != None:
            query = self._generateRowFromIDQuery(id_list=id_list, id_mode=id_mode)
            Logger.Log(f"Running query for rows from IDs:\n{query}", logging.DEBUG, depth=3)
            data = self._client.query(query)
            events = []
            for row in data:
                items = tuple(row.items())
                event = []
                for item in items:
                    if item[0] == "event_params":
                        _params = {param['key']:param['value'] for param in item[1]}
                        event.append(json.dumps(_params, sort_keys=True))
                    elif item[0] in {"device", "geo"}:
                        event.append(json.dumps(item[1], sort_keys=True))
                    else:
                        event.append(item[1])
                events.append(tuple(event))
        return events if events != None else []

    def _generateRowFromIDQuery(self, id_list:List[str], id_mode:IDMode) -> str:
        id_clause : str = ""
        id_string = ','.join([f"'{x}'" for x in id_list])
        if id_mode == IDMode.SESSION:
            id_clause = f"session_id IN ({id_string})"
        elif id_mode == IDMode.USER:
            id_clause  = f"user_id IN ({id_string})"
        else:
            Logger.Log(f"Invalid ID mode given (name={id_mode.name}, val={id_mode.value}), defaulting to session mode.", logging.WARNING, depth=3)
            id_clause = f"session_id IN ({id_string})"
        # 3) Set up WHERE clause based on whether we need Aqualab min version or not.
        where_clause = f"""
            WHERE {id_clause}
        """
        # 4) Set up actual query
        # TODO Order by user_id, and by timestamp within that.
        # Note that this could prove to be wonky when we have more games without user ids,
        # will need to really rethink this when we start using new system.
        # Still, not a huge deal because most of these will be rewritten at that time anyway.
        query = f"""
            SELECT session_id, user_id, user_data, client_time, client_offset, server_time, event_name, event_data, event_source, game_state, app_version, app_branch, log_version, event_sequence_index
            FROM `{self.DBPath()}`
            {where_clause}
            ORDER BY `user_id`, `session_id`, `server_time` ASC
        """
        return query

    def _IDsFromDates(self, min:datetime, max:datetime, versions:Optional[List[int]] = None) -> List[str]:
        ret_val = []
        str_min, str_max = min.strftime("%Y%m%d"), max.strftime("%Y%m%d")
        query = f"""
            SELECT DISTINCT session_id
            FROM `{self.DBPath(min_date=min.date(), max_date=max.date())}`
            WHERE _TABLE_SUFFIX BETWEEN '{str_min}' AND '{str_max}'
        """
        Logger.Log(f"Running query for ids from dates:\n{query}", logging.DEBUG, depth=3)
        data = self._client.query(query)
        ids = [str(row['session_id']) for row in data]
        if ids is not None:
            ret_val = ids
        Logger.Log(f"Found {len(ret_val)} ids. {ret_val if len(ret_val) <= 5 else ''}", logging.DEBUG, depth=3)
        return ret_val

    def _datesFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]] = None) -> Dict[str, datetime]:
        if id_mode==IDMode.SESSION:
            id_string = ','.join([f"{x}" for x in id_list])
            where_clause = f"""
                WHERE session_id IN ({id_string})
            """
        elif id_mode==IDMode.USER:
            id_string = ','.join([f"'{x}'" for x in id_list])
            where_clause = f"""
                WHERE user_id IN ({id_string})
            """
        else:
            Logger.Log(f"Invalid ID mode given (name={id_mode.name}, val={id_mode.value}), defaulting to session mode.", logging.WARNING, depth=3)
            id_string = ','.join([f"{x}" for x in id_list])
            where_clause = f"""
                WHERE session_id IN ({id_string})
            """
        query = f"""
            SELECT MIN(server_time), MAX(server_time)
            FROM `{self.DBPath()}`
            {where_clause}
        """
        Logger.Log(f"Running query for dates from IDs:\n{query}", logging.DEBUG, depth=3)
        data = list(self._client.query(query))
        ret_val : Dict[str, datetime] = {}
        if len(data) == 1:
            dates = data[0]
            if len(dates) == 2 and dates[0] is not None and dates[1] is not None:
                ret_val = {'min':datetime.strptime(dates[0], "%m-%d-%Y %H:%M:%S"), 'max':datetime.strptime(dates[1], "%m-%d-%Y %H:%M:%S")}
            else:
                Logger.Log(f"BigQueryInterface query did not give both a min and a max, setting both to 'now'", logging.WARNING, depth=3)
                ret_val = {'min':datetime.now(), 'max':datetime.now()}
        else:
            Logger.Log(f"BigQueryInterface query did not return any results, setting both min and max to 'now'", logging.WARNING, depth=3)
            ret_val = {'min':datetime.now(), 'max':datetime.now()}
        return ret_val

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def IsOpen(self) -> bool:
        """Overridden version of IsOpen function, checks that BigQueryInterface client has been initialized.

        :return: True if the interface is open, else False
        :rtype: bool
        """
        return True if (super().IsOpen() and self._client is not None) else False

    def DBPath(self, min_date:Optional[date]=None, max_date:Optional[date]=None) -> str:
        """The path of form "[projectID].[datasetID].[tableName]" used to make queries

        :return: The full path from project ID to table name, if properly set in configuration, else the literal string "INVALID SOURCE SCHEMA".
        :rtype: str
        """
        if isinstance(self._config.Source, BigQuerySchema):
            # _current_date = datetime.now().date()
            date_wildcard = "*"
            # if min_date is not None and max_date is not None:
            #     date_wildcard = BigQueryInterface._datesWildcard(a=min_date, b=max_date)
            # elif min_date is not None:
            #     date_wildcard = BigQueryInterface._datesWildcard(a=min_date, b=_current_date)
            # elif max_date is not None:
            #     date_wildcard = BigQueryInterface._datesWildcard(a=_current_date, b=max_date)
            return f"{self._config.Source.AsConnectionInfo}.{self._config.TableName}_{date_wildcard}"
        else:
            return "INVALID SOURCE SCHEMA"

    # *** PRIVATE STATICS ***

    @staticmethod
    def _datesWildcard(a:date, b:date) -> str:
        ret_val = "*"
        if a.year == b.year:
            ret_val = str(a.year).rjust(4, "0")
            if a.month == b.month:
                ret_val += str(a.month).rjust(2, "0")
                if a.day == b.day:
                    ret_val += str(a.day).rjust(2, "0")
                else:
                    ret_val += "*"
            else:
                ret_val += "*"
        else:
            ret_val = "*"
        return ret_val

    # *** PRIVATE METHODS ***
