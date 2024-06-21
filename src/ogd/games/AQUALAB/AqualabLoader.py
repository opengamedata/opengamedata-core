# import standard libraries
import itertools
import json
from pathlib import Path
from typing import Any, Callable, Dict, Final, List, Optional
# import local files
from . import features
from ogd.games import AQUALAB
from ogd.core.generators.detectors.Detector import Detector
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.GeneratorLoader import GeneratorLoader
from ogd.core.generators.extractors.Feature import Feature
from ogd.games.AQUALAB.detectors import *
from ogd.games.AQUALAB.features import *
from ogd.core.models.Event import Event
from ogd.core.models.enums.ExtractionMode import ExtractionMode
from ogd.core.schemas.games.GameSchema import GameSchema
from ogd.core.utils.utils import loadJSONFile

EXPORT_PATH : Final[str] = "games/AQUALAB/DBExport.json"

## @class AqualabLoader
#  Extractor subclass for extracting features from Aqualab game data.
class AqualabLoader(GeneratorLoader):

    # *** BUILT-INS & PROPERTIES ***

    ## Constructor for the AqualabLoader class.
    def __init__(self, player_id:str, session_id:str, game_schema: GameSchema, mode:ExtractionMode, feature_overrides:Optional[List[str]]):
        """Constructor for the AqualabLoader class.

        :param player_id: _description_
        :type player_id: str
        :param session_id: The id number for the session whose data is being processed by this instance
        :type session_id: str
        :param game_schema: A data structure containing information on how the game events and other data are structured
        :type game_schema: GameSchema
        :param feature_overrides: A list of features to export, overriding the default of exporting all enabled features.
        :type feature_overrides: Optional[List[str]]
        """
        super().__init__(player_id=player_id, session_id=session_id, game_schema=game_schema, mode=mode, feature_overrides=feature_overrides)
        self._job_map = {"no-active-job": 0}
        self._diff_map = {0: {"experimentation": 0, "modeling": 0, "argumentation": 0} }
        self._task_map = {}
        data = None

        # Load Aqualab jobs export and map job names to integer values
        _dbexport_path = Path(AQUALAB.__file__) if Path(AQUALAB.__file__).is_dir() else Path(AQUALAB.__file__).parent
        with open(_dbexport_path / "DBExport.json", "r") as file:
            export = json.load(file)

            task_num = 1
            for i, job in enumerate(export["jobs"], start=1):
                self._job_map[job["id"]] = i
                self._diff_map[i] = job["difficulties"]
                for task in job["tasks"]:
                    task_by_job = job["id"] + "_" + task["id"]
                    self._task_map[task_by_job] = task_num
                    task_num += 1

        # Update level count
        self._game_schema._max_level = len(self._job_map) - 1

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    @staticmethod
    def _getFeaturesModule():
        return features

    def _loadFeature(self, feature_type:str, extractor_params:GeneratorParameters, schema_args:Dict[str,Any]) -> Feature:
        ret_val : Feature
        # First run through aggregate features
        if extractor_params._count_index == None:
            match feature_type:
                case "ActiveTime":
                    ret_val = ActiveTime.ActiveTime(params=extractor_params, job_map=self._job_map, active_threads=schema_args.get("Active_threshold"))
                case "ActiveJobs":
                    ret_val = ActiveJobs.ActiveJobs(params=extractor_params, job_map=self._job_map)
                case "AppVersions":
                    ret_val = AppVersions.AppVersions(params=extractor_params)
                case "EchoSessionID":
                    ret_val = EchoSessionID.EchoSessionID(params=extractor_params)
                case "EventList":
                    ret_val = EventList.EventList(params=extractor_params)
                case "JobsCompleted":
                    ret_val = JobsCompleted.JobsCompleted(params=extractor_params, player_id=self._player_id)
                case "JobTriesInArgument":
                    ret_val = JobTriesInArgument.JobTriesInArgument(params=extractor_params, job_map=self._job_map)
                case "ModelExportCount":
                    ret_val = ModelExportCount.ModelExportCount(params=extractor_params, job_map=self._job_map)
                case "ModelInterveneCount":
                    ret_val = ModelInterveneCount.ModelInterveneCount(params=extractor_params, job_map=self._job_map)
                case "ModelPredictCount":
                    ret_val = ModelPredictCount.ModelPredictCount(params=extractor_params, job_map=self._job_map)
                # case "PlayLocations":
                #     ret_val = PlayLocations.PlayLocations(params=extractor_params)
                case "PlayerSummary":
                    ret_val = PlayerSummary.PlayerSummary(params=extractor_params)
                case "PopulationSummary":
                    ret_val = PopulationSummary.PopulationSummary(params=extractor_params)
                case "SessionDiveSitesCount":
                    ret_val = SessionDiveSitesCount.SessionDiveSitesCount(params=extractor_params)
                case "SessionDuration":
                    ret_val = SessionDuration.SessionDuration(params=extractor_params, threshold=int(schema_args.get("threshold", 60)))
                case "SessionGuideCount":
                    ret_val = SessionGuideCount.SessionGuideCount(params=extractor_params)
                case "SessionHelpCount":
                    ret_val = SessionHelpCount.SessionHelpCount(params=extractor_params)
                case "SessionID":
                    ret_val = SessionID.SessionID(params=extractor_params, session_id=self._session_id)
                case "SessionJobsCompleted":
                    ret_val = SessionJobsCompleted.SessionJobsCompleted(params=extractor_params)
                case "SwitchJobsCount":
                    ret_val = SwitchJobsCount.SwitchJobsCount(params=extractor_params)
                case "TankRulesCount":
                    ret_val = TankRulesCount.TankRulesCount(params=extractor_params)
                case "TopJobCompletionDestinations":
                    ret_val = TopJobCompletionDestinations.TopJobCompletionDestinations(params=extractor_params, job_map=self._job_map)
                case "TopJobSwitchDestinations":
                    ret_val = TopJobSwitchDestinations.TopJobSwitchDestinations(params=extractor_params, job_map=self._job_map)
                case "TotalArgumentationTime":
                    ret_val = TotalArgumentationTime.TotalArgumentationTime(params=extractor_params)
                case "TotalDiveTime":
                    ret_val = TotalDiveTime.TotalDiveTime(params=extractor_params)
                case "TotalExperimentationTime":
                    ret_val = TotalExperimentationTime.TotalExperimentationTime(params=extractor_params)
                case "TimeInJournal":
                    ret_val = TimeInJournal.TimeInJournal(params=extractor_params)
                case "TotalGuideCount":
                    ret_val = TotalGuideCount.TotalGuideCount(params=extractor_params)
                case "TotalHelpCount":
                    ret_val = TotalHelpCount.TotalHelpCount(params=extractor_params)
                case "TotalModelingTime":
                    ret_val = TotalModelingTime.TotalModelingTime(params=extractor_params)
                case "TotalPlayTime":
                    ret_val = TotalPlayTime.TotalPlayTime(params=extractor_params)
                case "UserAvgActiveTime":
                    ret_val = UserAvgActiveTime.UserAvgActiveTime(params=extractor_params, player_id=self._player_id)
                case "UserAvgSessionDuration":
                    ret_val = UserAvgSessionDuration.UserAvgSessionDuration(params=extractor_params, player_id=self._player_id)
                case "UserTotalSessionDuration":
                    ret_val = UserTotalSessionDuration.UserTotalSessionDuration(params=extractor_params, player_id=self._player_id)
                case _:
                    raise NotImplementedError(f"'{feature_type}' is not a valid aggregate feature type for Aqualab.")
        # then run through per-count features.
        else:
            match feature_type:
                case "JobActiveTime":
                    ret_val = JobActiveTime.JobActiveTime(params=extractor_params, job_map=self._job_map)
                case "JobArgumentation":
                    ret_val = JobArgumentation.JobArgumentation(params=extractor_params, job_map=self._job_map)
                case "JobCompletionTime":
                    ret_val = JobCompletionTime.JobCompletionTime(params=extractor_params, job_map=self._job_map)
                case "JobDiveSitesCount":
                    ret_val = JobDiveSitesCount.JobDiveSitesCount(params=extractor_params, job_map=self._job_map)
                case "JobDiveTime":
                    ret_val = JobDiveTime.JobDiveTime(params=extractor_params, job_map=self._job_map)
                case "JobExperimentation":
                    ret_val = JobExperimentation.JobExperimentation(params=extractor_params, job_map=self._job_map)
                case "JobGuideCount":
                    ret_val = JobGuideCount.JobGuideCount(params=extractor_params, job_map=self._job_map)
                case "JobHelpCount":
                    ret_val = JobHelpCount.JobHelpCount(params=extractor_params, job_map=self._job_map)
                case "JobLocationChanges":
                    ret_val = JobLocationChanges.JobLocationChanges(params=extractor_params, job_map=self._job_map)
                case "JobLocationChangeNoKelp":
                    ret_val = JobLocationChangesNoKelp.JobLocationChangesNoKelp(params=extractor_params, job_map=self._job_map)
                case "JobModeling":
                    ret_val = JobModeling.JobModeling(params=extractor_params, job_map=self._job_map)
                case "JobPriorAttempt":
                    ret_val = JobPriorAttempt.JobPriorAttempt(params=extractor_params, job_map=self._job_map)
                case "JobPriorComplete":
                    ret_val = JobPriorComplete.JobPriorComplete(params=extractor_params, job_map=self._job_map)
                case "JobStartCount":
                    ret_val = JobStartCount.JobStartCount(params=extractor_params, job_map=self._job_map)
                case "JobTasksCompleted":
                    ret_val = JobTasksCompleted.JobTasksCompleted(params=extractor_params, job_map=self._job_map)
                case "JobsAttempted":
                    ret_val = JobsAttempted.JobsAttempted(params=extractor_params, job_map=self._job_map, diff_map=self._diff_map)
                case "RegionName":
                    ret_val = RegionName.RegionName(params=extractor_params)
                case "RegionJobCount":
                    ret_val = RegionJobCount.RegionJobCount(params=extractor_params)
                case "SyncCompletionTime":
                    ret_val = SyncCompletionTime.SyncCompletionTime(params=extractor_params)
                case _:
                    raise NotImplementedError(f"'{feature_type}' is not a valid per-count feature type for Aqualab.")
        return ret_val

    def _loadDetector(self, detector_type:str, extractor_params:GeneratorParameters, schema_args:Dict[str,Any], trigger_callback:Callable[[Event], None]) -> Detector:
        ret_val : Detector
        match detector_type:
            case "CollectFactNoJob":
                ret_val = CollectFactNoJob.CollectFactNoJob(params=extractor_params, trigger_callback=trigger_callback)
            case "DiveSiteNoEvidence":
                ret_val = DiveSiteNoEvidence.DiveSiteNoEvidence(params=extractor_params, trigger_callback=trigger_callback, threshold=schema_args['threshold'])
            case "EchoRoomChange":
                ret_val = EchoRoomChange.EchoRoomChange(params=extractor_params, trigger_callback=trigger_callback)
            case "Idle":
                ret_val = Idle.Idle(params=extractor_params, trigger_callback=trigger_callback, idle_level=schema_args.get("idle_level"))
            case "SceneChangeFrequently":
                ret_val = SceneChangeFrequently.SceneChangeFrequently(params=extractor_params, trigger_callback=trigger_callback, time_threshold=schema_args.get("threshold"))
            case "HintAndLeave":
                ret_val = HintAndLeave.HintAndLeave(params=extractor_params, trigger_callback=trigger_callback, time_threshold=schema_args.get("threshold"))
            case "TwoHints":
                ret_val = TwoHints.TwoHints(params=extractor_params, trigger_callback=trigger_callback, time_threshold=schema_args.get("threshold"))
            case _:
                raise NotImplementedError(f"'{detector_type}' is not a valid detector for Aqualab.")
        return ret_val

    @property
    def JobMap(self) -> Dict:
        return self._job_map

    @staticmethod
    def GetAqualabJobCount(db_export_path:Path=Path(".") / "ogd" / "games" / "AQUALAB"):
        db_export = loadJSONFile(filename="DBExport.json", path=db_export_path)
        return len(db_export.get("jobs", []))

    @staticmethod
    def GetAqualabTaskCount(db_export_path:Path=Path(".") / "ogd" / "games" / "AQUALAB"):
        db_export = loadJSONFile(filename="DBExport.json", path=db_export_path)
        list_o_lists = [job.get('tasks', []) for job in db_export.get('jobs', [])]
        # jobs_to_task_cts = [f"{job.get('id')}: {len(job.get('tasks', []))}" for job in db_export.get('jobs', [])]
        # Logger.Log(f"Task counts by job:\n{jobs_to_task_cts}", logging.DEBUG)
        all_tasks    = list(itertools.chain.from_iterable(list_o_lists))
        return len(all_tasks)
