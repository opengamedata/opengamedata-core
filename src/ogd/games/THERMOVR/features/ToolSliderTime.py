from typing import Any, Dict, List

from ogd.core.extractors.Extractor import ExtractorParameters
from ogd.core.extractors.features.SessionFeature import SessionFeature
from ogd.core.schemas.Event import Event
from ogd.core.schemas.ExtractionMode import ExtractionMode
from ogd.core.schemas.FeatureData import FeatureData

class ToolSliderTime(SessionFeature):

    def __init__(self, params: ExtractorParameters, player_id: str):
        self._slider_start_time = {}
        self._slider_times = {}
        super().__init__(params=params)

    @classmethod
    def _getEventDependencies(cls, mode: ExtractionMode) -> List[str]:
        return ["grab_tool_slider", "release_tool_slider"]

    @classmethod
    def _getFeatureDependencies(cls, mode: ExtractionMode) -> List[str]:
        return []

    def _extractFromEvent(self, event: Event) -> None:
        if event.EventType == "grab_tool_slider":
            tool_name = event.EventData["tool_name"]
            self._slider_start_time[tool_name] = event.Timestamp
        elif event.EventType == "release_tool_slider":
            tool_name = event.EventData["tool_name"]
            if tool_name in self._slider_start_time:
                start_time = self._slider_start_time[tool_name]
                end_time = event.Timestamp
                slider_time = end_time - start_time
                if tool_name in self._slider_times:
                    self._slider_times[tool_name].append(slider_time)
                else:
                    self._slider_times[tool_name] = [slider_time]

    def _extractFromFeatureData(self, feature: FeatureData):
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self._slider_times]
