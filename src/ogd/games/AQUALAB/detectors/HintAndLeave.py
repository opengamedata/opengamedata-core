# import standard libraries
from datetime import datetime, timedelta
from typing import Callable, Final, List, Optional, Union
# import local files
from ogd.core.generators.detectors.Detector import Detector
from ogd.core.generators.detectors.DetectorEvent import DetectorEvent
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.utils.typing import Map


class HintAndLeave(Detector):
    """Template file to serve as a guide for creating custom Feature subclasses for games.

    :param Feature: Base class for a Custom Feature class.
    :type Feature: _type_
    """
    DEFAULT_THRESHOLD : Final[int] = 5


    def __init__(self, params:GeneratorParameters, trigger_callback:Callable[[Event], None], time_threshold:Optional[int]):
        super().__init__(params=params, trigger_callback=trigger_callback)
        self._found = False
        self._sess_id             : str = "Unknown"
        self._scene               : str = "Unknown"
        self._job_name            : str = "Unknown"
        self._hint                : str = "Unknown"
        self._last_hint_time      : Optional[datetime] = None
        self._time_spent          : Optional[Union[timedelta, float]] = None
        self._detector_event_data : Map = {}
        self._threshold           : timedelta
        if time_threshold is not None:
            self._threshold = timedelta(seconds=time_threshold)
        else:
            self._threshold = timedelta(seconds=HintAndLeave.DEFAULT_THRESHOLD)

    # *** Implement abstract functions ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        """_summary_

        :return: _description_
        :rtype: List[str]
        """
        return ["ask_for_help", "scene_changed", "room_changed"] # >>> fill in names of events this Feature should use for extraction. <<<

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

        if event.EventName == "ask_for_help":
            self._last_hint_time = event.Timestamp
            self._job_name = event.GameState.get('job_name', event.EventData.get('job_name', None))['string_value']
            self._hint = event.EventData.get("node_id", "NODE NOT FOUND")
            return

        if not self._last_hint_time:
            return
        self._time_spent = event.Timestamp - self._last_hint_time
        self._last_hint_time = None

        if self._time_spent <= self._threshold:
            self._found = True
            self._time_spent = self._time_spent / timedelta(seconds=1)
            self._sess_id = event.SessionID
            self._sequence_index = event.EventSequenceIndex
            if event.EventName == "scene_changed":
                self._scene = event.EventData.get("scene_name", "SCENE NOT FOUND")
                self._detector_event_data = {
                    "time": self._time_spent,
                    "level": self._threshold / timedelta(seconds=1),
                    "scene": self._scene,
                    "job_name": self._job_name,
                    "hint_node": self._hint
                }
            else:
                self._room = event.EventData.get("room_name")
                self._detector_event_data = {
                    "time": self._time_spent,
                    "level": self._threshold / timedelta(seconds=1),
                    "room": self._room,
                    "job_name": self._job_name,
                    "hint_node": self._hint
                }
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
                                                    event_name="HintAndLeave", event_data=self._detector_event_data,
                                                    event_sequence_index=self._sequence_index)
        return ret_val
