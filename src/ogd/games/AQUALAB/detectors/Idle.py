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

class Idle(Detector):
    """Template file to serve as a guide for creating custom Feature subclasses for games.

    :param Feature: Base class for a Custom Feature class.
    :type Feature: _type_
    """
    DEFAULT_IDLE_LEVEL : Final[int] = 30


    def __init__(self, params:GeneratorParameters, trigger_callback:Callable[[Event], None], idle_level:Optional[int]):
        super().__init__(params=params, trigger_callback=trigger_callback)
        self._found = False
        self._sess_id = "Unknown"
        self._last_action_time = None
        self._job_name = "Unknown"
        self._idle_level = 0
        self._idle_time: Optional[Union[float, timedelta]] = None
        if idle_level is not None:
            self._idle_threads: timedelta = timedelta(seconds=idle_level)
        else:
            self._idle_threads: timedelta = timedelta(seconds=Idle.DEFAULT_IDLE_LEVEL)

    # *** Implement abstract functions ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        """_summary_

        :return: _description_
        :rtype: List[str]
        """
        return ["all_events"] # >>> fill in names of events this Feature should use for extraction. <<<

    def _updateFromEvent(self, event:Event) -> None:
        """_summary_

        :param event: _description_
        :type event: Event
        """
        if event.EventName == "script_fired" and ("somethingLeft" or "nothingLeft") in event.EventData.get("node_id", ""):
            return
        if self._sess_id == "Unknown":
            self._sess_id = event.SessionID
        elif self._sess_id != event.SessionID:
            self._sess_id = event.SessionID
            self._last_action_time = None
        if not self._last_action_time:
            self._last_action_time = event.Timestamp
            return

        self._idle_time = event.Timestamp - self._last_action_time
        self._last_action_time = event.Timestamp
        if self._idle_time > self._idle_threads:
            self._found = True
            self._idle_time = self._idle_time / timedelta(seconds=1)
            self._idle_level = self._idle_threads / timedelta(seconds=1)
            self._sess_id = event.SessionID
            self._job_name = event.GameState.get('job_name', event.EventData.get('job_name', "JOB NAME NOT FOUND"))['string_value']
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
        _event_data = {
            "level" : self._idle_level,
            "time": self._idle_time,
            "job_name": self._job_name
        }
        ret_val : DetectorEvent = self.GenerateEvent(session_id=self._sess_id, app_id="AQUALAB",
                                                     event_name="Idle", event_data=_event_data)
        return ret_val
