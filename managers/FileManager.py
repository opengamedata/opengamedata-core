import abc
import git
import json
import logging
import os
import re
import shutil
import traceback
import typing
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, IO, Union
## import local files
import utils
from managers.Request import ExporterFiles, ExporterRange

class FileManager(abc.ABC):
    def __init__(self, exporter_files: ExporterFiles, game_id, data_dir: str, date_range: Dict[str,Union[datetime,None]], extension:str="tsv"):
        self._file_names   : Dict[str,Union[Path,None]] = {"population":None, "sessions":None, "events":None}
        self._zip_names    : Dict[str,Union[Path,None]] = {"population":None, "sessions":None, "events":None}
        self._files        : Dict[str,Union[IO,None]]   = {"population":None, "sessions":None, "events":None}
        self._game_id      : str  = game_id
        self._data_dir     : Path = Path("./" + data_dir)
        self._game_data_dir: Path = self._data_dir / self._game_id
        self._readme_path  : Path = self._game_data_dir/ "readme.md"
        self._extension    : str  = extension
        self._date_range   : Dict[str,Union[datetime,None]] = date_range
        self._dataset_id   : str  = ""
        self._short_hash   : str  = ""
        try:
            # figure out dataset ID.
            start = date_range['min'].strftime("%Y%m%d") if date_range['min'] is not None else "UNKNOWN"
            end   = date_range['max'].strftime("%Y%m%d") if date_range['max'] is not None else "UNKNOWN"
            self._dataset_id = f"{self._game_id}_{start}_to_{end}"
            # get hash
            repo = git.Repo(search_parent_directories=True)
            if repo.git is not None:
                self._short_hash = str(repo.git.rev_parse(repo.head.object.hexsha, short=7))
            # then set up our paths, and ensure each exists.
            base_file_name    : str  = f"{self._dataset_id}_{self._short_hash}"
            # finally, generate file names.
            self._file_names['events']   = self._game_data_dir / f"{base_file_name}_events.{self._extension}" if exporter_files.events else None
            self._zip_names['events']    = self._game_data_dir / f"{base_file_name}_events.zip" if exporter_files.events else None
            self._file_names['sessions'] = self._game_data_dir / f"{base_file_name}_session-features.{self._extension}" if exporter_files.sessions else None
            self._zip_names['sessions']  = self._game_data_dir / f"{base_file_name}_session-features.zip" if exporter_files.sessions else None
        except Exception as err:
            msg = f"{type(err)} {str(err)}"
            utils.Logger.Log(msg, logging.ERROR)
            traceback.print_tb(err.__traceback__)

    def GetFiles(self) -> Dict[str,Union[IO,None]]:
        return self._files

    def GetPopulationFile(self) -> Union[IO,None]:
        return self._files['population']

    def GetSessionsFile(self) -> Union[IO,None]:
        return self._files['sessions']

    def GetEventsFile(self) -> Union[IO,None]:
        return self._files['events']

    def OpenFiles(self) -> None:
        # self._data_dir.mkdir(exist_ok=True)
        self._game_data_dir.mkdir(exist_ok=True, parents=True)
        # self._base_path.mkdir(exist_ok=True)
        self._files['sessions'] = open(self._file_names['sessions'], "w+", encoding="utf-8") if (self._file_names['sessions'] is not None) else None
        self._files['events']   = open(self._file_names['events'],   "w+", encoding="utf-8") if (self._file_names['events'] is not None) else None

    def CloseFiles(self) -> None:
        if self._files['sessions'] is not None:
            self._files['sessions'].close()
        if self._files['events'] is not None:
            self._files['events'].close()

    def ZipFiles(self) -> None:
        try:
            existing_csvs = utils.loadJSONFile(filename="file_list.json", path=self._data_dir)
        except Exception as err:
            existing_csvs = {}
        # if we have already done this dataset before, rename old zip files
        # (of course, first check if we ever exported this game before).
        if (self._game_id in existing_csvs and self._dataset_id in existing_csvs[self._game_id]):
            src_sessions_f = existing_csvs[self._game_id][self._dataset_id]['sessions']
            src_events_f = existing_csvs[self._game_id][self._dataset_id]['events']
            try:
                if src_sessions_f is not None and self._zip_names['sessions'] is not None:
                    os.rename(src_sessions_f, str(self._zip_names['sessions']))
                if src_events_f is not None and self._zip_names['events'] is not None:
                    os.rename(src_events_f, str(self._zip_names['events']))
            except Exception as err:
                msg = f"Error while setting up zip files! {type(err)} : {err}"
                utils.Logger.Log(msg, logging.ERROR)
                traceback.print_tb(err.__traceback__)
        # for each file, try to save out the csv/tsv to a file - if it's one that should be exported, that is.
        if self._zip_names['sessions'] is not None:
            with zipfile.ZipFile(self._zip_names["sessions"], "w", compression=zipfile.ZIP_DEFLATED) as sessions_zip_file:
                try:
                    session_file = Path(self._dataset_id) / f"{self._dataset_id}_{self._short_hash}_session_features.{self._extension}"
                    readme_file  = Path(self._dataset_id) / "readme.md"
                    self._addToZip(path=self._file_names["sessions"], zip_file=sessions_zip_file, path_in_zip=session_file)
                    self._addToZip(path=self._readme_path,            zip_file=sessions_zip_file, path_in_zip=readme_file)
                    sessions_zip_file.close()
                    if self._file_names["sessions"] is not None:
                        os.remove(self._file_names["sessions"])
                except FileNotFoundError as err:
                    utils.Logger.Log(f"FileNotFoundError Exception: {err}", logging.ERROR)
                    traceback.print_tb(err.__traceback__)
        if self._zip_names['events'] is not None:
            with zipfile.ZipFile(self._zip_names["events"], "w", compression=zipfile.ZIP_DEFLATED) as events_zip_file:
                try:
                    events_file = Path(self._dataset_id) / f"{self._dataset_id}_{self._short_hash}_events.{self._extension}"
                    readme_file = Path(self._dataset_id) / "readme.md"
                    self._addToZip(path=self._file_names["events"], zip_file=events_zip_file, path_in_zip=events_file)
                    self._addToZip(path=self._readme_path,        zip_file=events_zip_file, path_in_zip=readme_file)
                    events_zip_file.close()
                    if self._file_names["events"] is not None:
                        os.remove(self._file_names["events"])
                except FileNotFoundError as err:
                    utils.Logger.Log(f"FileNotFoundError Exception: {err}", logging.ERROR)
                    traceback.print_tb(err.__traceback__)

    def _addToZip(self, path, zip_file, path_in_zip) -> None:
        try:
            zip_file.write(path, path_in_zip)
        except FileNotFoundError as err:
            utils.Logger.Log(str(err), logging.ERROR)
            traceback.print_tb(err.__traceback__)

    ## Public function to write out a tiny metadata file for indexing OGD data files.
    #  Using the paths of the exported files, and given some other variables for
    #  deriving file metadata, this simply outputs a new file_name.meta file.
    #  @param date_range    The range of dates included in the exported data.
    #  @param num_sess      The number of sessions included in the recent export.
    def WriteMetadataFile(self, num_sess:int) -> None:
        # First, ensure we have a data directory.
        try:
            self._game_data_dir.mkdir(exist_ok=True, parents=True)
        except Exception as err:
            msg = f"Could not set up folder {self._game_data_dir}. {type(err)} {str(err)}"
            utils.Logger.toFile(msg, logging.WARNING)
        else:
            # Second, remove old metas, if they exist.
            start_range = self._date_range['min'].strftime("%Y%m%d") if self._date_range['min'] is not None else "Unknown"
            end_range   = self._date_range['max'].strftime("%Y%m%d") if self._date_range['max'] is not None else "Unknown"
            match_string = f"{self._game_id}_{start_range}_to_{end_range}_\\w*\\.meta"
            old_metas = [f for f in os.listdir(self._game_data_dir) if re.match(match_string, f)]
            for old_meta in old_metas:
                try:
                    utils.Logger.Log(f"Removing old meta file, {old_meta}")
                    os.remove(self._game_data_dir / old_meta)
                except Exception as err:
                    msg = f"Could not remove old meta file {old_meta}. {type(err)} {str(err)}"
                    utils.Logger.Log(msg, logging.WARNING)
            # Third, write the new meta file.
            # calculate the path and name of the metadata file, and open/make it.
            meta_file_path : Path = self._game_data_dir/ f"{self._dataset_id}_{self._short_hash}.meta"
            with open(meta_file_path, "w", encoding="utf-8") as meta_file :
                metadata  = \
                {
                    "game_id"      :self._game_id,
                    "dataset_id"   :self._dataset_id,
                    "ogd_revision" :self._short_hash,
                    "sessions_f"   :str(self._zip_names["sessions"]),
                    "events_f"     :str(self._zip_names["events"]),
                    "start_date"   :self._date_range['min'].strftime("%m/%d/%Y") if self._date_range['min'] is not None else "Unknown",
                    "end_date"     :self._date_range['max'].strftime("%m/%d/%Y") if self._date_range['max'] is not None else "Unknown",
                    "date_modified":datetime.now().strftime("%m/%d/%Y"),
                    "sessions"     :num_sess
                }
                meta_file.write(json.dumps(metadata, indent=4))
                meta_file.close()

    ## Public function to update the list of exported files.
    #  Using the paths of the exported files, and given some other variables for
    #  deriving file metadata, this simply updates the JSON file to the latest
    #  list of files.
    #  @param date_range    The range of dates included in the exported data.
    #  @param num_sess      The number of sessions included in the recent export.
    def UpdateFileExportList(self, num_sess: int) -> None:
        self._backupFileExportList()
        existing_csvs = {}
        try:
            existing_csvs = utils.loadJSONFile(filename="file_list.json", path=self._data_dir)
        except FileNotFoundError as err:
            utils.Logger.toFile("file_list.json does not exist.", logging.WARNING)
        except Exception as err:
            msg = f"Could not load file list. {type(err)} {str(err)}"
            utils.Logger.toFile(msg, logging.ERROR)
        finally:
            with open(self._data_dir / "file_list.json", "w") as existing_csv_file:
                utils.Logger.toStdOut(f"opened csv file at {existing_csv_file.name}", logging.INFO)
                if not self._game_id in existing_csvs.keys():
                    existing_csvs[self._game_id] = {}
                # sessions_stat = os.stat(sessions_csv_full_path)
                prior_export = self._dataset_id in existing_csvs[self._game_id].keys()
                sessions_path = str(self._zip_names["sessions"]) if self._zip_names["sessions"] is not None else (existing_csvs[self._game_id][self._dataset_id]["sessions"] if prior_export else None)
                events_path   = str(self._zip_names["events"]) if self._zip_names["events"] is not None else (existing_csvs[self._game_id][self._dataset_id]["events"] if prior_export else None)
                existing_csvs[self._game_id][self._dataset_id] = \
                {
                    "ogd_revision" :self._short_hash,
                    "sessions_f"   :sessions_path,
                    "events_f"     :events_path,
                    "start_date"   :self._date_range['min'].strftime("%m/%d/%Y") if self._date_range['min'] is not None else "Unknown",
                    "end_date"     :self._date_range['max'].strftime("%m/%d/%Y") if self._date_range['max'] is not None else "Unknown",
                    "date_modified":datetime.now().strftime("%m/%d/%Y"),
                    "sessions"     :num_sess
                }
                existing_csv_file.write(json.dumps(existing_csvs, indent=4))

    def _backupFileExportList(self) -> bool:
        try:
            src  : Path = self._data_dir / "file_list.json"
            dest : Path = self._data_dir / "file_list.json.bak"
            if src.exists():
                shutil.copyfile(src=src, dst=dest)
            else:
                utils.Logger.Log(f"Could not back up file_list.json, because it does not exist!", logging.WARN)
        except Exception as err:
            msg = f"{type(err)} {str(err)}"
            utils.Logger.Log(f"Could not back up file_list.json. Got the following error: {msg}", logging.ERROR)
            return False
        else:
            utils.Logger.toStdOut(f"Backed up file_list.json to {dest}", logging.INFO)
            return True
