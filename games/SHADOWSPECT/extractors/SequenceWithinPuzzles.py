from typing import Any, List
import json
import pandas as pd
import numpy as np
from extractors.SessionFeature import SessionFeature
from schemas.Event import Event

orderMapping = {'1. One Box': 1, '2. Separated Boxes': 2, '3. Rotate a Pyramid': 3, '4. Match Silhouettes': 4, '5. Removing Objects': 5, '6. Stretch a Ramp': 6, '7. Max 2 Boxes': 7, '8. Combine 2 Ramps': 8, '9. Scaling Round Objects': 9,
                'Square Cross-Sections': 10, 'Bird Fez': 11, 'Pi Henge': 12, '45-Degree Rotations': 13,  'Pyramids are Strange': 14, 'Boxes Obscure Spheres': 15, 'Object Limits': 16, 'Warm Up': 17, 'Angled Silhouette': 18,
                'Sugar Cones': 19,'Stranger Shapes': 20, 'Tall and Small': 21, 'Ramp Up and Can It': 22, 'More Than Meets Your Eye': 23, 'Not Bird': 24, 'Unnecesary': 25, 'Zzz': 26, 'Bull Market': 27, 'Few Clues': 28, 'Orange Dance': 29, 'Bear Market': 30}
listPuzzles = list(orderMapping.keys())

eventsWithMetadata = ["create_shape", "delete_shape", "rotate_shape", "scale_shape", "move_shape"]
selectedEvents = ["start_level", "create_shape", "delete_shape", "rotate_shape", "scale_shape", "move_shape", "check_solution", "puzzle_complete", "rotate_view", "undo_action", "redo_action", "snapshot"]
#undoableActions = ["create_shape", "delete_shape", "rotate_shape", "scale_shape", "move_shape", "select_shape", "deselect_shape", #"select_shape_add", "rotate_view", "mode_change", "palette_change", "paint", "toogle_snapshot_display"]

