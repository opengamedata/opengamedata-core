# import libraries
from mysql.connector import connection, cursor
import logging
import sshtunnel
import traceback
from datetime import datetime
from typing import Dict, Final, List, Tuple, Optional
# import locals
from ogd.core.connectors.interfaces.EventInterface import EventInterface
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.schemas.configs.data_sources.MySQLSourceSchema import MySQLSchema
from ogd.core.utils.Logger import Logger


## @class SQL
#  A utility class containing some functions to assist in retrieving from a database.
#  Specifically, helps to connect to a database, make selections, and provides
#  a nicely formatted 500 error message.
class SQL:

    # Function to set up a connection to a database, via an ssh tunnel if available.
    @staticmethod
    def ConnectDB(schema:GameSourceSchema) -> Tuple[Optional[sshtunnel.SSHTunnelForwarder], Optional[connection.MySQLConnection]]:
        """
        Function to set up a connection to a database, via an ssh tunnel if available.

        :param db_settings: A dictionary mapping names of database parameters to values.
        :type db_settings: Dict[str,Any]
        :param ssh_settings: A dictionary mapping names of ssh parameters to values, or None if no ssh connection is desired., defaults to None
        :type ssh_settings: Optional[Dict[str,Any]], optional
        :return: A tuple consisting of the tunnel and database connection, respectively.
        :rtype: Tuple[Optional[sshtunnel.SSHTunnelForwarder], Optional[connection.MySQLConnection]]
        """
        ret_val : Tuple[Optional[sshtunnel.SSHTunnelForwarder], Optional[connection.MySQLConnection]] = (None, None)

        tunnel  : Optional[sshtunnel.SSHTunnelForwarder] = None
        db_conn : Optional[connection.MySQLConnection]   = None
        # Logger.Log("Preparing database connection...", logging.INFO)
        if schema.Source is not None and isinstance(schema.Source, MySQLSchema):
            if schema.Source.HasSSH:
                Logger.Log(f"Preparing to connect to MySQL via SSH, on host {schema.Source.SSH.Host}", level=logging.DEBUG)
                if (schema.Source.SSH.Host != "" and schema.Source.SSH.User != "" and schema.Source.SSH.Pass != ""):
                    tunnel,db_conn = SQL._connectToMySQLviaSSH(sql=schema.Source, db=schema.DatabaseName)
                else:
                    Logger.Log(f"SSH login had empty data, preparing to connect to MySQL directly instead, on host {schema.Source.DBHost}", level=logging.DEBUG)
                    db_conn = SQL._connectToMySQL(login=schema.Source, db=schema.DatabaseName)
                    tunnel = None
            else:
                Logger.Log(f"Preparing to connect to MySQL directly, on host {schema.Source.DBHost}", level=logging.DEBUG)
                db_conn = SQL._connectToMySQL(login=schema.Source, db=schema.DatabaseName)
                tunnel = None
            # Logger.Log("Done preparing database connection.", logging.INFO)
            ret_val = (tunnel, db_conn)
        else:
            Logger.Log(f"Unable to connect to MySQL, game source schema does not have a valid MySQL config!", level=logging.ERROR)

        return ret_val

    # Function to help connect to a mySQL server.
    @staticmethod
    def _connectToMySQL(login:MySQLSchema, db:str) -> Optional[connection.MySQLConnection]:
        """Function to help connect to a mySQL server.

        Simply tries to make a connection, and prints an error in case of failure.
        :param login: A SQLLogin object with the data needed to log into MySQL.
        :type login: SQLLogin
        :return: If successful, a MySQLConnection object, otherwise None.
        :rtype: Optional[connection.MySQLConnection]
        """
        try:
            Logger.Log(f"Connecting to SQL (no SSH) at {login.AsConnectionInfo}...", logging.DEBUG)
            db_conn = connection.MySQLConnection(host     = login.DBHost,    port    = login.DBPort,
                                                 user     = login.DBUser,    password= login.DBPass,
                                                 database = db, charset = 'utf8')
            Logger.Log(f"Connected.", logging.DEBUG)
            return db_conn
        #except MySQLdb.connections.Error as err:
        except Exception as err:
            msg = f"""Could not connect to the MySql database.
            Login info: {login.AsConnectionInfo} w/port type={type(login.DBPort)}.
            Full error: {type(err)} {str(err)}"""
            Logger.Log(msg, logging.ERROR)
            traceback.print_tb(err.__traceback__)
            return None

    ## Function to help connect to a mySQL server over SSH.
    @staticmethod
    def _connectToMySQLviaSSH(sql:MySQLSchema, db:str) -> Tuple[Optional[sshtunnel.SSHTunnelForwarder], Optional[connection.MySQLConnection]]:
        """Function to help connect to a mySQL server over SSH.

        Simply tries to make a connection, and prints an error in case of failure.
        :param sql: A SQLLogin object with the data needed to log into MySQL.
        :type sql: SQLLogin
        :param ssh: An SSHLogin object with the data needed to log into MySQL.
        :type ssh: SSHLogin
        :return: An open connection to the database if successful, otherwise None.
        :rtype: Tuple[Optional[sshtunnel.SSHTunnelForwarder], Optional[connection.MySQLConnection]]
        """
        tunnel    : Optional[sshtunnel.SSHTunnelForwarder] = None
        db_conn   : Optional[connection.MySQLConnection] = None
        MAX_TRIES : Final[int] = 5
        tries : int = 0
        connected_ssh : bool = False

        # First, connect to SSH
        while connected_ssh == False and tries < MAX_TRIES:
            if tries > 0:
                Logger.Log("Re-attempting to connect to SSH.", logging.INFO)
            try:
                Logger.Log(f"Connecting to SSH at {sql.SSHConfig.AsConnectionInfo}...", logging.DEBUG)
                tunnel = sshtunnel.SSHTunnelForwarder(
                    (sql.SSH.Host, sql.SSH.Port), ssh_username=sql.SSH.User, ssh_password=sql.SSH.Pass,
                    remote_bind_address=(sql.DBHost, sql.DBPort), logger=Logger.std_logger
                )
                tunnel.start()
                connected_ssh = True
                Logger.Log(f"Connected.", logging.DEBUG)
            except Exception as err:
                msg = f"Could not connect via SSH: {type(err)} {str(err)}"
                Logger.Log(msg, logging.ERROR)
                Logger.Print(msg, logging.ERROR)
                traceback.print_tb(err.__traceback__)
                tries = tries + 1
        if connected_ssh == True and tunnel is not None:
            # Then, connect to MySQL
            try:
                Logger.Log(f"Connecting to SQL (via SSH) at {sql.DBUser}@{sql.DBHost}:{tunnel.local_bind_port}/{db}...", logging.DEBUG)
                db_conn = connection.MySQLConnection(host     = sql.DBHost,    port    = tunnel.local_bind_port,
                                                     user     = sql.DBUser,    password= sql.DBPass,
                                                     database = db, charset ='utf8')
                Logger.Log(f"Connected", logging.DEBUG)
                return (tunnel, db_conn)
            except Exception as err:
                msg = f"Could not connect to the MySql database: {type(err)} {str(err)}"
                Logger.Log(msg, logging.ERROR)
                Logger.Print(msg, logging.ERROR)
                traceback.print_tb(err.__traceback__)
                if tunnel is not None:
                    tunnel.stop()
                return (None, None)
        else:
            return (None, None)

    @staticmethod
    def disconnectMySQL(db:Optional[connection.MySQLConnection], tunnel:Optional[sshtunnel.SSHTunnelForwarder]=None) -> None:
        if db is not None:
            db.close()
            Logger.Log("Closed MySQL database connection", logging.DEBUG)
        else:
            Logger.Log("No MySQL database to close.", logging.DEBUG)
        if tunnel is not None:
            tunnel.stop()
            Logger.Log("Stopped MySQL tunnel connection", logging.DEBUG)
        else:
            Logger.Log("No MySQL tunnel to stop", logging.DEBUG)

    # Function to build and execute SELECT statements on a database connection.
    @staticmethod
    def SELECT(cursor        :cursor.MySQLCursor,          db_name        : str,                   table    : str,
               columns       :List[str]           = [],    filter         : Optional[str] = None,
               sort_columns  :Optional[List[str]] = None,  sort_direction : str           = "ASC", grouping : Optional[str] = None,
               distinct      :bool                = False, offset         : int           = 0,     limit    : int           = -1,
               fetch_results :bool                = True,  params         : Tuple[str]    = tuple()) -> Optional[List[Tuple]]:
        """Function to build and execute SELECT statements on a database connection.

        :param cursor: A database cursor, retrieved from the active connection.
        :type cursor: cursor.MySQLCursor
        :param db_name: The name of the database to which we are connected.
        :type db_name: str
        :param table: The name of the table from which we want to make a selection.
        :type table: str
        :param columns: A list of columns to be selected. If empty (or None), all columns will be used (SELECT * FROM ...). Defaults to None
        :type columns: List[str], optional
        :param filter: A string giving the constraints for a WHERE clause (The "WHERE" term itself should not be part of the filter string), defaults to None
        :type filter: str, optional
        :param sort_columns: A list of columns to sort results on. The order of columns in the list is the order given to SQL. Defaults to None
        :type sort_columns: List[str], optional
        :param sort_direction: The "direction" of sorting, either ascending or descending., defaults to "ASC"
        :type sort_direction: str, optional
        :param grouping: A column name to group results on. Subject to SQL rules for grouping, defaults to None
        :type grouping: str, optional
        :param distinct: A bool to determine whether to select only rows with distinct values in the column, defaults to False
        :type distinct: bool, optional
        :param limit: The maximum number of rows to be selected. Use -1 for no limit., defaults to -1
        :type limit: int, optional
        :param fetch_results: A bool to determine whether all results should be fetched and returned, defaults to True
        :type fetch_results: bool, optional
        :return: A collection of all rows from the selection, if fetch_results is true, otherwise None.
        :rtype: Optional[List[Tuple]]
        """
        d          = "DISTINCT" if distinct else ""
        cols       = ",".join([f"{col}" for col in columns]) if len(columns) > 0 else "*"
        sort_cols  = ",".join([f"`{col}`" for col in sort_columns]) if sort_columns is not None and len(sort_columns) > 0 else None
        table_path = db_name + "." + str(table)

        sel_clause = f"SELECT {d} {cols} FROM {table_path}"
        where_clause = "" if filter    is None else f"WHERE {filter}"
        group_clause = "" if grouping  is None else f"GROUP BY {grouping}"
        sort_clause  = "" if sort_cols is None else f"ORDER BY {sort_cols} {sort_direction}"
        lim_clause   = "" if limit < 0         else f"LIMIT {str(max(offset, 0))}, {str(limit)}" # don't use a negative for offset
        query = f"{sel_clause} {where_clause} {group_clause} {sort_clause} {lim_clause};"
        return SQL.Query(cursor=cursor, query=query, params=params, fetch_results=fetch_results)

    @staticmethod
    def Query(cursor:cursor.MySQLCursor, query:str, params:Optional[Tuple], fetch_results: bool = True) -> Optional[List[Tuple]]:
        result : Optional[List[Tuple]] = None
        # first, we do the query.
        Logger.Log(f"Running query: {query}\nWith params: {params}", logging.DEBUG, depth=3)
        start = datetime.now()
        cursor.execute(query, params)
        time_delta = datetime.now()-start
        Logger.Log(f"Query execution completed, time to execute: {time_delta}", logging.DEBUG)
        # second, we get the results.
        if fetch_results:
            result = cursor.fetchall()
            time_delta = datetime.now()-start
            Logger.Log(f"Query fetch completed, total query time:    {time_delta} to get {len(result) if result is not None else 0:d} rows", logging.DEBUG)
        return result

