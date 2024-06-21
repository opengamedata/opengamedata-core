# import libraries
import logging
from datetime import timedelta
from typing import Any, List, Optional
# import locals
from ogd.core.utils.Logger import Logger
from ogd.core.generators.Generator import GeneratorParameters
from ogd.games.AQUALAB.features.PerJobFeature import PerJobFeature
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class JobActiveTime(PerJobFeature):

    def __init__(self, params:GeneratorParameters, job_map:dict):
        super().__init__(params=params, job_map=job_map)
        self._total_time = timedelta(0)
        if self.ExtractionMode == ExtractionMode.PLAYER:
            self._session_id      = None
            self._last_start_time = None
            self._last_event_time = None
            self._last_event_session = None
            self._last_event_name = None
            self._last_event_index = None
            self._last_event_session = None
            self._last_event_name = None
            self._last_event_index = None
        else:
            raise NotImplementedError(f"Got invalid export mode of {self.ExtractionMode.name} in JobActiveTime!")

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["all_events"]
        # if self.ExtractionMode == ExtractionMode.PLAYER \
        # or self.ExtractionMode == ExtractionMode.SESSION:
        #     return ["all_events"]
        # else:
        #     return []

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []
        # if self.ExtractionMode == ExtractionMode.POPULATION:
        #     return ["JobActiveTime"]
        # else:
        #     return []

    def _updateFromEvent(self, event:Event) -> None:
        self._player_id = event.UserID
        if event.SessionID != self._session_id:
            self._handleNewSession(event)

        if event.EventName == "accept_job":
            self._last_start_time = event.timestamp
        elif event.EventName == "switch_job":
            new_job = event.GameState.get('job_name', event.EventData.get('job_name', None))['string_value']
            if new_job is None:
                raise KeyError("Could not find key 'job_name' in GameState or EventData!")
            old_job = event.EventData["prev_job_name"]
            # if we switched into "this" job, this becomes new start time
            if self._job_map.get(new_job, None) == self.CountIndex:
                self._last_start_time = event.Timestamp
                if event.Timestamp is None:
                    self.WarningMessage(f"JobActiveTime received a switch_job event with Timestamp == None!")
            # if we switched out of "this" job, update total time in the job.
            # note, if "this" job is no-active-job, we don't care. Further, if we switched into no-active-job, then we just completed a job and don't care.
            elif self._job_map.get(old_job, None) == self.CountIndex and new_job != "no-active-job" and old_job != "no-active-job":
                self._updateTotalTime()
        elif event.EventName == "complete_job":
            self._updateTotalTime()
        # if we got an event unrelated to job change, but didn't have a start (e.g. new session started mid-job), then make now the start.
        elif self._last_start_time is None:
            self._last_start_time = event.Timestamp
        # if we got an event earlier than last start, we are out of order
        elif self._last_start_time > event.Timestamp:
            self.WarningMessage(f"Got out-of-order events in JobActiveTime; event {event.EventName}:{event.EventSequenceIndex} had timestamp {event.Timestamp} earlier than start event, with time {self._last_start_time}!")
            self._last_start_time = event.Timestamp

        # finally, update latest timestamp
        if self._last_event_time and self._last_event_time > event.Timestamp:
            self.WarningMessage(f"Got out-of-order events in SessionDuration; event {event.EventName}:{event.EventSequenceIndex} had timestamp {event.Timestamp} earlier than end event, with time {self._last_event_time}!")
        else:
            self._last_event_time = event.timestamp
            self._last_event_session = event.SessionID
            self._last_event_name = event.UserID
            self._last_event_index = event.EventSequenceIndex

    def _updateFromFeatureData(self, feature:FeatureData):
        return
        # if self.ExtractionMode == ExtractionMode.PLAYER \
        # or self.ExtractionMode == ExtractionMode.SESSION:
        #     pass
        # elif self.ExtractionMode == ExtractionMode.POPULATION:
        #     self._handle_population(feature=feature)

    def _getFeatureValues(self) -> List[Any]:
        return [self._total_time.total_seconds()]

    def _validateEventCountIndex(self, event:Event):
        ret_val : bool = False

        _current_job = event.GameState.get('job_name', event.EventData.get('job_name', None))['string_value']
        if _current_job is None:
            raise KeyError("Could not find key 'job_name' in GameState or EventData!")
        if self._job_map.get(_current_job, None) is not None:
            if self._job_map.get(_current_job, None) == self.CountIndex:
                    ret_val = True
            elif event.EventName == "switch_job":
                # if we got switch job, and were switching away from this instance's job, we still want to process it.
                old_job = event.EventData["prev_job_name"]
                if self._job_map.get(old_job, None) == self.CountIndex:
                    ret_val = True
        else:
            self.WarningMessage(f"Got invalid job_name data in {type(self).__name__}")

        return ret_val


    # *** Optionally override public functions. ***

    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"

    @staticmethod
    def AvailableModes() -> List[ExtractionMode]:
        return [ExtractionMode.PLAYER]

    # *** PRIVATE METHODS ***

    def _handleNewSession(self, event:Event):
            _old_sess = self._session_id
            self._session_id = event.SessionID
            # if we jumped to a new session, we only want to count time up to last event, then skip the time between sessions to new timestamp;
            # but only if we had a previous session, i.e. this isn't the first event seen.
            if _old_sess is not None:
                # Logger.Log(f"JobActiveTime attempting to update total time for {event.UserID} ({_old_sess} -> {self._session_id}) following change in session, index={event.EventSequenceIndex}", logging.INFO)
                self._updateTotalTime()
                # Logger.Log("Done", logging.INFO)
                if event.app_version == 'Aqualab' or event.app_version == 'None':
                    current_job = event.EventData.get("job_name", {}).get('string_value')
                else:
                    current_job = event.EventData.get("job_name")
                if current_job is not None and self._job_map.get(current_job, None) == self.CountIndex:
                    self._last_start_time = event.Timestamp
                    self._last_event_time = event.Timestamp
                if event.Timestamp is None:
                    Logger.Log(f"JobActiveTime received an initial event with Timestamp == None!", logging.WARN)
            # _old_sess = self._session_id
            # self._session_id = event.SessionID
            # # if we jumped to a new session, we only want to count time up to last event, then skip the time between sessions to new timestamp;
            # # but only if we had a previous session, i.e. this isn't the first event seen.
            # if _old_sess is not None:
            #     # Logger.Log(f"JobActiveTime attempting to update total time for {event.UserID} ({_old_sess} -> {self._session_id}) following change in session, index={event.EventSequenceIndex}", logging.INFO)
            #     self._updateTotalTime()
            #     # Logger.Log("Done", logging.INFO)
            #     self._last_start_time = event.timestamp
            #     if event.Timestamp is None:
            #         self.WarningMessage(f"JobActiveTime received an initial event with Timestamp == None!")

    def _updateTotalTime(self):
        if self._last_start_time:
            if self._last_event_time:
                self._total_time += (self._last_event_time - self._last_start_time)
                self._last_start_time = None
                self._last_event_time = None
            else:
                self.WarningMessage(f"JobActiveTime could not update total time, missing previous event time!")
        elif self.ExtractionMode == ExtractionMode.PLAYER:
            self.WarningMessage(f"JobActiveTime could not update total time for player {self._player_id}, session {self._session_id} missing start time!")

    # def _handle_population(self, feature:FeatureData):
    #     if feature.ExportMode == ExtractionMode.PLAYER:
    #         _val = feature.FeatureValues[0]
    #         if type(_val) == timedelta:
    #             self._total_seconds += _val
    #         else:
    #             Logger.Log(f"JobActiveTime for population got invalid value {_val} of type {type(_val)} for column {feature.FeatureNames[0]}", logging.WARN)
    #     else:
    #         Logger.Log(f"JobActiveTime for population got feature data for mode {feature.ExportMode.name}", logging.DEBUG)
