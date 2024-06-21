# import libraries
import json
from typing import Any, List, Optional

# import locals
from ogd.core.generators.extractors.Feature import Feature
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.models.FeatureData import FeatureData

class EventList(Feature):

    def __init__(self, params:GeneratorParameters):
        super().__init__(params=params)
        self._event_list = []

        # Map of event names to primary detail parameter and its type
        self._details_map = {
            "accept_job":                   ("job_name", "string_value"),
            "switch_job":                   ("job_name", "string_value"),
            "receive_fact":                 ("fact_id", "string_value"),
            "receive_entity":               ("entity_id", "string_value"),
            "complete_job":                 ("job_name", "string_value"),
            "complete_task":                ("task_id", "string_value"),
            "scene_changed":                ("scene_name", "string_value"),
            "room_changed":                 ("room_name", "string_value"),
            "begin_dive":                   ("site_id", "string_value"),
            "ask_for_help":                 ("node_id", "string_value"),
            "script_fired":                 ("node_id", "string_value"),
            "bestiary_select_species":      ("species_id", "string_value"),
            "bestiary_select_environment":  ("environment_id", "string_value"),
            "bestiary_select_model":        ("model_id", "string_value"),
            "begin_model":                  ("job_name", "string_value"),
            "model_phase_changed":          ("phase", "string_value"),
            "model_ecosystem_selected":     ("ecosystem", "string_value"),
            "model_concept_started":        ("ecosystem", "string_value"),
            "model_concept_updated":        ("status", "string_value"),
            "model_concept_exported":       ("ecosystem", "string_value"),
            "begin_simulation":             ("job_name", "string_value"),
            "model_sync_error":             ("sync", "int_value"),
            "simulation_sync_achieved":     ("job_name", "string_value"),
            "model_predict_completed":      ("ecosystem", "string_value"),
            "model_intervene_update":       ("difference_value", "int_value"),
            "model_intervene_error":        ("ecosystem", "string_value"),
            "model_intervene_completed":    ("ecosystem", "string_value"),
            "end_model":                    ("phase", "string_value"),
            "purchase_upgrade":             ("item_name", "string_value"),
            "insufficient_funds":           ("item_name", "string_value"),
            "add_environment":              ("environment", "string_value"),
            "remove_environment":           ("environment", "string_value"),
            "add_critter":                  ("critter", "string_value"),
            "remove_critter":               ("critter", "string_value"),
            "begin_experiment":             ("tank_type", "string_value"),
            "end_experiment":               ("tank_type", "string_value"),
            "begin_argument":               ("job_name", "string_value"),
            "fact_submitted":               ("fact_id", "string_value"),
            "fact_rejected":                ("fact_id", "string_value"),
            "leave_argument":               ("job_name", "string_value"),
            "complete_argument":            ("job_name", "string_value")
        }

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
    def _eventFilter(cls, mode:ExtractionMode) -> List[str]:
        return ["all_events"]

    @classmethod
    def _featureFilter(cls, mode:ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event:Event) -> None:
        if event.UserID:
            next_event = {
                "name": event.EventName,
                "user_id": event.UserID,
                "session_id": event.SessionID,
                "timestamp": event.Timestamp.isoformat(),
                "job_name": event.GameState.get('job_name', event.EventData.get('job_name', "UNDEFINED"))['string_value'],
                "index": event.EventSequenceIndex,
                "event_primary_detail": None
            }

            if event.EventName == "scene_changed":
                next_event['scene_name'] = event.EventData['scene_name']

            if event.EventName in self._details_map:
                param_name = self._details_map[event.EventName][0]

                try:
                    next_event["event_primary_detail"] = event.EventData[param_name]
                except KeyError as err:
                    raise KeyError(f"Event of type {event.EventName} did not have parameter {param_name}, valid parameters are {event.EventData.keys()}")

            self._event_list.append(next_event)

    def _updateFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [json.dumps(self._event_list)]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