class MySQLInterface(EventInterface):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:GameSourceSchema, fail_fast:bool):
        self._tunnel    : Optional[sshtunnel.SSHTunnelForwarder] = None
        self._db        : Optional[connection.MySQLConnection] = None
        self._db_cursor : Optional[cursor.MySQLCursor] = None
        super().__init__(game_id=game_id, config=config, fail_fast=fail_fast)
        self.Open()

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    def _open(self, force_reopen:bool = False) -> bool:
        if force_reopen:
            self.Close()
            self.Open(force_reopen=False)
        if not self._is_open:
            start = datetime.now()
            if isinstance(self._config.Source, MySQLSchema):
                self._tunnel, self._db = SQL.ConnectDB(schema=self._config)
                if self._db is not None:
                    self._db_cursor = self._getCursor()
                    self._is_open = True
                    time_delta = datetime.now() - start
                    Logger.Log(f"Database Connection Time: {time_delta}", logging.INFO)
                    return True
                else:
                    Logger.Log(f"Unable to open MySQL interface.", logging.ERROR)
                    SQL.disconnectMySQL(tunnel=self._tunnel, db=self._db)
                    return False
            else:
                Logger.Log(f"Unable to open MySQL interface, the schema has invalid type {type(self._config)}", logging.ERROR)
                SQL.disconnectMySQL(tunnel=self._tunnel, db=self._db)
                return False
        else:
            return True

    def _close(self) -> bool:
        SQL.disconnectMySQL(tunnel=self._tunnel, db=self._db)
        Logger.Log("Closed connection to MySQL.", logging.DEBUG)
        self._is_open = False
        return True

    def _availableIDs(self) -> List[str]:
        if self._db_cursor is not None and isinstance(self._config.Source, MySQLSchema):
            _db_name     : str = self._config.DatabaseName
            _table_name  : str = self._config.TableName

            sess_id_col  : str = self._TableSchema.SessionIDColumn or "session_id"

            filters : List[str] = []
            params  : List[str] = []
            if _table_name != self._game_id:
                filters.append(f"`app_id`=%s")
                params.append(self._game_id)
            filter_clause = " AND ".join(filters)
            
            data = SQL.SELECT(cursor =self._db_cursor, db_name=_db_name,      table   =_table_name,
                              columns=[sess_id_col],   filter =filter_clause, distinct=True,
                              params =tuple(params))
            return [str(id[0]) for id in data] if data != None else []
        else:
            Logger.Log(f"Could not get list of all session ids, MySQL connection is not open.", logging.WARN)
            return []

    def _availableDates(self) -> Dict[str,datetime]:
        ret_val = {'min':datetime.now(), 'max':datetime.now()}
        if self._db_cursor is not None and isinstance(self._config.Source, MySQLSchema):
            _db_name     : str = self._config.DatabaseName
            _table_name  : str = self._config.TableName

            # prep filter strings
            filters = []
            params  = []
            if _table_name != self._game_id:
                filters.append(f"`app_id`=%s")
                params.append(self._game_id)
            filter_clause = " AND ".join(filters)

            # run query
            result = SQL.SELECT(cursor=self._db_cursor, db_name=_db_name, table=_table_name,
                                columns=['MIN(server_time)', 'MAX(server_time)'], filter=filter_clause,
                                params =tuple(params))
            if result is not None:
                ret_val = {'min':result[0][0], 'max':result[0][1]}
        else:
            Logger.Log(f"Could not get full date range, MySQL connection is not open or config was not for MySQL.", logging.WARN)
        return ret_val

    def _rowsFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION, versions:Optional[List[int]]=None, exclude_rows:Optional[List[str]]=None) -> List[Tuple]:
        ret_val = []
        # grab data for the given session range. Sort by event time, so
        if self._db_cursor is not None and isinstance(self._config.Source, MySQLSchema):
            # filt = f"app_id='{self._game_id}' AND (session_id  BETWEEN '{next_slice[0]}' AND '{next_slice[-1]}'){ver_filter}"
            _db_name     : str = self._config.DatabaseName
            _table_name  : str = self._config.TableName

            sess_id_col = self._TableSchema.SessionIDColumn or 'session_id'
            play_id_col = self._TableSchema.UserIDColumn or 'player_id'
            seq_idx_col = self._TableSchema.EventSequenceIndexColumn or 'session_n'
            evt_nam_col = self._TableSchema.EventNameColumn or "event_name"

            filters = []
            params = []
            if _table_name != self._game_id:
                filters.append(f"`app_id`=%s")
                params.append(self._game_id)
            # if versions is not None and versions is not []:
            #     filters.append(f"app_version in ({','.join([str(version) for version in versions])})")
            id_param_string = ",".join( [f"%s"]*len(id_list) )
            if id_mode == IDMode.SESSION:
                filters.append(f"`{sess_id_col}` IN ({id_param_string})")
                params += [str(id) for id in id_list]
            elif id_mode == IDMode.USER:
                filters.append(f"`{play_id_col}` IN ({id_param_string})")
                params += [str(id) for id in id_list]
            else:
                raise ValueError("Invalid IDMode in MySQLInterface!")
            if exclude_rows is not None:
                evt_name_param_string = ",".join( ["%s"]*len(exclude_rows) )
                filters.append(f"`{evt_nam_col}` not in ({evt_name_param_string})")
                params += [str(name) for name in exclude_rows]
            filter_clause = " AND ".join(filters)

            data = SQL.SELECT(cursor=self._db_cursor, db_name=_db_name,                        table=_table_name,
                              filter=filter_clause,   sort_columns=[sess_id_col, seq_idx_col], sort_direction="ASC",
                              params=tuple(params))
            if data is not None:
                ret_val = data
            # self._select_queries.append(select_query) # this doesn't appear to be used???
        else:
            Logger.Log(f"Could not get data for {len(id_list)} sessions, MySQL connection is not open or config was not for MySQL.", logging.WARN)
        return ret_val

    def _IDsFromDates(self, min:datetime, max:datetime) -> List[str]:
        ret_val = []
        if self._db_cursor is not None and isinstance(self._config.Source, MySQLSchema):
            # alias long setting names.
            _db_name     : str = self._config.DatabaseName
            _table_name  : str = self._config.TableName

            # prep filter strings
            filters = []
            params = []
            if _table_name != self._game_id:
                filters.append(f"`app_id`=%s")
                params.append(self._game_id)
            filters.append(f"`{self._TableSchema.EventSequenceIndexColumn}`='0'")
            filters.append(f"(`server_time` BETWEEN '{min.isoformat()}' AND '{max.isoformat()}')")
            filter_clause = " AND ".join(filters)

            # run query
            # We grab the ids for all sessions that have 0th move in the proper date range.
            sess_id_col = self._TableSchema.SessionIDColumn or "`session_id`"
            sess_ids_raw = SQL.SELECT(cursor=self._db_cursor,   db_name=_db_name,     table=_table_name,
                                     columns=[sess_id_col],     filter=filter_clause,
                                     sort_columns=[sess_id_col], sort_direction="ASC", distinct=True,
                                     params=tuple(params))
            if sess_ids_raw is not None:
                ret_val = [str(sess[0]) for sess in sess_ids_raw]
        else:
            Logger.Log(f"Could not get session list for {min.isoformat()}-{max.isoformat()} range, MySQL connection is not open or config was not for MySQL.", logging.WARN)
        return ret_val

    def _datesFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION) -> Dict[str, datetime]:
        ret_val = {'min':datetime.now(), 'max':datetime.now()}
        if self._db_cursor is not None and isinstance(self._config.Source, MySQLSchema):
            # alias long setting names.
            _db_name     : str = self._config.DatabaseName
            _table_name  : str = self._config.TableName
            
            # prep filter strings
            filters = []
            params = tuple()
            if _table_name != self._game_id:
                filters.append(f"`app_id`=%s")
                params = tuple(self._game_id)
            ids_string = ','.join([f"'{x}'" for x in id_list])
            if id_mode == IDMode.SESSION:
                sess_id_col = self._TableSchema.SessionIDColumn or "session_id"
                filters.append(f"{sess_id_col} IN ({ids_string})")
            elif id_mode == IDMode.USER:
                play_id_col = self._TableSchema.UserIDColumn or "player_id"
                filters.append(f"`{play_id_col}` IN ({ids_string})")
            else:
                raise ValueError("Invalid IDMode in MySQLInterface!")
            filter_clause = " AND ".join(filters)
            # run query
            result = SQL.SELECT(cursor=self._db_cursor,      db_name=_db_name,    table=_table_name,
                                columns=['MIN(server_time)', 'MAX(server_time)'], filter=filter_clause,
                                params=params)
            if result is not None:
                ret_val = {'min':result[0][0], 'max':result[0][1]}
        else:
            Logger.Log(f"Could not get date range for {len(id_list)} sessions, MySQL connection is not open.", logging.WARN)
        return ret_val

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***

    def _getCursor(self) -> Optional[cursor.MySQLCursor]:
        ret_val : Optional[cursor.MySQLCursor] = None

        if self._db is not None:
            _cursor = self._db.cursor()
            if isinstance(_cursor, cursor.MySQLCursor):
                ret_val = _cursor
            else:
                Logger.Log(f"db.cursor() call returned a cursor of unexpected type {type(ret_val)}, can not access the database!", logging.ERROR)
        return ret_val
