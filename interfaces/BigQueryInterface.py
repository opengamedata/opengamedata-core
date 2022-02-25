import json
import logging
import os
from datetime import datetime
from google.cloud import bigquery
from typing import Dict, List, Tuple, Union
# local imports
from config.config import settings as default_settings
from interfaces.DataInterface import DataInterface
from utils import Logger

class BigQueryInterface(DataInterface):

    def __init__(self, game_id: str, settings):
        super().__init__(game_id=game_id)
        self._settings = settings
        self.Open()

    def _open(self, force_reopen: bool = False) -> bool:
        if force_reopen:
            self.Close()
            self.Open(force_reopen=False)
        if not self._is_open:
            if "GITHUB_ACTIONS" in os.environ:
                self._client = bigquery.Client()
            else:
                credential_path : str
                if "GAME_SOURCE_MAP" in self._settings:
                    credential_path = self._settings["GAME_SOURCE_MAP"][self._game_id]["credential"]
                else:
                    credential_path = default_settings["GAME_SOURCE_MAP"][self._game_id]["credential"]
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
                self._client = bigquery.Client()
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
        Logger.toStdOut("Closed connection to BigQuery.", logging.DEBUG)
        return True

    def _rowsFromIDs(self, id_list:List[str], versions:Union[List[int],None] = None) -> List[Tuple]:
        if self._client != None:
            db_name    : str
            table_name : str
            if "BIGQUERY_CONFIG" in self._settings:
                db_name = self._settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = self._settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            else:
                db_name = default_settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = default_settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            id_string = ','.join([f"{x}" for x in id_list])
            if self._game_id == "AQUALAB":
                # TODO: Temporary fix for 6.1 playtest
                query = f"""
                    SELECT event_name, event_params, user_id, device, geo, platform,
                        (SELECT value.int_value FROM UNNEST(event_params) WHERE (key = "ga_session_id" AND value.int_value IN ({id_string}))) AS session_id,
                    concat(FORMAT_DATE('%Y-%m-%d', PARSE_DATE('%Y%m%d', event_date)), FORMAT_TIME('T%H:%M:%S.00', TIME(TIMESTAMP_MICROS(event_timestamp)))) AS timestamp,
                    FROM `{db_name}.{table_name}`,
                    UNNEST(event_params) AS param
                    WHERE (param.key = "page_location" AND param.value.string_value = "https://fielddaylab.wisc.edu/play/aqualab/ci/milestone6.1/")
                    ORDER BY `session_id`, `timestamp` ASC
                """
            else:
                query = f"""
                    SELECT event_name, event_params, user_id, device, geo, platform, param.value.int_value AS session_id,
                    concat(FORMAT_DATE('%Y-%m-%d', PARSE_DATE('%Y%m%d', event_date)), FORMAT_TIME('T%H:%M:%S.00', TIME(TIMESTAMP_MICROS(event_timestamp)))) AS timestamp,
                    FROM `{db_name}.{table_name}`,
                    UNNEST(event_params) AS param
                    WHERE param.key = "ga_session_id"
                    AND param.value.int_value IN ({id_string})
                    ORDER BY `session_id`, `timestamp` ASC
                """
            data = self._client.query(query)
            events = []
            for row in data:
                items = tuple(row.items())
                event = []
                for item in items:
                    if item[0] == "event_params":
                        _params = {param['key']:param['value'] for param in item[1]}
                        event.append(json.dumps(_params, sort_keys=True))
                    elif item[0] in ["device", "geo"]:
                        event.append(json.dumps(item[1], sort_keys=True))
                    else:
                        event.append(item[1])
                events.append(tuple(event))
            return events if events != None else []
        else:
            Logger.Log(f"Could not get data for {len(id_list)} sessions, BigQuery connection is not open.", logging.WARN)
            return []

    def _allIDs(self) -> List[str]:
        if self._client != None:
            db_name    : str
            table_name : str
            if "BIGQUERY_CONFIG" in self._settings:
                db_name = self._settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = self._settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            else:
                db_name = default_settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = default_settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            query = f"""
                SELECT DISTINCT param.value.int_value AS session_id
                FROM `{db_name}.{table_name}`,
                UNNEST(event_params) AS param
                WHERE param.key = "ga_session_id"
            """
            data = self._client.query(query)
            ids = [str(row['session_id']) for row in data]
            return ids if ids != None else []
        else:
            Logger.Log(f"Could not get list of all session ids, BigQuery connection is not open.", logging.WARN)
            return []

    def _fullDateRange(self) -> Dict[str, datetime]:
        if self._client != None:
            db_name    : str
            table_name : str
            if "BIGQUERY_CONFIG" in self._settings:
                db_name = self._settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = self._settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            else:
                db_name = default_settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = default_settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            query = f"""
                WITH datetable AS
                (
                    SELECT event_date, event_timestamp,
                    FORMAT_DATE('%m-%d-%Y', PARSE_DATE('%Y%m%d', event_date)) AS date, 
                    FORMAT_TIME('%T', TIME(TIMESTAMP_MICROS(event_timestamp))) AS time,
                    FROM `{db_name}.{table_name}`
                )
                SELECT MIN(concat(date, ' ', time)), MAX(concat(date, ' ', time))
                FROM datetable
            """
            data = list(self._client.query(query))
            return {'min':data[0][0], 'max':data[0][1]}
        else:
            Logger.Log(f"Could not get full date range, BigQuery connection is not open.", logging.WARN)
            return {"min":datetime.now(), "max":datetime.now()}

    def _IDsFromDates(self, min:datetime, max:datetime, versions:Union[List[int],None] = None) -> List[str]:
        ret_val = []
        str_min, str_max = min.strftime("%Y%m%d"), max.strftime("%Y%m%d")
        if self._client != None:
            db_name    : str
            table_name : str
            if "BIGQUERY_CONFIG" in self._settings:
                db_name = self._settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = self._settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            else:
                db_name = default_settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = default_settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            query = f"""
                SELECT DISTINCT param.value.int_value AS session_id
                FROM `{db_name}.{table_name}`,
                UNNEST(event_params) AS param
                WHERE param.key = "ga_session_id"
                AND _TABLE_SUFFIX BETWEEN '{str_min}' AND '{str_max}'
            """
            data = self._client.query(query)
            ids = [str(row['session_id']) for row in data]
            if ids is not None:
                ret_val = ids
        else:
            Logger.Log(f"Could not get session list for {str_min}-{str_max} range, BigQuery connection is not open.", logging.WARN)
        return ret_val

    def _datesFromIDs(self, id_list:List[str], versions:Union[List[int],None] = None) -> Dict[str, datetime]:
        if self._client != None:
            db_name    : str
            table_name : str
            if "BIGQUERY_CONFIG" in self._settings:
                db_name = self._settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = self._settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            else:
                db_name = default_settings["BIGQUERY_CONFIG"][self._game_id]["DB_NAME"]
                table_name = default_settings["BIGQUERY_CONFIG"]["TABLE_NAME"]
            id_string = ','.join([f"'{x}'" for x in id_list])
            query = f"""
                WITH datetable AS
                (
                    SELECT event_date, event_timestamp, event_params,
                    FORMAT_DATE('%m-%d-%Y', PARSE_DATE('%Y%m%d', event_date)) AS date, 
                    FORMAT_TIME('%T', TIME(TIMESTAMP_MICROS(event_timestamp))) AS time,
                    FROM `{db_name}.{table_name}`
                )
                SELECT MIN(concat(date, ' ', time)), MAX(concat(date, ' ', time))
                FROM datetable,
                UNNEST(event_params) AS param
                WHERE param.key = "ga_session_id"
                AND param.value.int_value IN ({id_string})
            """
            data = list(self._client.query(query))
            return {'min':data[0][0], 'max':data[0][1]}
        else:
            Logger.Log(f"Could not get date range for {len(id_list)} sessions, BigQuery connection is not open.", logging.WARN)
            return {'min':datetime.now(), 'max':datetime.now()}
