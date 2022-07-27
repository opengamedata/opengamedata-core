# import libraries
import json
from typing import Any, List, Optional

# import locals
from extractors.features.Feature import Feature
from extractors.Extractor import ExtractorParameters
from schemas.Event import Event
from schemas.FeatureData import FeatureData

class EventList(Feature):

    def __init__(self, params:ExtractorParameters):
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
    def _getEventDependencies(cls) -> List[str]:
        return ["all_events"]

    @classmethod
    def _getFeatureDependencies(cls) -> List[str]:
        return []

    def _extractFromEvent(self, event:Event) -> None:
        if event.UserID:
            next_event = {
                "name": event.EventName,
                "user_id": event.UserID,
                "session_id": event.SessionID,
                "timestamp": event.Timestamp.isoformat(),
                "job_name": event.EventData["job_name"]["string_value"],
                "index": event.EventSequenceIndex,
                "event_primary_detail": None
            }

            if event.EventName == "scene_changed":
                next_event['scene_name'] = event.EventData['scene_name']['string_value']

            if event.EventName in self._details_map:
                param_name = self._details_map[event.EventName][0]
                param_type = self._details_map[event.EventName][1]

                try:
                    next_event["event_primary_detail"] = event.EventData[param_name][param_type]
                except KeyError as err:
                    raise KeyError(f"Event of type {event.EventName} did not have parameter {param_name}, valid parameters are {event.EventData.keys()}")

            self._event_list.append(next_event)

    def _extractFromFeatureData(self, feature:FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [json.dumps(self._event_list)]

    # *** Optionally override public functions. ***
    @staticmethod
    def MinVersion(self) -> Optional[str]:
        return "1"
