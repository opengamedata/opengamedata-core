# import standard libraries
import itertools
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Final, List, Optional
# import OGD files
from ogd.games import AQUALAB
from ogd.games.AQUALAB.detectors import *
from ogd.games.AQUALAB.features import *
from ogd.core.generators.detectors.Detector import Detector
from ogd.core.generators.Generator import GeneratorParameters
from ogd.core.generators.GeneratorLoader import GeneratorLoader
from ogd.core.generators.extractors.Feature import Feature
from ogd.common.models.Event import Event
from ogd.common.models.enums.ExtractionMode import ExtractionMode
from ogd.common.schemas.games.GameSchema import GameSchema
from ogd.common.utils import utils
from ogd.common.utils.Logger import Logger
from . import features

EXPORT_PATH : Final[str] = "games/AQUALAB/DBExport.json"


class AqualabLoader(GeneratorLoader):
    """Loader subclass for Aqualab generators"""

    # *** BUILT-INS & PROPERTIES ***

    ## Constructor for the AqualabLoader class.
    def __init__(self, player_id:str, session_id:str, game_schema: GameSchema, mode:ExtractionMode, feature_overrides:Optional[List[str]]):
        """Constructor for the AqualabLoader class.

        :param player_id: The player ID associated with the feature extractors/event detectors being loaded.
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

        # Load Aqualab jobs export and map job names to integer values
        METADATA = {}
        _dbexport_path = Path(AQUALAB.__file__) if Path(AQUALAB.__file__).is_dir() else Path(AQUALAB.__file__).parent
        with open(_dbexport_path / "DBExport.json", "r") as file:
            METADATA = json.load(file)

        task_num = 1
        for i, job in enumerate(METADATA.get("jobs", {}), start=1):
            self._job_map[job["id"]] = i
            self._diff_map[i] = job["difficulties"]
            for task in job["tasks"]:
                task_by_job = job["id"] + "_" + task["id"]
                self._task_map[task_by_job] = task_num
                task_num += 1

        # Update level count
        self._game_schema._max_level = len(self._job_map) - 1

    @property
    def JobMap(self) -> Dict:
        """Property returning the "job map" that assigns each job in the DBExport an integer value/index.

        :return: The "job map" from the current DBExport
        :rtype: Dict
        """
        return self._job_map

    # *** IMPLEMENT ABSTRACT FUNCTIONS ***

    @staticmethod
    def _getFeaturesModule() -> ModuleType:
        return features

    def _loadFeature(self, feature_type:str, extractor_params:GeneratorParameters, schema_args:Dict[str,Any]) -> Optional[Feature]:
        ret_val : Optional[Feature] = None
        # First run through aggregate features
        if extractor_params._count_index is None:
            match feature_type:
                case "ActiveTime":
                    ret_val = ActiveTime.ActiveTime(params=extractor_params, job_map=self._job_map, active_threads=schema_args.get("Active_threshold"))
                case "ActiveJobs":
                    ret_val = ActiveJobs.ActiveJobs(params=extractor_params, job_map=self._job_map)
                case "AppVersions":
                    ret_val = AppVersions.AppVersions(params=extractor_params)
                case "AverageSessionTime":
                    ret_val = AverageSessionTime.AverageSessionTime(params=extractor_params)
                case "EchoSessionID":
                    ret_val = EchoSessionID.EchoSessionID(params=extractor_params)
                case "EventList":
                    ret_val = EventList.EventList(params=extractor_params)
                case "ExperimentalCondition":
                    ret_val = ExperimentalCondition.ExperimentalCondition(params=extractor_params, job_map=self._job_map)
                case "FinalBestiary":
                    ret_val = FinalBestiary.FinalBestiary(params=extractor_params)
                case "PlayedNonexperimentalVersion":
                    ret_val = PlayedNonexperimentalVersion.PlayedNonexperimentalVersion(params=extractor_params)
                case "JobsCompleted":
                    ret_val = JobsCompleted.JobsCompleted(params=extractor_params)
                case "JobQuitsPerComplete":
                    ret_val = JobQuitsPerComplete.JobQuitsPerComplete(params=extractor_params)
                case "JobPlayTime":
                    ret_val = JobPlayTime.JobPlayTime(params=extractor_params, job_map=self._job_map)
                case "ModelExportCount":
                    ret_val = ModelExportCount.ModelExportCount(params=extractor_params, job_map=self._job_map)
                case "ModelInterveneCount":
                    ret_val = ModelInterveneCount.ModelInterveneCount(params=extractor_params, job_map=self._job_map)
                case "ModelPredictCount":
                    ret_val = ModelPredictCount.ModelPredictCount(params=extractor_params, job_map=self._job_map)
                case "PlayLocations":
                     ret_val = PlayLocations.PlayLocations(params=extractor_params)
                case "PlayerSummary":
                    ret_val = PlayerSummary.PlayerSummary(params=extractor_params)
                case "PopulationSummary":
                    ret_val = PopulationSummary.PopulationSummary(params=extractor_params)
                case "SessionDiveSitesCount":
                    ret_val = SessionDiveSitesCount.SessionDiveSitesCount(params=extractor_params)
                case "SessionDuration":
                    ret_val = SessionDuration.SessionDuration(params=extractor_params, threshold=int(schema_args.get("threshold", 60)))
                case "SessionDurationPerJob":
                    ret_val = SessionDurationPerJob.SessionDuration(params=extractor_params, threshold=int(schema_args.get("threshold", 60)))
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
                case "TotalJobQuits":
                    ret_val = TotalJobQuits.TotalJobQuits(params=extractor_params)
                case "TotalJobRecommendationReceived":
                    ret_val = TotalJobRecommendationReceived.TotalJobRecommendationReceived(params=extractor_params)
                case "TopJobSwitchDestinations":
                    ret_val = TopJobSwitchDestinations.TopJobSwitchDestinations(params=extractor_params, job_map=self._job_map)
                case "TotalArcticTime":
                    ret_val = TotalArcticTime.TotalArcticTime(params=extractor_params)
                case "TotalArgumentationTime":
                    ret_val = TotalArgumentationTime.TotalArgumentationTime(params=extractor_params)
                case "TotalBayouTime":
                    ret_val = TotalBayouTime.TotalBayouTime(params=extractor_params)
                case "TotalCoralTime":
                    ret_val = TotalCoralTime.TotalCoralTime(params=extractor_params)
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
                case "TotalKelpTime":
                    ret_val = TotalKelpTime.TotalKelpTime(params=extractor_params)
                case "TotalModelingTime":
                    ret_val = TotalModelingTime.TotalModelingTime(params=extractor_params)
                case "TotalPlayTime":
                    ret_val = TotalPlayTime.TotalPlayTime(params=extractor_params)
                case "TotalSessionTime":
                    ret_val = TotalSessionTime.TotalSessionTime(params=extractor_params, threshold=int(schema_args.get("threshold", 30)))
                case "TotalPopulationTime":
                    ret_val = TotalPopulationTime.TotalPopulationTime(params=extractor_params, threshold=int(schema_args.get("threshold", 30)))
                case "TotalPlayerTime":
                    ret_val = TotalPlayerTime.TotalPlayerTime(params=extractor_params, threshold=int(schema_args.get("threshold", 30)))
                case "UserAvgActiveTime":
                    ret_val = UserAvgActiveTime.UserAvgActiveTime(params=extractor_params, player_id=self._player_id)
                case "UserAvgSessionDuration":
                    ret_val = UserAvgSessionDuration.UserAvgSessionDuration(params=extractor_params, player_id=self._player_id)
                case "UserTotalSessionDuration":
                    ret_val = UserTotalSessionDuration.UserTotalSessionDuration(params=extractor_params, player_id=self._player_id)
                case "PlayerProgressionJobNodes":
                    ret_val = PlayerProgressionJobNodes.PlayerProgressionJobNodes(params=extractor_params)
                case "PlayerProgressionLinks":
                    ret_val = PlayerProgressionLinks.PlayerProgressionLinks(params=extractor_params)
                case "PopulationJobCompletionProgression":
                    ret_val = PopulationJobCompletionProgression.PopulationJobCompletionProgression(params=extractor_params)
                case "PopulationJobSwitchProgression":
                    ret_val = PopulationJobSwitchProgression.PopulationJobSwitchProgression(params=extractor_params)
                case "LanguageSelected":    
                    ret_val = LanguageSelected.LanguageSelected(params=extractor_params)
                case "PlayerLanguageSelected":
                    ret_val = PlayerLanguageSelected.PlayerLanguageSelected(params=extractor_params)
                case _:
                    Logger.Log(f"'{feature_type}' is not a valid aggregate feature type for Aqualab.")
        # then run through per-count features.
        else:
            match feature_type:
                case "JobActiveTime":
                    ret_val = JobActiveTime.JobActiveTime(params=extractor_params, job_map=self._job_map)
                case "JobArgumentation":
                    ret_val = JobArgumentation.JobArgumentation(params=extractor_params, job_map=self._job_map)
                case "JobArgumentationFails":
                    ret_val = JobArgumentationFails.JobArgumentationFails(params=extractor_params, job_map=self._job_map)
                case "JobArgumentationNoReject":
                    ret_val = JobArgumentationNoReject.JobArgumentationNoReject(params=extractor_params, job_map=self._job_map)
                case "JobArgumentationSuccessRatio":
                    ret_val = JobArgumentationSuccessRatio.JobArgumentationSuccessRatio(params=extractor_params, job_map=self._job_map)
                case "JobArgumentationSuccessRatioPerDifficulty":
                    ret_val = JobArgumentationSuccessRatioPerDifficulty.JobArgumentationSuccessRatioPerDifficulty(params=extractor_params, diff_map=self._diff_map, difficulty_type=schema_args.get("difficulty_type"))
                case "JobArgumentationRejects":
                    ret_val = JobArgumentationRejects.JobArgumentationRejects(params=extractor_params, job_map=self._job_map)
                case "JobTriesInArgument":
                    ret_val = JobTriesInArgument.JobTriesInArgument(params=extractor_params, job_map=self._job_map)
                case "JobTriesInArgumentPerDifficulty":
                    ret_val = JobTriesInArgumentPerDifficulty.JobTriesInArgumentPerDifficulty(params=extractor_params, diff_map=self._diff_map, difficulty_type=schema_args.get("difficulty_type"))
                case "JobTotalAttempts":
                    ret_val = JobTotalAttempts.JobTotalAttempts(params=extractor_params, job_map=self._job_map)
                case "JobInterventionFails":
                    ret_val = JobInterventionFails.JobInterventionFails(params=extractor_params, job_map=self._job_map)
                case "JobTotalHelpCount":
                    ret_val = JobTotalHelpCount.JobTotalHelpCount(params=extractor_params, job_map=self._job_map)
                case "JobAttempted":
                    ret_val = JobAttempted.JobAttempted(params=extractor_params, job_map=self._job_map)
                case "JobComplete":
                    ret_val = JobComplete.JobComplete(params=extractor_params, job_map=self._job_map)
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
                case "JobLocationChangesNoKelp":
                    ret_val = JobLocationChangesNoKelp.JobLocationChangesNoKelp(params=extractor_params, job_map=self._job_map)
                case "JobModeling":
                    ret_val = JobModeling.JobModeling(params=extractor_params, job_map=self._job_map)
                case "JobName":
                    ret_val = JobName.JobName(params=extractor_params, job_map=self._job_map)
                case "JobPriorAttempt":
                    ret_val = JobPriorAttempt.JobPriorAttempt(params=extractor_params, job_map=self._job_map)
                case "JobPriorComplete":
                    ret_val = JobPriorComplete.JobPriorComplete(params=extractor_params, job_map=self._job_map)
                case "JobStarted":
                    ret_val = JobStarted.JobStarted(params=extractor_params, job_map=self._job_map)
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
                case "QuitJob":
                    ret_val = QuitJob.QuitJob(params=extractor_params, job_map=self._job_map)
                case "JobRecommendationReceived":
                    ret_val = JobRecommendationReceived.JobRecommendationReceived(params=extractor_params, job_map=self._job_map)
                case "FollowedAdvice":
                    ret_val = FollowedAdvice.FollowedAdvice(params=extractor_params, job_map=self._job_map)
                case "SuccessfulAdvice":
                    ret_val = SuccessfulAdvice.SuccessfulAdvice(params=extractor_params, job_map=self._job_map)
                case "SurveyCompleted":
                    ret_val = SurveyCompleted.SurveyCompleted(params=extractor_params)
                case "SurveyItemResponse":
                    _target = schema_args.get("target", "NO TARGET CONFIGURED")
                    _retest = schema_args.get("retest", False)
                    ret_val = SurveyItemResponse.SurveyItemResponse(params=extractor_params, target_survey=_target, retest=_retest)
                case _:
                    Logger.Log(f"'{feature_type}' is not a valid per-count feature type for Aqualab.")
        return ret_val

    def _loadDetector(self, detector_type:str, extractor_params:GeneratorParameters, schema_args:Dict[str,Any], trigger_callback:Callable[[Event], None]) -> Optional[Detector]:
        ret_val : Optional[Detector] = None

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
                Logger.Log(f"'{detector_type}' is not a valid detector for Aqualab.")
        return ret_val

# *** PUBLIC STATICS ***

    @staticmethod
    def GetAqualabJobCount(db_export_path:Path=Path(".") / "ogd" / "games" / "AQUALAB") -> int:
        """Function to retrieve the number of jobs in the DBExport file.

        :param db_export_path: A path to the folder containing DBExport, defaults to Path(".")/"ogd"/"games"/"AQUALAB"
        :type db_export_path: Path, optional
        :return: The number of jobs in the current DBExport
        :rtype: int
        """
        ret_val : int
        db_export = utils.loadJSONFile(filename="DBExport.json", path=db_export_path)
        ret_val = len(db_export.get("jobs", []))
        return ret_val

    @staticmethod
    def GetAqualabTaskCount(db_export_path:Path=Path(".") / "ogd" / "games" / "AQUALAB") -> int:
        """Function to retrieve the total number of tasks in the DBExport file.

        :param db_export_path: A path to the folder containing DBExport, defaults to Path(".")/"ogd"/"games"/"AQUALAB"
        :type db_export_path: Path, optional
        :return: The total number of tasks in the current DBExport
        :rtype: int
        """
        db_export = utils.loadJSONFile(filename="DBExport.json", path=db_export_path)
        list_o_lists = [job.get('tasks', []) for job in db_export.get('jobs', [])]
        all_tasks    = list(itertools.chain.from_iterable(list_o_lists))
        return len(all_tasks)
