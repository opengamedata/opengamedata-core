# import standard libraries
from datetime import datetime, timedelta
from time import time
from typing import Callable, Final, List, Optional, Union
# import local files
from ogd.core.generators.detectors.Detector import Detector
from ogd.core.generators.detectors.DetectorEvent import DetectorEvent
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.utils.typing import Map


class TwoHints(Detector):
    """Template file to serve as a guide for creating custom Feature subclasses for games.

    :param Feature: Base class for a Custom Feature class.
    :type Feature: _type_
    """
    DEFAULT_THRESOLD : Final[int] = 5


    def __init__(self, params:GeneratorParameters, trigger_callback:Callable[[Event], None], time_threshold:Optional[int]):
        super().__init__(params=params, trigger_callback=trigger_callback)
        self._found = False
        self._sess_id = "Unknown"
        self._job_name = "Unknown"
        self._last_hint = "Unknown"
        self._this_hint = "Unknown"
        self._last_hint_time:Optional[datetime] = None
        self._time_spent: Optional[Union[timedelta, float]] = None
        self._detector_event_data: Map = {"job_name": self._job_name}
        self._threshold : timedelta
        if time_threshold is not None:
            self._threshold = timedelta(seconds=time_threshold)
        else:
            self._threshold = timedelta(seconds=TwoHints.DEFAULT_THRESOLD)

    # *** Implement abstract functions ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        """_summary_

        :return: _description_
        :rtype: List[str]
        """
        return ["ask_for_help"] # >>> fill in names of events this Feature should use for extraction. <<<

    def _updateFromEvent(self, event:Event) -> None:
        """_summary_

        :param event: _description_
        :type event: Event
        """
        if self._sess_id == "Unknown":
            self._sess_id = event.SessionID
        elif self._sess_id != event.SessionID:
            self._sess_id = event.SessionID
            self._last_hint_time = None
        
        if not self._last_hint_time:
            self._last_hint_time = event.Timestamp
            self._last_hint = event.EventData.get("node_id")
            return
        
        self._time_spent = event.Timestamp - self._last_hint_time

        if self._time_spent <= self._threshold:
            self._found = True
            self._time_spent = self._time_spent / timedelta(seconds=1)
            self._sess_id = event.SessionID

            self._job_name = event.GameState.get('job_name', event.EventData.get('job_name', "JOB NAME NOT FOUND"))['string_value']
            self._this_hint = event.EventData.get("node_id")
            self._detector_event_data = {
                "time": self._time_spent,
                "level": self._threshold / timedelta(seconds=1),
                "job_name": self._job_name,
                "last_hint_node": self._last_hint,
                "this_hint_node": self._this_hint
            }

        self._last_hint_time = event.Timestamp
        self._last_hint = self._this_hint
        return

    def _trigger_condition(self) -> bool:
        if self._found:
            self._found = False
            return True
        else:
            return False

    def _trigger_event(self) -> DetectorEvent:
        """_summary_

        :return: _description_
        :rtype: List[Any]
        """
        ret_val: DetectorEvent = self.GenerateEvent(session_id=self._sess_id, app_id="AQUALAB",
                                                    event_name="TwoHints", event_data=self._detector_event_data)
        return ret_val
