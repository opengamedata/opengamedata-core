import logging
from datetime import timedelta
from multiprocessing.sharedctypes import Value
from typing import Any, List

from extractors.Extractor import ExtractorParameters
from extractors.features.SessionFeature import SessionFeature
from schemas.Event import Event
from schemas.FeatureData import FeatureData
from schemas.ExtractionMode import ExtractionMode
from utils import Logger

class PlayerSummary(SessionFeature):

    def __init__(self, params:ExtractorParameters):
        super().__init__(params=params)
        self._summary = {}

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    @classmethod
def _getEventDependencies(cls, mode:ExtractionMode) -> List[str]:
        return []

    @classmethod
def _getEventDependencies(cls, mode:ExtractionMode) -> List[str]:
        return ["JobsCompleted", "SessionDuration", "SessionID"]

    def _extractFromEvent(self, event:Event) -> None:
        return

    def _extractFromFeatureData(self, feature:FeatureData):
        user_id = feature.PlayerID

        if user_id not in self._summary:
            self._summary[user_id] = {
                "active_time": 0,
                "jobs_completed": [],
                "sessions": [],
                "num_sessions": 0
            }

        if feature.ExportMode == ExtractionMode.PLAYER:
            if feature.FeatureType == "JobsCompleted":
                self._summary[user_id]["jobs_completed"] = feature.FeatureValues[0]
            elif feature.FeatureType == "SessionDuration":
                if type(feature.FeatureValues[0]) == timedelta:
                    self._summary[user_id]["active_time"] += feature.FeatureValues[0].seconds
                elif type(feature.FeatureValues[0]) == str and feature.FeatureValues[0] == "No events":
                    pass
                else:
                    raise ValueError(f"PlayerSummary got {feature.Name} feature with value {feature.FeatureValues[0]} of non-timedelta type {type(feature.FeatureValues[0])} in the {feature.FeatureNames[0]} column!")
        elif feature.ExportMode == ExtractionMode.SESSION:
            if feature.FeatureType == "SessionID":
                self._summary[user_id]["sessions"].append(feature.FeatureValues[0])

    def _getFeatureValues(self) -> List[Any]:
        for summary in self._summary.values():
            summary['num_sessions'] = len(set(summary['sessions']))
        return [self._summary]

    # *** Optionally override public functions. ***

    @staticmethod
    def AvailableModes() -> List[ExtractionMode]:
        """List of ExtractionMode supported by the Feature.

        Overridden from base Feature version.
        A PlayerSummary is only used at player and population levels; not concerned with session-level.
        :return: _description_
        :rtype: List[ExtractionMode]
        """
        return [ExtractionMode.POPULATION, ExtractionMode.PLAYER]
