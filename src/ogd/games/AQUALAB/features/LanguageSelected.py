# import libraries
from typing import Any, List, Optional

from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.extractors.Feature import Feature
from ogd.common.models.Event import Event
from ogd.common.models.enums.ExtractionMode import ExtractionMode
from ogd.common.models.FeatureData import FeatureData
from ogd.common.utils.Logger import Logger
import logging

class LanguageSelected(Feature):
    def __init__(self, params: GeneratorParameters):
        super().__init__(params=params)
        self.session_languages = {}
        self.player_sessions = {}
    
    @classmethod
    def _eventFilter(cls, mode: ExtractionMode) -> List[str]:
        return ["all_events"]

    @classmethod
    def _featureFilter(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _updateFromEvent(self, event: Event) -> None:
        session_id = event.SessionID
        player_id = event.UserID

        if player_id:
            if player_id not in self.player_sessions:
                self.player_sessions[player_id] = [session_id]
            else:
                self.player_sessions[player_id].append(session_id)

        if event.EventName == "select_language":
            language_selected = event.EventData["language"]
            if self.session_languages.get(session_id, None) is None:
                self.session_languages[session_id] = language_selected
            # elif self.session_languages[session_id] != language_selected:
            #     self.session_languages[session_id] = "BOTH"
 
    def _updateFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        player_languages = {}
        for player_id, sessions in self.player_sessions.items():
            session_languages = [self.session_languages.get(session_id, None) for session_id in sessions]
            if "SPANISH" in session_languages and "ENGLISH" in session_languages:
                player_languages[player_id] = "BOTH"
            elif "SPANISH" in session_languages:
                player_languages[player_id] = "SPANISH"
            elif "ENGLISH" in session_languages:
                player_languages[player_id] = "ENGLISH"
            else:
                player_languages[player_id] = "ENGLISH"
        return [player_languages]

    def Subfeatures(self) -> List[str]:
        return []

    @staticmethod
    def MinVersion() -> Optional[str]:
        return "1"
    
    @classmethod
    def AvailableModes(cls) -> List[ExtractionMode]:
        return [ExtractionMode.POPULATION]