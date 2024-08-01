## import standard libraries
import json
import logging
import os
import re
import shutil
import sys
import traceback
import zipfile
from datetime import datetime
from git.repo import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
from pathlib import Path
from typing import Any, Dict, IO, List, Optional, Set

# import local files
from ogd import games
from ogd.core.connectors.outerfaces.Outerface import Outerface
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.enums.ExportMode import ExportMode
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.schemas.games.GameSchema import GameSchema
from ogd.core.schemas.tables.TableSchema import TableSchema
from ogd.core.schemas.configs.IndexingSchema import FileIndexingSchema
from ogd.core.utils import utils
from ogd.core.utils.Logger import Logger
from ogd.core.utils.utils import ExportRow
from ogd.core.utils.Readme import Readme

class TSVOuterface(Outerface):

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, game_id:str, config:GameSourceSchema, export_modes:Set[ExportMode], date_range:Dict[str,Optional[datetime]], file_indexing:FileIndexingSchema, extension:str="tsv", dataset_id:Optional[str]=None):
        super().__init__(game_id=game_id, config=config, export_modes=export_modes)
        self._file_paths    : Dict[str,Optional[Path]] = {"population":None, "players":None, "sessions":None, "processed_events":None, "raw_events":None}
        self._zip_paths     : Dict[str,Optional[Path]] = {"population":None, "players":None, "sessions":None, "processed_events":None, "raw_events":None}
        self._files         : Dict[str,Optional[IO]]   = {"population":None, "players":None, "sessions":None, "processed_events":None, "raw_events":None}
        self._file_indexing : FileIndexingSchema       = file_indexing
        self._data_dir      : Path = Path(f"./{self._file_indexing.LocalDirectory}")
        self._game_data_dir : Path = self._data_dir / self._game_id
        self._readme_path   : Path = self._game_data_dir / "README.md"
        self._extension     : str  = extension
        self._date_range    : Dict[str,Optional[datetime]] = date_range
        self._dataset_id    : str  = ""
        self._short_hash    : str  = ""
        # self._sess_count    : int  = 0
        # figure out dataset ID.
        # Logger.Log(f"the min in date range is {self._date_range['min']}, of type {type(self._date_range['min'])}")
        start = self._date_range['min'].strftime("%Y%m%d") if self._date_range['min'] is not None else "UNKNOWN"
        end   = self._date_range['max'].strftime("%Y%m%d") if self._date_range['max'] is not None else "UNKNOWN"
        self._dataset_id = dataset_id or f"{self._game_id}_{start}_to_{end}"
        # get hash
        try:
            repo = Repo(search_parent_directories=True)
            if repo.git is not None:
                self._short_hash = str(repo.git.rev_parse(repo.head.object.hexsha, short=7))
        except InvalidGitRepositoryError as err:
            msg = f"Code is not in a valid Git repository:\n{str(err)}"
            Logger.Log(msg, logging.ERROR)
        except NoSuchPathError as err:
            msg = f"Unable to access proper file paths for Git repository:\n{str(err)}"
            Logger.Log(msg, logging.ERROR)
        # then set up our paths, and ensure each exists.
        base_file_name    : str  = f"{self._dataset_id}_{self._short_hash}"
        # finally, generate file names.
        if ExportMode.EVENTS in export_modes:
            self._file_paths['raw_events']       = self._game_data_dir / f"{base_file_name}_events.{self._extension}"
            self._zip_paths['raw_events']        = self._game_data_dir / f"{base_file_name}_events.zip"
        if ExportMode.DETECTORS in export_modes:
            self._file_paths['processed_events'] = self._game_data_dir / f"{base_file_name}_all-events.{self._extension}"
            self._zip_paths['processed_events']  = self._game_data_dir / f"{base_file_name}_all-events.zip"
        if ExportMode.SESSION in export_modes:
            self._file_paths['sessions']         = self._game_data_dir / f"{base_file_name}_session-features.{self._extension}"
            self._zip_paths['sessions']          = self._game_data_dir / f"{base_file_name}_session-features.zip"
        if ExportMode.PLAYER in export_modes:
            self._file_paths['players']          = self._game_data_dir / f"{base_file_name}_player-features.{self._extension}"
            self._zip_paths['players']           = self._game_data_dir / f"{base_file_name}_player-features.zip"
        if ExportMode.POPULATION in export_modes:
            self._file_paths['population']       = self._game_data_dir / f"{base_file_name}_population-features.{self._extension}"
            self._zip_paths['population']        = self._game_data_dir / f"{base_file_name}_population-features.zip"
        # self.Open()

    def __del__(self):
        self.Close()

    # *** IMPLEMENT ABSTRACTS ***

    def _open(self) -> bool:
        self._game_data_dir.mkdir(exist_ok=True, parents=True)
        if (self._file_paths['raw_events'] is not None):
            self._files['raw_events']       = open(self._file_paths['raw_events'],   "w+", encoding="utf-8")
        if (self._file_paths['processed_events'] is not None):
            self._files['processed_events'] = open(self._file_paths['processed_events'],   "w+", encoding="utf-8")
        if (self._file_paths['sessions'] is not None):
            self._files['sessions']         = open(self._file_paths['sessions'], "w+", encoding="utf-8")
        if (self._file_paths['players'] is not None):
            self._files['players']          = open(self._file_paths['players'],  "w+", encoding="utf-8")           
        if (self._file_paths['population'] is not None):
            self._files['population']       = open(self._file_paths['population'], "w+", encoding="utf-8")
        return True

    def _close(self) -> bool:
        Logger.Log(f"Closing TSV outerface...")
        try:
            # before we zip stuff up, let's check if the readme is in place:
            readme = open(self._readme_path, mode='r')
        except FileNotFoundError:
            # if not in place, generate the readme
            Logger.Log(f"Missing readme for {self._game_id}, generating new readme...", logging.WARNING, depth=1)
            _games_path  = Path(games.__file__) if Path(games.__file__).is_dir() else Path(games.__file__).parent
            game_schema  : GameSchema  = GameSchema.FromFile(game_id=self._game_id, schema_path=_games_path / self._game_id / "schemas")
            table_schema = TableSchema(schema_name=self._config.TableSchema)
            readme = Readme(game_schema=game_schema, table_schema=table_schema)
            readme.GenerateReadme(path=self._game_data_dir)
        else:
            # otherwise, readme is there, so just close it and move on.
            readme.close()
            Logger.Log(f"Successfully found, opened, and closed the README.md", logging.DEBUG, depth=1)
        finally:
            self._closeFiles()
            self._zipFiles()
            self._writeMetadataFile(num_sess=self.SessionCount)
            self._updateFileExportList(num_sess=self.SessionCount)
            return True

    def _destination(self, mode:ExportMode) -> str:
        ret_val = ""
        match mode:
            case ExportMode.EVENTS:
                ret_val = str(self._file_paths['raw_events'])
            case ExportMode.DETECTORS:
                ret_val = str(self._file_paths['processed_events'])
            case ExportMode.SESSION:
                ret_val = str(self._file_paths['sessions'])
            case ExportMode.PLAYER:
                ret_val = str(self._file_paths['players'])
            case ExportMode.POPULATION:
                ret_val = str(self._file_paths['population'])
        return ret_val

    def _removeExportMode(self, mode:ExportMode):
        match mode:
            # NOTE: Originally, this case was a lone "if" followed by "if-elif-elif..." for Detectors on.
            # I don't think that was intentional, but wanted to make a note of it just in case.
            case ExportMode.EVENTS:
                if self._files['raw_events'] is not None:
                    self._files['raw_events'].close()
                self._files['raw_events']      = None
                self._file_paths['raw_events'] = None
                self._zip_paths['raw_events']  = None
            case ExportMode.DETECTORS:
                if self._files['processed_events'] is not None:
                    self._files['processed_events'].close()
                self._files['processed_events']      = None
                self._file_paths['processed_events'] = None
                self._zip_paths['processed_events']  = None
            case ExportMode.SESSION:
                if self._files['sessions'] is not None:
                    self._files['sessions'].close()
                self._files['sessions']      = None
                self._file_paths['sessions'] = None
                self._zip_paths['sessions']  = None
            case ExportMode.PLAYER:
                if self._files['players'] is not None:
                    self._files['players'].close()
                self._files['players']      = None
                self._file_paths['players'] = None
                self._zip_paths['players']  = None
            case ExportMode.POPULATION:
                if self._files['population'] is not None:
                    self._files['population'].close()
                self._files['population']      = None
                self._file_paths['population'] = None
                self._zip_paths['population']  = None

    def _writeRawEventsHeader(self, header:List[str]) -> None:
        cols = TSVOuterface._cleanSpecialChars(vals=header)
        cols_line = "\t".join(cols) + "\n"
        if self._files['raw_events'] is not None:
            self._files['raw_events'].writelines(cols_line)
        else:
            Logger.Log("No raw_events file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(cols_line))

    def _writeProcessedEventsHeader(self, header:List[str]) -> None:
        cols = TSVOuterface._cleanSpecialChars(vals=header)
        cols_line = "\t".join(cols) + "\n"
        if self._files['processed_events'] is not None:
            self._files['processed_events'].writelines(cols_line)
        else:
            Logger.Log("No processed_events file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(cols_line))

    def _writeSessionHeader(self, header:List[str]) -> None:
        cols = TSVOuterface._cleanSpecialChars(vals=header)
        cols_line = "\t".join(cols) + "\n"
        if self._files['sessions'] is not None:
            self._files['sessions'].writelines(cols_line)
        else:
            Logger.Log("No session file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(cols_line))

    def _writePlayerHeader(self, header:List[str]) -> None:
        cols = TSVOuterface._cleanSpecialChars(vals=header)
        cols_line = "\t".join(cols) + "\n"
        if self._files['players'] is not None:
            self._files['players'].writelines(cols_line)
        else:
            Logger.Log("No player file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(cols_line))

    def _writePopulationHeader(self, header:List[str]) -> None:
        cols = TSVOuterface._cleanSpecialChars(vals=header)
        cols_line = "\t".join(cols) + "\n"
        if self._files['population'] is not None:
            self._files['population'].writelines(cols_line)
        else:
            Logger.Log("No population file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(cols_line))

    def _writeRawEventLines(self, events:List[ExportRow]) -> None:
        event_strs = [TSVOuterface._cleanSpecialChars(vals=[str(item) for item in event]) for event in events]
        event_lines = ["\t".join(event) + "\n" for event in event_strs]
        if self._files['raw_events'] is not None:
            self._files['raw_events'].writelines(event_lines)
        else:
            Logger.Log("No raw_events file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(event_lines))

    def _writeProcessedEventLines(self, events:List[ExportRow]) -> None:
        event_strs = [TSVOuterface._cleanSpecialChars(vals=[str(item) for item in event]) for event in events]
        event_lines = ["\t".join(event) + "\n" for event in event_strs]
        if self._files['processed_events'] is not None:
            self._files['processed_events'].writelines(event_lines)
        else:
            Logger.Log("No processed_events file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(event_lines))

    def _writeSessionLines(self, sessions:List[ExportRow]) -> None:
        # self._sess_count += len(sessions)
        _session_feats = [TSVOuterface._cleanSpecialChars(vals=sess) for sess in sessions]
        _session_lines = ["\t".join(sess) + "\n" for sess in _session_feats]
        if self._files['sessions'] is not None:
            self._files['sessions'].writelines(_session_lines)
        else:
            Logger.Log("No session file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(_session_lines))

    def _writePlayerLines(self, players:List[ExportRow]) -> None:
        _player_feats = [TSVOuterface._cleanSpecialChars(vals=play) for play in players]
        _player_lines = ["\t".join(play) + "\n" for play in _player_feats]
        if self._files['players'] is not None:
            self._files['players'].writelines(_player_lines)
        else:
            Logger.Log("No player file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(_player_lines))

    def _writePopulationLines(self, populations:List[ExportRow]) -> None:
        _pop_feats = [TSVOuterface._cleanSpecialChars(vals=pop) for pop in populations]
        _pop_lines = ["\t".join(pop) + "\n" for pop in _pop_feats]
        if self._files['population'] is not None:
            self._files['population'].writelines(_pop_lines)
        else:
            Logger.Log("No population file available, writing to standard output instead.", logging.WARN)
            sys.stdout.write("".join(_pop_lines))

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    @staticmethod
    def _cleanSpecialChars(vals:List[Any], tab_width:int=3) -> List[str]:
        # check all return values for strings, and ensure no newlines or tabs get through, as they could throw off our outputs.
        for i in range(len(vals)):
            vals[i] = str(vals[i]).replace('\n', ' ').replace('\t', ' '*tab_width)
        return vals

    @staticmethod
    def _addToZip(path, zip_file, path_in_zip) -> None:
        try:
            zip_file.write(path, path_in_zip)
        except FileNotFoundError as err:
            Logger.Log(str(err), logging.ERROR)
            traceback.print_tb(err.__traceback__)

    # *** PRIVATE METHODS ***

    def _closeFiles(self) -> None:
        if self._files['raw_events'] is not None:
            self._files['raw_events'].close()
        if self._files['processed_events'] is not None:
            self._files['processed_events'].close()
        if self._files['sessions'] is not None:
            self._files['sessions'].close()
        if self._files['players'] is not None:
            self._files['players'].close()
        if self._files['population'] is not None:
            self._files['population'].close()

    def _zipFiles(self) -> None:
        existing_datasets = {}
        try:
            file_directory = utils.loadJSONFile(filename="file_list.json", path=self._data_dir)
            existing_datasets = file_directory.get(self._game_id, {})
        except FileNotFoundError as err:
            Logger.Log("file_list.json does not exist.", logging.WARNING)
        except json.decoder.JSONDecodeError as err:
            Logger.Log(f"file_list.json has invalid format: {str(err)}.", logging.WARNING)
        # if we have already done this dataset before, rename old zip files
        # (of course, first check if we ever exported this game before).
        existing_meta = existing_datasets.get(self._dataset_id, None)
        if existing_meta is not None:
            _existing_raw_events_file  = existing_meta.get('raw_events_file', None)
            _existing_proc_events_file = existing_meta.get('processed_events_file', None) or existing_meta.get('events_file', None)
            _existing_sess_file    = existing_meta.get('sessions_file', None)
            _existing_players_file = existing_meta.get('players_file', None)
            _existing_pop_file     = existing_meta.get('population_file', None)
            try:
                if _existing_raw_events_file is not None and Path(_existing_raw_events_file).is_file() and self._zip_paths['raw_events'] is not None:
                    Logger.Log(f"Renaming {str(_existing_raw_events_file)} -> {self._zip_paths['raw_events']}", logging.DEBUG)
                    os.rename(_existing_raw_events_file, str(self._zip_paths['raw_events']))
                if _existing_proc_events_file is not None and Path(_existing_proc_events_file).is_file() and self._zip_paths['processed_events'] is not None:
                    Logger.Log(f"Renaming {str(_existing_proc_events_file)} -> {self._zip_paths['processed_events']}", logging.DEBUG)
                    os.rename(_existing_proc_events_file, str(self._zip_paths['processed_events']))
                if _existing_sess_file is not None and Path(_existing_sess_file).is_file() and self._zip_paths['sessions'] is not None:
                    Logger.Log(f"Renaming {str(_existing_sess_file)} -> {self._zip_paths['sessions']}", logging.DEBUG)
                    os.rename(_existing_sess_file, str(self._zip_paths['sessions']))
                if _existing_players_file is not None and Path(_existing_players_file).is_file() and self._zip_paths['players'] is not None:
                    Logger.Log(f"Renaming {str(_existing_players_file)} -> {self._zip_paths['players']}", logging.DEBUG)
                    os.rename(_existing_players_file, str(self._zip_paths['players']))
                if _existing_pop_file is not None and Path(_existing_pop_file).is_file() and self._zip_paths['population'] is not None:
                    Logger.Log(f"Renaming {str(_existing_pop_file)} -> {self._zip_paths['population']}", logging.DEBUG)
                    os.rename(_existing_pop_file, str(self._zip_paths['population']))
            except FileExistsError as err:
                msg = f"Error while setting up zip files, could not rename an existing file because another file is already using the target name! {err}"
                Logger.Log(msg, logging.ERROR)
            except Exception as err:
                msg = f"Unexpected error while setting up zip files! {type(err)} : {err}"
                Logger.Log(msg, logging.ERROR)
                traceback.print_tb(err.__traceback__)
        # for each file, try to save out the csv/tsv to a file - if it's one that should be exported, that is.
        if self._zip_paths['population'] is not None:
            with zipfile.ZipFile(self._zip_paths["population"], "w", compression=zipfile.ZIP_DEFLATED) as population_zip_file:
                try:
                    population_file = Path(self._dataset_id) / f"{self._dataset_id}_{self._short_hash}_population-features.{self._extension}"
                    readme_file  = Path(self._dataset_id) / "README.md"
                    TSVOuterface._addToZip(path=self._file_paths["population"], zip_file=population_zip_file, path_in_zip=population_file)
                    TSVOuterface._addToZip(path=self._readme_path,              zip_file=population_zip_file, path_in_zip=readme_file)
                    population_zip_file.close()
                    if self._file_paths["population"] is not None:
                        os.remove(self._file_paths["population"])
                except FileNotFoundError as err:
                    Logger.Log(f"FileNotFoundError Exception: {err}", logging.ERROR)
                    traceback.print_tb(err.__traceback__)
        if self._zip_paths['players'] is not None:
            with zipfile.ZipFile(self._zip_paths["players"], "w", compression=zipfile.ZIP_DEFLATED) as players_zip_file:
                try:
                    player_file = Path(self._dataset_id) / f"{self._dataset_id}_{self._short_hash}_player-features.{self._extension}"
                    readme_file  = Path(self._dataset_id) / "README.md"
                    TSVOuterface._addToZip(path=self._file_paths["players"], zip_file=players_zip_file, path_in_zip=player_file)
                    TSVOuterface._addToZip(path=self._readme_path,           zip_file=players_zip_file, path_in_zip=readme_file)
                    players_zip_file.close()
                    if self._file_paths["players"] is not None:
                        os.remove(self._file_paths["players"])
                except FileNotFoundError as err:
                    Logger.Log(f"FileNotFoundError Exception: {err}", logging.ERROR)
                    traceback.print_tb(err.__traceback__)
        if self._zip_paths['sessions'] is not None:
            with zipfile.ZipFile(self._zip_paths["sessions"], "w", compression=zipfile.ZIP_DEFLATED) as sessions_zip_file:
                try:
                    session_file = Path(self._dataset_id) / f"{self._dataset_id}_{self._short_hash}_session-features.{self._extension}"
                    readme_file  = Path(self._dataset_id) / "README.md"
                    TSVOuterface._addToZip(path=self._file_paths["sessions"], zip_file=sessions_zip_file, path_in_zip=session_file)
                    TSVOuterface._addToZip(path=self._readme_path,            zip_file=sessions_zip_file, path_in_zip=readme_file)
                    sessions_zip_file.close()
                    if self._file_paths["sessions"] is not None:
                        os.remove(self._file_paths["sessions"])
                except FileNotFoundError as err:
                    Logger.Log(f"FileNotFoundError Exception: {err}", logging.ERROR)
                    traceback.print_tb(err.__traceback__)
        if self._zip_paths['raw_events'] is not None:
            with zipfile.ZipFile(self._zip_paths["raw_events"], "w", compression=zipfile.ZIP_DEFLATED) as _raw_events_zip_file:
                try:
                    events_file = Path(self._dataset_id) / f"{self._dataset_id}_{self._short_hash}_events.{self._extension}"
                    readme_file = Path(self._dataset_id) / "README.md"
                    TSVOuterface._addToZip(path=self._file_paths["raw_events"], zip_file=_raw_events_zip_file, path_in_zip=events_file)
                    TSVOuterface._addToZip(path=self._readme_path,          zip_file=_raw_events_zip_file, path_in_zip=readme_file)
                    _raw_events_zip_file.close()
                    if self._file_paths["raw_events"] is not None:
                        os.remove(self._file_paths["raw_events"])
                except FileNotFoundError as err:
                    Logger.Log(f"FileNotFoundError Exception: {err}", logging.ERROR)
                    traceback.print_tb(err.__traceback__)
        if self._zip_paths['processed_events'] is not None:
            with zipfile.ZipFile(self._zip_paths["processed_events"], "w", compression=zipfile.ZIP_DEFLATED) as _processed_events_zip_file:
                try:
                    events_file = Path(self._dataset_id) / f"{self._dataset_id}_{self._short_hash}_all-events.{self._extension}"
                    readme_file = Path(self._dataset_id) / "README.md"
                    TSVOuterface._addToZip(path=self._file_paths["processed_events"], zip_file=_processed_events_zip_file, path_in_zip=events_file)
                    TSVOuterface._addToZip(path=self._readme_path,          zip_file=_processed_events_zip_file, path_in_zip=readme_file)
                    _processed_events_zip_file.close()
                    if self._file_paths["processed_events"] is not None:
                        os.remove(self._file_paths["processed_events"])
                except FileNotFoundError as err:
                    Logger.Log(f"FileNotFoundError Exception: {err}", logging.ERROR)
                    traceback.print_tb(err.__traceback__)

    ## Public function to write out a tiny metadata file for indexing OGD data files.
    #  Using the paths of the exported files, and given some other variables for
    #  deriving file metadata, this simply outputs a new file_name.meta file.
    #  @param date_range    The range of dates included in the exported data.
    #  @param num_sess      The number of sessions included in the recent export.
    def _writeMetadataFile(self, num_sess:int) -> None:
        # First, ensure we have a data directory.
        try:
            self._game_data_dir.mkdir(exist_ok=True, parents=True)
        except Exception as err:
            msg = f"Could not set up folder {self._game_data_dir}. {type(err)} {str(err)}"
            Logger.Log(msg, logging.WARNING)
        else:
            # Second, remove old metas, if they exist.
            start_range = self._date_range['min'].strftime("%Y%m%d") if self._date_range['min'] is not None else "Unknown"
            end_range   = self._date_range['max'].strftime("%Y%m%d") if self._date_range['max'] is not None else "Unknown"
            match_string = f"{self._game_id}_{start_range}_to_{end_range}_\\w*\\.meta"
            old_metas = [f for f in os.listdir(self._game_data_dir) if re.match(match_string, f)]
            for old_meta in old_metas:
                try:
                    Logger.Log(f"Removing old meta file, {old_meta}")
                    os.remove(self._game_data_dir / old_meta)
                except Exception as err:
                    msg = f"Could not remove old meta file {old_meta}. {type(err)} {str(err)}"
                    Logger.Log(msg, logging.WARNING)
            # Third, write the new meta file.
            # calculate the path and name of the metadata file, and open/make it.
            meta_file_path : Path = self._game_data_dir/ f"{self._dataset_id}_{self._short_hash}.meta"
            with open(meta_file_path, "w", encoding="utf-8") as meta_file :
                metadata  = \
                {
                    "game_id"      :self._game_id,
                    "dataset_id"   :self._dataset_id,
                    "ogd_revision" :self._short_hash,
                    "start_date"   :self._date_range['min'].strftime("%m/%d/%Y") if self._date_range['min'] is not None else "Unknown",
                    "end_date"     :self._date_range['max'].strftime("%m/%d/%Y") if self._date_range['max'] is not None else "Unknown",
                    "date_modified":datetime.now().strftime("%m/%d/%Y"),
                    "sessions"     :num_sess,
                    "population_file"     : str(self._zip_paths['population'])       if self._zip_paths['population']       else None,
                    "population_template" : f'/tree/{self._game_id.lower()}'         if self._zip_paths['population']       else None,
                    "players_file"        : str(self._zip_paths['players'])          if self._zip_paths['players']          else None,
                    "players_template"    : f'/tree/{self._game_id.lower()}'         if self._zip_paths['players']          else None,
                    "sessions_file"       : str(self._zip_paths['sessions'])         if self._zip_paths['sessions']         else None,
                    "sessions_template"   : f'/tree/{self._game_id.lower()}'         if self._zip_paths['sessions']         else None,
                    "raw_file"            : str(self._zip_paths['raw_events'])       if self._zip_paths['raw_events']       else None,
                    "events_template"     : f'/tree/{self._game_id.lower()}'         if self._zip_paths['raw_events']       else None,
                    "events_file"         : str(self._zip_paths['processed_events']) if self._zip_paths['processed_events'] else None,
                    "all_events_template" : f'/tree/{self._game_id.lower()}'         if self._zip_paths['processed_events'] else None
                }
                meta_file.write(json.dumps(metadata, indent=4))
                meta_file.close()

    ## Public function to update the list of exported files.
    #  Using the paths of the exported files, and given some other variables for
    #  deriving file metadata, this simply updates the JSON file to the latest
    #  list of files.
    #  @param date_range    The range of dates included in the exported data.
    #  @param num_sess      The number of sessions included in the recent export.
    def _updateFileExportList(self, num_sess: int) -> None:
        self._backupFileExportList()
        file_index = {}
        existing_datasets = {}
        try:
            file_index = utils.loadJSONFile(filename="file_list.json", path=self._data_dir)
        except FileNotFoundError as err:
            Logger.Log("file_list.json does not exist.", logging.WARNING)
        except json.decoder.JSONDecodeError as err:
            Logger.Log(f"file_list.json has invalid format: {str(err)}.", logging.WARNING)
        finally:
            if not "CONFIG" in file_index.keys():
                Logger.Log(f"No CONFIG found in file_list.json, adding default CONFIG...", logging.WARNING)
                file_index["CONFIG"] = {
                    "files_base" : self._file_indexing.RemoteURL,
                    "templates_base" : self._file_indexing.TemplatesURL
                }
            if not self._game_id in file_index.keys():
                file_index[self._game_id] = {}
            existing_datasets  = file_index[self._game_id]
            with open(self._data_dir / "file_list.json", "w") as existing_csv_file:
                Logger.Log(f"Opened file list for writing at {existing_csv_file.name}", logging.INFO)
                existing_metadata = existing_datasets.get(self._dataset_id, {})
                population_path = self._zip_paths.get("population") or existing_metadata.get("population")
                players_path    = self._zip_paths.get("players")    or existing_metadata.get("players")
                sessions_path   = self._zip_paths.get("sessions")   or existing_metadata.get("sessions")
                raw_events_path = self._zip_paths.get("raw_events") or existing_metadata.get("raw_events") or existing_metadata.get("events")
                processed_events_path = self._zip_paths.get("processed_events") or existing_metadata.get("processed_events")
                file_index[self._game_id][self._dataset_id] = \
                {
                    "ogd_revision"          : self._short_hash,
                    "start_date"            : self._date_range['min'].strftime("%m/%d/%Y") if self._date_range['min'] is not None else "Unknown",
                    "end_date"              : self._date_range['max'].strftime("%m/%d/%Y") if self._date_range['max'] is not None else "Unknown",
                    "date_modified"         : datetime.now().strftime("%m/%d/%Y"),
                    "sessions"              : num_sess,
                    "population_file"       : str(population_path)       if population_path       is not None else None,
                    "population_template"   : ''                         if population_path       is not None else None,
                    "players_file"          : str(players_path)          if players_path          is not None else None,
                    "players_template"      : ''                         if players_path          is not None else None,
                    "sessions_file"         : str(sessions_path)         if sessions_path         is not None else None,
                    "sessions_template"     : ''                         if sessions_path         is not None else None,
                    "events_file"           : str(raw_events_path)       if raw_events_path       is not None else None,
                    "events_template"       : ''                         if raw_events_path       is not None else None,
                    "all_events_file"       : str(processed_events_path) if processed_events_path is not None else None,
                    "all_events_template"   : ''                         if processed_events_path is not None else None
                }
                existing_csv_file.write(json.dumps(file_index, indent=4))

    def _backupFileExportList(self) -> bool:
        try:
            src  : Path = self._data_dir / "file_list.json"
            dest : Path = self._data_dir / "file_list.json.bak"
            if src.exists():
                shutil.copyfile(src=src, dst=dest)
            else:
                Logger.Log(f"Could not back up file_list.json, because it does not exist!", logging.WARN)
        except Exception as err:
            msg = f"{type(err)} {str(err)}"
            Logger.Log(f"Could not back up file_list.json. Got the following error: {msg}", logging.ERROR)
            return False
        else:
            Logger.Log(f"Backed up file_list.json to {dest}", logging.INFO)
            return True