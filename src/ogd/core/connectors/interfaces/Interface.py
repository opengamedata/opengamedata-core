"""DataInterface Module
"""
## import standard libraries
import abc
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

# import local files
from ogd.core.connectors.StorageConnector import StorageConnector
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.schemas.configs.GameSourceSchema import GameSourceSchema
from ogd.core.utils.Logger import Logger

class Interface(StorageConnector):
    """Base class for all connectors that serve as an interface to some IO resource.

    All subclasses must implement the `_availableIDs`, `_availableDates`, `_IDsFromDates`, and `_datesFromIDs` functions.
    """

    # *** ABSTRACTS ***

    @abc.abstractmethod
    def _availableIDs(self, mode:IDMode=IDMode.SESSION) -> List[str]:
        """Private implementation of the logic to retrieve all IDs of given mode from the connected storage.

        :param mode: The type of ID to be listed.
        :type mode: IDMode
        :return: A list of IDs with given mode available through the connected storage.
        :rtype: List[str]
        """
        pass

    @abc.abstractmethod
    def _availableDates(self) -> Dict[str,datetime]:
        """Private implementation of the logic to retrieve the full range of dates/times from the connected storage.

        :return: A dict mapping `min` and `max` to the minimum and maximum datetimes
        :rtype: Dict[str,datetime]
        """
        pass

    @abc.abstractmethod
    def _IDsFromDates(self, min:datetime, max:datetime, mode:IDMode=IDMode.SESSION) -> List[str]:
        """Private implementation of logic to list IDs of given mode that have data within a range of dates.

        :param min: Earliest date in the range
        :type min: datetime
        :param max: Latest date in the range
        :type max: datetime
        :return: A list of IDs of given mode with data falling within the given date range.
        :rtype: Optional[List[str]]
        """
        pass

    @abc.abstractmethod
    def _datesFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION) -> Dict[str,datetime]:
        """Private implementation of the logic to get a range of dates covering all data for given list of IDs (with given mode).

        :param id_list: The list of IDs, for whose data we want a date range.
        :type id_list: List[str]
        :param id_mode: The kind of ID to use when interpreting the `id_list`, defaults to IDMode.SESSION
        :type id_mode: IDMode, optional
        :return: A dictionary mapping `min` and `max` to the range of dates covering all data for the given IDs
        :rtype: Union[Dict[str,datetime], Dict[str,None]]
        """
        pass

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, config:GameSourceSchema):
        super().__init__(config=config)

    def __del__(self):
        self.Close()

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def AvailableIDs(self, mode:IDMode=IDMode.SESSION) -> Optional[List[str]]:
        """Retrieve all IDs of given mode from the connected storage.

        :param mode: The type of ID to be listed.
        :type mode: IDMode
        :return: A list of IDs with given mode available through the connected storage.
        :rtype: List[str]
        """
        ret_val = None
        if self.IsOpen:
            ret_val = self._availableIDs(mode=mode)
        else:
            Logger.Log(f"Can't retrieve list of all {mode} IDs, the storage connection is not open!", logging.WARNING, depth=3)
        return ret_val

    def AvailableDates(self) -> Union[Dict[str,datetime], Dict[str,None]]:
        """Retrieve the full range of dates/times covered by data in the connected storage.

        :return: A dictionary mapping `min` and `max` to the min and max datetimes, or to None (if unavailable)
        :rtype: Union[Dict[str,datetime], Dict[str,None]]
        """
        ret_val = {'min':None, 'max':None}
        if self.IsOpen:
            ret_val = self._availableDates()
        else:
            Logger.Log("Could not get full date range, the storage connection is not open!", logging.WARNING, depth=3)
        return ret_val

    def IDsFromDates(self, min:datetime, max:datetime, mode:IDMode=IDMode.SESSION) -> Optional[List[str]]:
        """Get a list of IDs of given mode that have data within a range of dates.

        :param min: Earliest date in the range
        :type min: datetime
        :param max: Latest date in the range
        :type max: datetime
        :return: A list of IDs of given mode with data falling within the given date range.
        :rtype: Optional[List[str]]
        """
        ret_val = None
        if not self.IsOpen:
            str_min, str_max = min.strftime("%Y%m%d"), max.strftime("%Y%m%d")
            Logger.Log(f"Could not retrieve IDs for {str_min}-{str_max}, the source interface is not open!", logging.WARNING, depth=3)
        else:
            ret_val = self._IDsFromDates(min=min, max=max, mode=mode)
        return ret_val

    def DatesFromIDs(self, id_list:List[str], id_mode:IDMode=IDMode.SESSION) -> Union[Dict[str,datetime], Dict[str,None]]:
        """Get a range of dates covering all data for given list of IDs (with given mode).

        :param id_list: The list of IDs, for whose data we want a date range.
        :type id_list: List[str]
        :param id_mode: The kind of ID to use when interpreting the `id_list`, defaults to IDMode.SESSION
        :type id_mode: IDMode, optional
        :return: A dictionary mapping `min` and `max` to the range of dates covering all data for the given IDs
        :rtype: Union[Dict[str,datetime], Dict[str,None]]
        """
        ret_val = {'min':None, 'max':None}
        if not self.IsOpen:
            Logger.Log(f"Could not retrieve date range {len(id_list)} session IDs, the source interface is not open!", logging.WARNING, depth=3)
        else:
            Logger.Log(f"Retrieving date range from IDs with {id_mode.name} ID mode.", logging.DEBUG, depth=3)
            ret_val = self._datesFromIDs(id_list=id_list, id_mode=id_mode)
        return ret_val

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
