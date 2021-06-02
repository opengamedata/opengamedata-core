# import standard libraries
import logging
import os
import typing
from typing import Dict, List, Union
# import local files
import utils

## @class GameSchema
#  A fairly simple class that reads a JSON schema with information on how a given
#  game's data is structured in the database, and the features we want to extract
#  for that game.
#  The class includes several functions for easy access to the various parts of
#  this schema data.
class GameSchema:
    ## Constructor for the GameSchema class.
    #  Given a path and filename, it loads the data from a JSON schema,
    #  storing the full schema into a private variable, and compiling a list of
    #  all features to be extracted.
    #
    #  @param schema_name The name of the JSON schema file
    #                     (if .json is not the file extension, .json will be appended)
    #  @param schema_path Path to the folder containing the JSON schema file
    #                     (if the path does not end in "/", a "/" will be appended)
    def __init__(self, schema_name:str, schema_path:str = os.path.dirname(__file__) + "/JSON/"):
        # define instance vars
        self._schema:       Dict = {}
        self._feature_list: Union[List,None] = None
        # set instance vars
        if not schema_name.lower().endswith(".json"):
            schema_name += ".json"
        if not schema_path.endswith("/"):
            schema_path += "/"
        self._schema = utils.loadJSONFile(schema_name, schema_path)
        if self._schema is None:
            utils.Logger.Log(f"Could not find event_data_complex schemas at {schema_path}{schema_name}", logging.ERROR)
        else:
            self._feature_list = list(self._schema["features"]["perlevel"].keys()) \
                               + list(self._schema["features"]["per_custom_count"].keys()) \
                               + list(self._schema["features"]["aggregate"].keys())

    def __getitem__(self, key):
        return self._schema[key]

    def level_range(self) -> Dict:
        return self["level_range"]

    ## Function to retrieve the dictionary of event types for the game.
    def events(self) -> Dict:
        return self["events"]

    ## Function to retrieve the names of all event types for the game.
    def event_types(self):
        return self["events"].keys()

    ## Function to retrieve the dictionary of categorized features to extract.
    def features(self) -> Dict:
        return self["features"]

    ## Function to retrieve the dictionary of per-level features.
    def perlevel_features(self) -> Dict:
        return self["features"]["perlevel"]

    ## Function to retrieve the dictionary of per-custom-count features.
    def percount_features(self) -> Dict:
        return self["features"]["per_custom_count"]

    ## Function to retrieve the dictionary of aggregate features.
    def aggregate_features(self) -> Dict:
        return self["features"]["aggregate"]

    ## Function to retrieve the compiled list of all feature names.
    def feature_list(self) -> Union[List, None]:
        return self._feature_list

    ## Function to retrieve the dictionary of database columns.
    def db_columns_with_types(self) -> Dict:
        return self["db_columns"]

    ## Function to retrieve the names of all database columns.
    def db_columns(self):
        return self["db_columns"].keys()