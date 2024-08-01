"""Module containing all the commands available through the OGD CLI"""
# import standard libraries
import csv
import logging
import traceback
from argparse import Namespace
from itertools import chain
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple

# import 3rd-party libraries

# import OGD files
# from ogd.core.exec.Generators import OGDGenerators
from ogd.core.connectors.interfaces.CSVInterface import CSVInterface
from ogd.core.connectors.interfaces.EventInterface import EventInterface
from ogd.core.connectors.outerfaces.Outerface import Outerface
from ogd.core.connectors.outerfaces.DebugOuterface import DebugOuterface
from ogd.core.connectors.outerfaces.TSVOuterface import TSVOuterface
from ogd.core.managers.ExportManager import ExportManager
from ogd.core.models.enums.ExportMode import ExportMode
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.requests.Request import ExporterRange, Request
from ogd.core.requests.RequestResult import RequestResult, ResultStatus
from ogd.core.schemas.configs.ConfigSchema import ConfigSchema
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.schemas.games.GameSchema import GameSchema
from ogd.core.schemas.tables.EventTableSchema import EventTableSchema
from ogd.core.utils.Logger import Logger
from ogd.core.utils.Readme import Readme
from .Generators import OGDGenerators


class OGDCommands:
    """Utility class to collect functions for each of the commands that can be run when executing ogd-core as a module."""

    # *** BUILT-INS & PROPERTIES ***

    # *** PUBLIC STATICS ***

    @staticmethod
    def ListGames(games_list:List[str]) -> bool:
        """Command to list out the games available for export.

        :param games_list: The list of available games, which the command should display.
        :type games_list: List[str]
        :return: True if the list was successfully displayed, else False.
        :rtype: bool
        """
        print(f"The games available for export are:\n{games_list}")
        return True

    @staticmethod
    def ShowGameInfo(config:ConfigSchema, game:str) -> bool:
        """Function to print out info on a game from the game's schema.
    This does a similar function to writeReadme, but is limited to the CSV metadata part
    (basically what was in the schema, at one time written into the csv's themselves).
    Further, the output is printed rather than written to file.

        :return: True if game metadata was successfully loaded and printed, or False if an error occurred
        :rtype: bool
        """
        try:
            game_schema = GameSchema.FromFile(game_id=game)
            table_schema = EventTableSchema(schema_name=f"{config.GameSourceMap[game].TableSchema}.json")
            readme = Readme(game_schema=game_schema, table_schema=table_schema)
            print(readme.CustomReadmeSource)
        except Exception as err:
            msg = f"Could not print information for {game}: {type(err)} {str(err)}"
            Logger.Log(msg, logging.ERROR)
            traceback.print_tb(err.__traceback__)
            return False
        else:
            return True

    @staticmethod
    def WriteReadme(config:ConfigSchema, game:str, destination:Path) -> bool:
        """Function to write out the readme file for a given game.
    This includes the CSV metadata (data from the schema, originally written into
    the CSV files themselves), custom readme source, and the global changelog.
    The readme is placed in the game's data folder.

        :return: _description_
        :rtype: bool
        """
        path = destination / game
        try:
            game_schema = GameSchema.FromFile(game_id=game, schema_path=Path("src") / "ogd" / "games" / game / "schemas")
            table_schema = EventTableSchema(schema_name=f"{config.GameSourceMap[game].TableSchema}.json")
            readme = Readme(game_schema=game_schema, table_schema=table_schema)
            readme.GenerateReadme(path=path)
        except Exception as err:
            msg = f"Could not create a readme for {game}: {type(err)} {str(err)}"
            Logger.Log(msg, logging.ERROR)
            traceback.print_tb(err.__traceback__)
            return False
        else:
            Logger.Log(f"Successfully generated a readme for {game}.", logging.INFO)
            return True

    @staticmethod
    def RunExport(args:Namespace, config:ConfigSchema, destination:Path, with_events:bool = False, with_features:bool = False) -> bool:
        """Function to handle execution of export code.
        This is the main intended use of the program.

        :param events: _description_, defaults to False
        :type events: bool, optional
        :param features: _description_, defaults to False
        :type features: bool, optional
        :return: _description_
        :rtype: bool

        .. todo:: Make use of destination parameter
        .. todo:: Refactor "step 2" logic into smaller functions, probably a "get case", then pass in to a "get range" and "get dataset ID"
        """
        success : bool = False

        export_modes   : Set[ExportMode]
        interface      : EventInterface
        export_range   : ExporterRange
        file_outerface : Outerface
        dataset_id     : Optional[str] = None

    # 1. get exporter modes to run
        export_modes = OGDGenerators.GenModes(with_events=with_events, with_features=with_features,
                                              no_session_file=args.no_session_file, no_player_file=args.no_player_file, no_pop_file=args.no_pop_file)
    # 2. figure out the interface and range; optionally set a different dataset_id
        if args.file is not None and args.file != "":
            # raise NotImplementedError("Sorry, exports with file inputs are currently broken.")
            _ext = str(args.file).rsplit('.', maxsplit=1)[-1]
            _cfg = GameSourceSchema(name="FILE SOURCE", all_elements={"schema":"OGD_EVENT_FILE"}, data_sources={})
            interface = CSVInterface(game_id=args.game, config=_cfg, fail_fast=config.FailFast, filepath=Path(args.file), delim="\t" if _ext == 'tsv' else ',')
            export_range = ExporterRange.FromIDs(source=interface, ids=interface.AvailableIDs() or [])
        else:
            interface = OGDGenerators.GenDBInterface(config=config, game=args.game)
        # a. Case where specific player ID was given
            if args.player is not None and args.player != "":
                export_range = ExporterRange.FromIDs(source=interface, ids=[args.player], id_mode=IDMode.USER)
                dataset_id = f"{args.game}_{args.player}"
        # b. Case where player ID file was given
            elif args.player_id_file is not None and args.player_id_file != "":
                file_path = Path(args.player_id_file)
                with open(file_path) as player_file:
                    reader = csv.reader(player_file)
                    file_contents = list(reader) # this gives list of lines, each line a list
                    names = list(chain.from_iterable(file_contents)) # so, convert to single list
                    print(f"list of names: {list(names)}")
                    export_range = ExporterRange.FromIDs(source=interface, ids=names, id_mode=IDMode.USER)
                dataset_id = f"{args.game}_from_{file_path.name}"
        # c. Case where specific session ID was given
            elif args.session is not None and args.session != "":
                export_range = ExporterRange.FromIDs(source=interface, ids=[args.session], id_mode=IDMode.SESSION)
                dataset_id = f"{args.game}_{args.session}"
        # d. Case where session ID file was given
            elif args.session_id_file is not None and args.session_id_file != "":
                file_path = Path(args.session_id_file)
                with open(file_path) as session_file:
                    reader = csv.reader(session_file)
                    file_contents = list(reader) # this gives list of lines, each line a list
                    names = list(chain.from_iterable(file_contents)) # so, convert to single list
                    print(f"list of sessions: {list(names)}")
                    export_range = ExporterRange.FromIDs(source=interface, ids=names, id_mode=IDMode.SESSION)
                dataset_id = f"{args.game}_from_{file_path.name}"
        # e. Default case where we use date range
            else:
                export_range = OGDGenerators.GenDateRange(game=args.game, interface=interface, monthly=args.monthly, start_date=args.start_date, end_date=args.end_date)
    # 3. set up the outerface, based on the range and dataset_id.
        _cfg = GameSourceSchema(name="FILE DEST", all_elements={"database":"FILE", "table":"DEBUG", "schema":"OGD_EVENT_FILE"}, data_sources={})
        file_outerface = TSVOuterface(game_id=args.game, config=_cfg, export_modes=export_modes, date_range=export_range.DateRange,
                                    file_indexing=config.FileIndexConfig, dataset_id=dataset_id)
        outerfaces : Set[Outerface] = {file_outerface}
        # If we're in debug level of output, include a debug outerface, so we know what is *supposed* to go through the outerfaces.
        if config.DebugLevel == "DEBUG":
            _cfg = GameSourceSchema(name="DEBUG", all_elements={"database":"DEBUG", "table":"DEBUG", "schema":"OGD_EVENT_FILE"}, data_sources={})
            outerfaces.add(DebugOuterface(game_id=args.game, config=_cfg, export_modes=export_modes))

    # 4. Once we have the parameters parsed out, construct the request.
        req = Request(range=export_range, exporter_modes=export_modes, interface=interface, outerfaces=outerfaces)
        if req.Interface.IsOpen:
            export_manager : ExportManager = ExportManager(config=config)
            result         : RequestResult = export_manager.ExecuteRequest(request=req)
            success = result.Status == ResultStatus.SUCCESS
            level = logging.INFO if success else logging.ERROR
            Logger.Log(message=result.Message, level=level)
            Logger.Log(f"Total data request execution time: {result.Duration}", logging.INFO)
            # cProfile.runctx("feature_exporter.ExportFromSQL(request=req)",
                            # {'req':req, 'feature_exporter':feature_exporter}, {})
        return success

    # *** PUBLIC METHODS ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
