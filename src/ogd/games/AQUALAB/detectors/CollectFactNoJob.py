# import standard libraries
from datetime import datetime
from typing import Callable, List

# import local files
from ogd.core.generators.detectors.Detector import Detector
from ogd.core.generators.detectors.DetectorEvent import DetectorEvent
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode

class CollectFactNoJob(Detector):
    """Template file to serve as a guide for creating custom Feature subclasses for games.

    :param Feature: Base class for a Custom Feature class.
    :type Feature: _type_
    """
    def __init__(self, params:GeneratorParameters, trigger_callback:Callable[[Event], None]):
        super().__init__(params=params, trigger_callback=trigger_callback)
        self._found_jobless_fact = False
        self._fact_id = None
        self._current_job = None

    # *** Implement abstract functions ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        """_summary_

        :return: _description_
        :rtype: List[str]
        """
        return ["receive_fact"]

    def _updateFromEvent(self, event:Event) -> None:
        """_summary_

        :param event: _description_
        :type event: Event
        """
        self._current_job = event.GameState.get('job_name', event.EventData.get('job_name', None))['string_value']
        if self._current_job is None:
            raise KeyError("Could not find key 'job_name' in GameState or EventData!")
        if self._current_job == "no-active-job":
            self._found_jobless_fact = True
            self._fact_id = event.EventData['fact_id']
        return

    def _trigger_condition(self) -> bool:
        if self._found_jobless_fact:
            self._found_jobless_fact = False
            return True
        else:
            return False

    def _trigger_event(self) -> DetectorEvent:
        """_summary_

        :return: _description_
        :rtype: List[Any]
        """
        ret_val : DetectorEvent = self.GenerateEvent(app_id="AQUALAB",
                                                     event_name="CollectFactNoJob", event_data={"fact_id":self._fact_id},
                                                     game_state={"job_name":self._current_job})
        return ret_val
