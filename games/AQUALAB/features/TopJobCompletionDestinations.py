# global imports
import json
from collections import defaultdict
from typing import Any, List, Union
# local imports
import utils
from features.Feature import Feature
from features.FeatureData import FeatureData
from schemas.Event import Event

class TopJobCompletionDestinations(Feature):

    def __init__(self, name:str, description:str, job_map:dict):
        self._job_map = job_map
        super().__init__(name=name, description=description, count_index=0)
        self._current_user_code = None
        self._last_completed_id = None
        self._job_complete_pairs = defaultdict(dict)

    # *** Implement abstract functions ***
    def _getEventDependencies(self) -> List[str]:
        return ["accept_job", "complete_job"]

    def _getFeatureDependencies(self) -> List[str]:
        return []

    def _extractFromEvent(self, event:Event) -> None:
        user_code = event.user_id
        job_name = event.event_data["job_name"]["string_value"]

        # in either case, handle event.
        if event.event_name == "complete_job":
            self._last_completed_id = job_name # here, we take what we last completed, and append where we switched to.
        elif event.event_name == "accept_job":
            if user_code == self._current_user_code and self._last_completed_id is not None:
                if not job_name in self._job_complete_pairs[self._last_completed_id].keys():
                    self._job_complete_pairs[self._last_completed_id][job_name] = []

                self._job_complete_pairs[self._last_completed_id][job_name].append(user_code)
                self._last_completed_id = None

        # finally, once we process the event, we know we're looking at data for this event's user.
        self._current_user_code = user_code

    def _extractFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        ret_val = {}

        for src in self._job_complete_pairs.keys():
            dests = sorted(
                self._job_complete_pairs[src].items(),
                key=lambda item: len(item[1]), # sort by length of list of ids.
                reverse=True # sort largest to smallest
            )
            ret_val[src] = {
                item[0]:item[1] for item in dests[0:5]
            }

            utils.Logger.Log(f"For TopJobCompletionDestinations, sorted dests as: {json.dumps(dests)}")

        return [json.dumps(ret_val)]

    # *** Optionally override public functions. ***
    def MinVersion(self) -> Union[str,None]:
        return "1"