# import libraries
import json
import logging
from collections import defaultdict
from typing import Any, List, Optional
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class TopJobSwitchDestinations(Feature):

    def __init__(self, params:GeneratorParameters, job_map:dict):
        self._job_map = job_map
        super().__init__(params=params)
        self._current_user_code = None
        self._last_started_id = None
        self._job_switch_pairs = defaultdict(dict)

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["accept_job", "switch_job"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event:Event) -> None:
        _job_name = event.GameState.get('job_name', event.EventData.get('job_name', None))['string_value']
        if _job_name is None:
            raise KeyError("Could not find key 'job_name' in GameState or EventData!")
        if self._validate_job(_job_name):
            user_code = event.UserID

            if event.EventName == "accept_job":
                self._last_started_id = _job_name
            elif event.EventName == "switch_job":
                if user_code == self._current_user_code and self._last_started_id is not None and self._last_started_id != _job_name and _job_name != "no-active-job":
                    if not _job_name in self._job_switch_pairs[self._last_started_id].keys():
                        self._job_switch_pairs[self._last_started_id][_job_name] = []

                    self._job_switch_pairs[self._last_started_id][_job_name].append(user_code) # here, we take what we switched to, and append where we switched from

                self._last_started_id = _job_name

            # once we process the event, we know we're looking at data for this event's user next time.
            self._current_user_code = user_code

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        ret_val = {}

        for src in self._job_switch_pairs.keys():
            dests = sorted(
                self._job_switch_pairs[src].items(),
                key=lambda item: len(item[1]), # sort by length of list of ids.
                reverse=True # sort largest to smallest
            )
            ret_val[src] = {
                item[0]:item[1] for item in dests[0:5]
            }
            # Logger.Log(f"For TopJobSwitchDestinations, sorted dests as: {json.dumps(dests)}")

        # TODO: figure out if we really need to dump to string, or if we can assume things get stringified as needed elsewhere.
        return [json.dumps(ret_val)]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"

    # *** Other local functions
    def _validate_job(self, job_data):
        ret_val : bool = False
        if job_data and job_data in self._job_map:
            ret_val = True
        else:
            self.WarningMessage(f"Got invalid job_name data in JobsAttempted")
        return ret_val
