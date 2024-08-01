"""Module for generating certain objects for internal use in the OGD CLI"""
# import standard libraries
import logging
from calendar import monthrange
from datetime import datetime
from typing import Optional, Set

# import 3rd-party libraries

# import local files
from ogd.core.connectors.interfaces.EventInterface import EventInterface
from ogd.core.connectors.interfaces.MySQLInterface import MySQLInterface
from ogd.core.connectors.interfaces.BigQueryInterface import BigQueryInterface
from ogd.core.connectors.interfaces.BQFirebaseInterface import BQFirebaseInterface
from ogd.core.requests.Request import ExporterRange
from ogd.core.schemas.configs.ConfigSchema import ConfigSchema
from ogd.core.models.enums.ExportMode import ExportMode
from ogd.core.utils.Logger import Logger

class OGDGenerators:
    """Utility class to collect functions for generating objects used to execute certain commands.
    
    Essentially, just a collection of random stuff that we didn't want cluttering other files.
    """

    @staticmethod
    def GenDBInterface(config:ConfigSchema, game:str) -> EventInterface:
        """Create a data interface based on a config and desired game.

        :param config: The current OGD configuration
        :type config: ConfigSchema
        :param game: The ID of the game whose data should be retrieved from the interface
        :type game: str
        :raises Exception: If the configuration for the given game does not give a valid type of database for the source.
        :raises ValueError: If the given game does not exist in the GameSourceMap of the given configuration.
        :return: A data interface for the configured type of database.
        :rtype: EventInterface

        .. todo:: Accept a GameSourceSchema instead of a full ConfigSchema
        .. todo:: Use the "upper" of the source type, instead of checking for capitalized and non-capitalized versions of names.
        """
        ret_val : EventInterface
        _game_cfg = config.GameSourceMap.get(game)
        if _game_cfg is not None and _game_cfg.Source is not None:
            match (_game_cfg.Source.Type):
                case "Firebase" | "FIREBASE":
                    ret_val = BQFirebaseInterface(game_id=game, config=_game_cfg, fail_fast=config.FailFast)
                case "BigQuery" | "BIGQUERY":
                    ret_val = BigQueryInterface(game_id=game, config=_game_cfg, fail_fast=config.FailFast)
                case "MySQL" | "MYSQL":
                    ret_val = MySQLInterface(game_id=game, config=_game_cfg, fail_fast=config.FailFast)
                case _:
                    raise Exception(f"{_game_cfg.Source.Type} is not a valid EventInterface type!")
            return ret_val
        else:
            raise ValueError(f"Config for {game} was invalid or not found!")

    @staticmethod
    def GenModes(with_events:bool, with_features:bool, no_session_file:bool, no_player_file:bool, no_pop_file:bool) -> Set[ExportMode]:
        """Convert a series of booleans for each type of export mode into a set of ExportMode enum values.

        :param with_events: Whether to include `EVENTS` and `DETECTORS` in the set
        :type with_events: bool
        :param with_features: Whether to include any feature types in the set
        :type with_features: bool
        :param no_session_file: Whether to include `SESSION` in the set
        :type no_session_file: bool
        :param no_player_file: Whether to include `PLAYER` in the set
        :type no_player_file: bool
        :param no_pop_file: Whether to include `POPULATION` in the set
        :type no_pop_file: bool
        :return: A set of ExportModes, based on the arguments
        :rtype: Set[ExportMode]
        """
        ret_val = set()

        if with_events:
            ret_val.add(ExportMode.EVENTS)
            ret_val.add(ExportMode.DETECTORS)
        if with_features:
            if not no_session_file:
                ret_val.add(ExportMode.SESSION)
            if not no_player_file:
                ret_val.add(ExportMode.PLAYER)
            if not no_pop_file:
                ret_val.add(ExportMode.POPULATION)

        return ret_val

    # retrieve/calculate date range.
    @staticmethod
    def GenDateRange(game:str, interface:EventInterface, monthly:bool, start_date:str, end_date:Optional[str]) -> ExporterRange:
        """Use a pair of date strings to create an `ExporterRange` for use with an interface.

        Also allows the range to be specified as "monthly,"
        i.e. to treat the "start date" as a specification of a full month for the range.
        Note that `ExporterRange` objects carry data about the sessions contained within the range,
        so an interface is required in order to create the session list.

        :param game: The specific game for which a date range is generated
        :type game: str
        :param interface: An interface to use for generation of the `ExporterRange`.
        :type interface: EventInterface
        :param monthly: Whether the range should cover a full month, or use the exact given start and end.
        :type monthly: bool
        :param start_date: A string representing the first day of the range in MM/DD/YYYY format, or the month to use for the range in MM/YYYY format.
        :type start_date: str
        :param end_date: A string representing the last day of the range in MM/DD/YYYY format, or None (if using a full month range)
        :type end_date: Optional[str]
        :raises ValueError: If using full month range, and `start_date` does not have a correct format.
        :return: An `ExporterRange` object representing the given range, as well as the sessions available for that range via the given interface.
        :rtype: ExporterRange

        .. todo:: Don't include game as param, it's only used in outputs, which should not be included here.
        .. todo:: Add some try-except logic around the `int(...)` calls.
        .. todo:: Add logic to check for yyyymmdd in addition to mmddyyyy.
        .. todo:: Add logic to check for `-` separators, in addition to `/`.
        """
        _from : datetime
        _to   : datetime
        today : datetime = datetime.now()
        # If we want to export all data for a given month, calculate a date range from 1st to end of month.
        if monthly:
            month : int = today.month
            year  : int = today.year
            month_year = start_date.split("/")
            month = int(month_year[0])
            year  = int(month_year[1])
            month_range = monthrange(year, month)
            days_in_month = month_range[1]
            _from = datetime(year=year, month=month, day=1, hour=0, minute=0, second=0)
            _to   = datetime(year=year, month=month, day=days_in_month, hour=23, minute=59, second=59)
            Logger.Log(f"Exporting {month}/{year} data for {game}...", logging.DEBUG)
        # Otherwise, create date range from given pair of dates.
        else:
            _from = datetime.strptime(start_date, "%m/%d/%Y") if start_date is not None else today
            _from = _from.replace(hour=0, minute=0, second=0)
            _to   = datetime.strptime(end_date, "%m/%d/%Y") if end_date is not None else _from
            _to = _to.replace(hour=23, minute=59, second=59)
            if _from > _to:
                raise ValueError(f"Invalid date range, start date of {_from} is after end date of {_to}!")
            Logger.Log(f"Exporting from {str(_from)} to {str(_to)} of data for {game}...", logging.INFO)
        return ExporterRange.FromDateRange(source=interface, date_min=_from, date_max=_to)
