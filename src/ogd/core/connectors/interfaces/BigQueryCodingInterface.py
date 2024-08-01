import json
import logging
import os
from datetime import datetime
from google.cloud import bigquery
from typing import Dict, List, Tuple, Optional
# import locals
from coding.Code import Code
from coding.Coder import Coder
from ogd.core.connectors.interfaces.CodingInterface import CodingInterface
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.schemas.configs.ConfigSchema import ConfigSchema
from ogd.core.utils.Logger import Logger

# TODO: see about merging this back into BigQueryInterface for a unified interface.

class BigQueryCodingInterface(CodingInterface):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:ConfigSchema):
        super().__init__()
        self._game_id : str = game_id
        self._settings = config
        self.Open()

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

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
        Logger.Log("Closed connection to BigQuery.", logging.DEBUG)
        return True

    def _allCoders(self) -> Optional[List[Coder]]:
        query = f"""
            SELECT DISTINCT coder_id, name
            FROM `{self._dbPath()}.coders`
        """
        data = self._client.query(query)
        coders = [Coder(name=str(row['name']), id=str(row['coder_id'])) for row in data]
        return coders or []

    def _createCoder(self, coder_name:str) -> bool:
        # TODO: figure out how to make metadata available for insert.
        query = f"""
            INSERT {self._dbPath()}(coder_id, name, metadata)
            VALUES (GENERATE_UUID(), @name, NULL)
        """
        cfg = bigquery.QueryJobConfig(
            query_parameters= [
                bigquery.ScalarQueryParameter(name="name", type_="STRING", value=coder_name),
            ]
        )
        try:
            self._client.query(query=query, job_config=cfg)
        except Exception as err:
            Logger.Log(f"Error while creating a new Coder in database: {err}", level=logging.ERROR, depth=2)
            return False
        else:
            return True

    def _getCodeWordsByGame(self, game_id:str) -> Optional[List[str]]:
        query = f"""
            SELECT DISTINCT code
            FROM `{self._dbPath(game_id=game_id)}.codes`
        """
        data = self._client.query(query)
        codes = [str(row['code']) for row in data]
        return codes or []

    def _getCodeWordsByCoder(self, coder_id:str) -> Optional[List[str]]:
        query = f"""
            SELECT DISTINCT code
            FROM `{self._dbPath()}.codes`
            WHERE coder_id=@coder_id
        """
        cfg = bigquery.QueryJobConfig(
            query_parameters= [
                bigquery.ScalarQueryParameter(name="coder_id", type_="STRING", value=coder_id),
            ]
        )
        data = self._client.query(query=query, job_config=cfg)
        codes = [str(row['code']) for row in data]
        return codes or []

    def _getCodeWordsBySession(self, session_id:str) -> Optional[List[str]]:
        query = f"""
            SELECT DISTINCT code
            FROM `{self._dbPath()}.codes`
            CROSS JOIN UNNEST(event_params) AS param_session
            WHERE param_session.key = 'ga_session_id' AND param_session.value.int_value=@session_id)
        """
        i_session_id : int = int(session_id)
        cfg = bigquery.QueryJobConfig(
            query_parameters= [
                bigquery.ScalarQueryParameter(name="session_id", type_="INTEGER", value=i_session_id),
            ]
        )
        data = self._client.query(query=query, job_config=cfg)
        codes = [str(row['code']) for row in data]
        return codes or []

    def _getCodesByGame(self, game_id:str) -> Optional[List[Code]]:
        query = f"""
            SELECT *
            FROM `{self._dbPath(game_id=game_id)}.codes`,
        """
        try:
            data = self._client.query(query)
            codes = [BigQueryCodingInterface._codeFromRow(row=row) for row in data]
        except Exception as err:
            Logger.Log(f"Error while retrieving {game_id} codes from database: {err}", level=logging.ERROR, depth=2)
            return []
        else:
            return codes

    def _getCodesByCoder(self, coder_id:str) -> Optional[List[Code]]:
        query = f"""
            SELECT *
            FROM `{self._dbPath()}.codes`
            WHERE `coder_id`=@coder_id
        """
        cfg = bigquery.QueryJobConfig(
            query_parameters= [
                bigquery.ScalarQueryParameter(name="coder_id", type_="STRING", value=coder_id),
            ]
        )
        try:
            data = self._client.query(query)
            codes = [BigQueryCodingInterface._codeFromRow(row=row) for row in data]
        except Exception as err:
            Logger.Log(f"Error while retrieving {coder_id} codes from database: {err}", level=logging.ERROR, depth=2)
            return []
        else:
            return codes

    def _getCodesBySession(self, session_id:str) -> Optional[List[Code]]:
        query = f"""
            SELECT *
            FROM `{self._dbPath()}.codes`
            CROSS JOIN UNNEST(events) AS param_session
            WHERE param_session.key = 'session_id' AND param_session.value.int_value=@session_id
        """
        cfg = bigquery.QueryJobConfig(
            query_parameters= [
                bigquery.ScalarQueryParameter(name="session_id", type_="STRING", value=session_id),
            ]
        )
        try:
            data = self._client.query(query)
            codes = [BigQueryCodingInterface._codeFromRow(row=row) for row in data]
        except Exception as err:
            Logger.Log(f"Error while retrieving {session_id} codes from database: {err}", level=logging.ERROR, depth=2)
            return []
        else:
            return codes

    def _createCode(self, code:str, coder_id:str, events:List[Code.EventID], notes:Optional[str]=None):
        query = f"""
            INSERT {self._dbPath()}(code_id, code, coder_id, notes, events)
            VALUES (GENERATE_UUID(), @code, @coder_id, @notes, @events)
        """
        evt_params = [
            bigquery.StructQueryParameter.positional(
                bigquery.ScalarQueryParameter(name="session_id", type_="STRING", value=event.SessionID),
                bigquery.ScalarQueryParameter(name="index", type_="INTEGER", value=event.Index)
            )
            for event in events
        ]
        cfg = bigquery.QueryJobConfig(
            query_parameters= [
                bigquery.ScalarQueryParameter(name="code", type_="STRING", value=code),
                bigquery.ScalarQueryParameter(name="coder_id", type_="STRING", value=coder_id),
                bigquery.ScalarQueryParameter(name="notes", type_="STRING", value=notes),
                bigquery.ArrayQueryParameter(
                    name="events",
                    array_type="STRUCT",
                    values=evt_params
                ),
            ]
        )
        try:
            self._client.query(query=query, job_config=cfg)
        except Exception as err:
            Logger.Log(f"Error while creating a new Coder in database: {err}", level=logging.ERROR, depth=2)
            return False
        else:
            return True

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def IsOpen(self) -> bool:
        """Overridden version of IsOpen function, checks that BigQueryInterface client has been initialized.

        :return: True if the interface is open, else False
        :rtype: bool
        """
        return True if (super().IsOpen() and self._client is not None) else False

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    @staticmethod
    def _codeFromRow(row) -> Code:
        _code_word = str(row['code'])
        _code_id   = str(row['code_id'])
        _coder_id  = str(row['coder_id'])
        _name      = str(row['coder_name'])
        _events    = [] # TODO: figure out how to parse these out.
        _notes     = str(row['notes'])
        return Code(code_word=_code_word, id=_code_id,
                    coder=Coder(name=_name, id=_coder_id),
                    events=_events, notes=_notes
        )

    # *** PRIVATE METHODS ***

    def _dbPath(self, game_id:Optional[str]=None) -> str:
        _game_id = game_id or self._game_id
        if "BIGQUERY_CONFIG" in self._settings:
            project_name = self._settings["BIGQUERY_CONFIG"][_game_id]["PROJECT_ID"]
        else:
            project_name = default_settings["BIGQUERY_CONFIG"][_game_id]["PROJECT_ID"]
        return f"{project_name}.coding"
