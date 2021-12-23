from typing import Any, List
import json
import pandas as pd
from extractors.SessionFeature import SessionFeature
from schemas.Event import Event

orderMapping = {'1. One Box': 1, '2. Separated Boxes': 2, '3. Rotate a Pyramid': 3, '4. Match Silhouettes': 4, '5. Removing Objects': 5, '6. Stretch a Ramp': 6, '7. Max 2 Boxes': 7, '8. Combine 2 Ramps': 8, '9. Scaling Round Objects': 9,
                'Square Cross-Sections': 10, 'Bird Fez': 11, 'Pi Henge': 12, '45-Degree Rotations': 13,  'Pyramids are Strange': 14, 'Boxes Obscure Spheres': 15, 'Object Limits': 16, 'Warm Up': 17, 'Angled Silhouette': 18,
                'Sugar Cones': 19,'Stranger Shapes': 20, 'Tall and Small': 21, 'Ramp Up and Can It': 22, 'More Than Meets Your Eye': 23, 'Not Bird': 24, 'Unnecesary': 25, 'Zzz': 26, 'Bull Market': 27, 'Few Clues': 28, 'Orange Dance': 29, 'Bear Market': 30}
listPuzzles = list(orderMapping.keys())

class SequenceBetweenPuzzles(SessionFeature):
    def __init__(self, name:str, description:str):
        super().__init__(name=name, description=description)
        self._numPuzzles = 1
        self._currentPuzzle = {}
        self._activePuzzle = None
        self._userPuzzleDict = dict()

    def GetEventTypes(self) -> List[str]:
        return ["start_level", "puzzle_started", "create_shape", "check_solution", "puzzle_complete", "disconnect", "login_user", "exit_to_menu"]

    def GetFeatureValues(self) -> List[Any]:
        listReturn = []
        listReturn.append(self._numPuzzles - 1)
        emptyList = []
        for puzzle in listPuzzles:
            if puzzle in self._userPuzzleDict.keys():
                listReturn.append(self._userPuzzleDict[puzzle])
            else:
                listReturn.append(emptyList)
        return listReturn
        
    def Subfeatures(self) -> List[str]:
        return listPuzzles

    def _extractFromEvent(self, event:Event) -> None:
        ignoreEvent = False
        
        if event.event_name == "start_level":
            self._activePuzzle = event.event_data["task_id"]["string_value"]
            
            if self._activePuzzle == "Sandbox":
                ignoreEvent = True
            
            if ignoreEvent == False:
                if self._activePuzzle not in self._userPuzzleDict.keys():
                    self._userPuzzleDict[self._activePuzzle] = []
                self._currentPuzzle = {}
                self._currentPuzzle["sequence"] = self._numPuzzles
                self._currentPuzzle["funnel"] = "No data"

        if self._activePuzzle == "Sandbox":
            ignoreEvent = True
            
        if ignoreEvent == False:
        
            if event.event_name == "puzzle_started":
                self._currentPuzzle["funnel"] = "started"

            elif event.event_name == "create_shape":
                self._currentPuzzle["funnel"] = "shape_created"

            elif event.event_name == "check_solution":
                self._currentPuzzle["funnel"] = "submitted"

            elif event.event_name == "puzzle_complete":
                self._currentPuzzle["funnel"] = "completed"

            elif event.event_name in ["disconnect", "login_user", "exit_to_menu"] and self._activePuzzle != None:
                #Add current data
                self._userPuzzleDict[self._activePuzzle].append(json.dumps(self._currentPuzzle))
                self._currentPuzzle = {}
                self._numPuzzles += 1

