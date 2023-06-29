# import libraries
from os import truncate
from extractors.features.PerCountFeature import PerCountFeature
from schemas import Event
from typing import Any, List, Optional
# import locals
from extractors.features.PerLevelFeature import PerLevelFeature
from extractors.Extractor import ExtractorParameters
from schemas.Event import Event
from schemas.ExtractionMode import ExtractionMode
from schemas.FeatureData import FeatureData

class MaxedPlayerAttribute(PerCountFeature):
    def __init__(self, params:ExtractorParameters):
        PerCountFeature.__init__(self, params=params)
        self._attr_count = 0
        self._ATTRIBUTE_ENUM : List[str] = ["endurance", "resourceful", "tech","social","trust","research"]
        self._attr_name = self._ATTRIBUTE_ENUM[self.CountIndex]


    # *** IMPLEMENT ABSTRACT FUNCTIONS ***
    def _validateEventCountIndex(self, event:Event):
        
        return False
        #return int(event.GameState['att']) == self.CountIndex



    @classmethod
    def _getEventDependencies(cls, mode:ExtractionMode) -> List[str]:
        return [""]

    @classmethod
    def _getFeatureDependencies(cls, mode:ExtractionMode) -> List[str]:
        return ["TopAttribute"]

    def _extractFromEvent(self, event:Event) -> None:
        #self._story_alignment = event.EventData["story_alignment"]

        pass


    def _extractFromFeatureData(self, feature:FeatureData):
        #add logic to make sure that MODE is session, not player so we don't get duplicates
        if(feature._mode == ExtractionMode.SESSION):
            attribute_list = feature._vals[1]
            for attr in attribute_list:
                if(self._ATTRIBUTE_ENUM.index(attr) == self.CountIndex):
                    if(feature._vals[0]>=10):
                        self._attr_count+=1



            
        return

    def _getFeatureValues(self) -> List[Any]:
        return [self._attr_name, self._attr_count]

    # *** Optionally override public functions. ***
    def Subfeatures(self) -> List[str]:
        return ["Count"]
    
    @staticmethod
    def AvailableModes() -> List[ExtractionMode]:
        return [ExtractionMode.POPULATION, ExtractionMode.DETECTOR] # >>> delete any modes you don't want run for your Feature. <<<
    