class SequenceWithinPuzzles(SessionFeature):
    def __init__(self, name:str, description:str):
        super().__init__(name=name, description=description)
        self._numPuzzles = 1
        self._currentPuzzle = []
        self._activePuzzle = None
        self._prevEvent = None
        self._prevCheck = False
        self._dictFigures = {}
        self._userPuzzleDict = dict()

    def GetEventTypes(self) -> List[str]:
        return ["start_level", "puzzle_started", "create_shape", "delete_shape", "rotate_shape", "scale_shape", "move_shape", "check_solution", "puzzle_complete", "rotate_view", "undo_action", "redo_action", "snapshot", "disconnect","login_user", "exit_to_menu"]

    def GetFeatureValues(self) -> List[Any]:
        listReturn = []
        listReturn.append(self._numPuzzles - 1)
        emptyList = {}
        for puzzle in listPuzzles:
            if puzzle in self._userPuzzleDict.keys():
                listReturn.append(json.dumps(self._userPuzzleDict[puzzle]))
            else:
                listReturn.append(emptyList)
        return listReturn
        
    def Subfeatures(self) -> List[str]:
        return listPuzzles

    def _extractFromEvent(self, event:Event) -> None:
        appendEvent = False
        ignoreEvent = False
        currentEvent = {}
        currentEvent["type"] = event.event_name
        currentEvent["n_times"] = 1
        currentEvent["metadata"] = {}
        currentEvent["action_index"] = [np.nan]
        
        if (self._prevCheck == True):
            if (event.event_name == "puzzle_complete"):
                self._prevEvent["metadata"]["correct"] = True
            else:
                self._prevEvent["metadata"]["correct"] = False
            
            self._prevCheck = False
                
                
        if event.event_name == "start_level":
            self._activePuzzle = event.event_data["task_id"]["string_value"]
            
            if self._activePuzzle == "Sandbox":
                ignoreEvent = True
            
            if ignoreEvent == False:
                if self._activePuzzle not in self._userPuzzleDict.keys():
                    self._userPuzzleDict[self._activePuzzle] = {}
                #self._currentPuzzle = {}
                #self._currentPuzzle["sequence"] = self._numPuzzles
                #self._currentPuzzle["funnel"] = "No data"
        elif event.event_name not in ["login_user", "puzzle_started"]:
            currentEvent["action_index"] = [event.event_data["actionIndex"]["int_value"]]

        if self._activePuzzle == "Sandbox":
            ignoreEvent = True
            
        if ignoreEvent == False:
        
            if event.event_name == "check_solution":
                self._prevCheck = True
                appendEvent = False
            
            elif event.event_name == "create_shape":
                shape_id = event.event_data["objSerialization"]["int_value"]
                shape_type = event.event_data["shapeType"]["int_value"]
                self._dictFigures[shape_id] = shape_type
                currentEvent["metadata"]["shape_id"] = shape_id
                currentEvent["metadata"]["shape_type"] = shape_type
            
            # Should be allowed for one or more objects, but until now we will treat this case as one single object, int
            elif event.event_name in ["delete_shape", "move_shape"]:
                if event.event_name == "delete_shape":
                    shape_id = event.event_data["deletedShapes"]["int_value"]
                else:
                    shape_id = event.event_data["selectedObjects"]["int_value"]
                shape_type = self._dictFigures.get(shape_id)
                if shape_type == None:
                    self._dictFigures[shape_id] = shape_type
                currentEvent["metadata"]["shape_id"] = shape_id
                currentEvent["metadata"]["shape_type"] = shape_type
                
            elif event.event_name in ["rotate_shape", "scale_shape"]:
                shape_id = event.event_data["selectedObject"]["int_value"]
                shape_type = self._dictFigures.get(shape_id)
                if shape_type == None:
                    self._dictFigures[shape_id] = shape_type
                currentEvent["metadata"]["shape_id"] = shape_id
                currentEvent["metadata"]["shape_type"] = shape_type
            
            elif event.event_name in ["undo_action", "redo_action"]:
            
                currentEvent["metadata"]["targeted_actionIndex"] = event.event_data["targetedActionIndex"]["int_value"]
                
                
                    
            #if (appendEvent == True):
            #    self._currentPuzzle.append(json.dumps(currentEvent))
            
            if self._prevEvent != None:
                if event.event_name == self._prevEvent["type"]:
                    if event.event_name in eventsWithMetadata:
                        if currentEvent["metadata"]["shape_id"] != self._prevEvent["metadata"]["shape_id"]:
                            if (self._prevEvent["type"] in selectedEvents):
                                self._currentPuzzle.append(json.dumps(self._prevEvent))
                        else:
                            currentEvent["action_index"].extend(self._prevEvent["action_index"])
                            currentEvent["n_times"] = self._prevEvent["n_times"]
                            currentEvent["n_times"] += 1
                            
                    elif event.event_name in ["check_solution", "undo_action", "redo_action"]:
                        if (self._prevEvent["type"] in selectedEvents):
                            self._currentPuzzle.append(json.dumps(self._prevEvent))
                    else:
                        currentEvent["action_index"].extend(self._prevEvent["action_index"])
                        currentEvent["n_times"] = self._prevEvent["n_times"]
                        currentEvent["n_times"] += 1
                        
                else:
                    if (self._prevEvent["type"] in selectedEvents):
                        self._currentPuzzle.append(json.dumps(self._prevEvent))
            
            
            
            if event.event_name in ["disconnect", "login_user", "exit_to_menu"] and self._activePuzzle != None:
                #Add current data
                key = "Attempt" + str(self._numPuzzles)
                self._userPuzzleDict[self._activePuzzle][key] = self._currentPuzzle
                self._currentPuzzle = []
                self._dictFigures = {}
                self._numPuzzles += 1
            
            self._prevEvent = currentEvent

