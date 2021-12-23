from typing import Any, List
import json
import pandas as pd
from extractors.SessionFeature import SessionFeature
from schemas.Event import Event

class FunnelByUser(SessionFeature):
    def __init__(self, name:str, description:str):
        super().__init__(name=name, description=description)
        self._count = 0
        self._level = None
        self._userFunnelDict = dict()

    def GetEventTypes(self) -> List[str]:
        return ["start_level", "puzzle_started", "create_shape", "check_solution", "puzzle_complete"]

    def GetFeatureValues(self) -> List[Any]:
        count = 0
        finalList = []
        listReturn = []
        finalDict = json.loads('{"started": 0, "create_shape": 0, "submitted": 0, "completed": 0}')
        for key in self._userFunnelDict.keys():
            finalList.append((self._userFunnelDict[key]["started"], self._userFunnelDict[key]["create_shape"], self._userFunnelDict[key]["submitted"], self._userFunnelDict[key]["completed"]))
        percent = round((sum([x[3] for x in finalList]) / 30) * 100, 2)
        listReturn.append(percent)
        listReturn.append(sum([x[0] for x in finalList]))
        listReturn.append(sum([x[1] for x in finalList]))
        listReturn.append(sum([x[2] for x in finalList]))
        listReturn.append(sum([x[3] for x in finalList]))
        return listReturn
        
    def Subfeatures(self) -> List[str]:
        return ["started", "create_shape", "submitted", "completed"]

    def _extractFromEvent(self, event:Event) -> None:
        if event.event_name in ["start_level", "puzzle_started"]:
            self._level = event.event_data["task_id"]["string_value"]

            if self._level not in self._userFunnelDict.keys():
                self._userFunnelDict[self._level] = json.loads('{"started": 0, "create_shape": 0, "submitted": 0, "completed": 0}')
                
        if self._level != None:

            if event.event_name == "puzzle_started":
                self._userFunnelDict[self._level]["started"] = 1

            elif event.event_name == "create_shape":
                self._userFunnelDict[self._level]["create_shape"] = 1

            elif event.event_name == "check_solution":
                self._userFunnelDict[self._level]["submitted"] = 1

            elif event.event_name == "puzzle_complete":
                self._userFunnelDict[self._level]["completed"] = 1

