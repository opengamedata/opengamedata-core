## import standard libraries
import abc
from enum import IntEnum
from typing import Dict, List, Tuple, Optional

# import local files
from coding.Code import Code
from coding.Coder import Coder
from ogd.core.connectors.interfaces.Interface import Interface
from ogd.core.models.enums.IDMode import IDMode
from ogd.core.utils.Logger import Logger

class CodingInterface(Interface):

    # *** ABSTRACTS ***

    @abc.abstractmethod
    def _allCoders(self) -> Optional[List[Coder]]:
        pass

    @abc.abstractmethod
    def _createCoder(self, coder_name:str) -> bool:
        pass

    @abc.abstractmethod
    def _getCodeWordsByGame(self, game_id:str) -> Optional[List[str]]:
        pass

    @abc.abstractmethod
    def _getCodeWordsByCoder(self, coder_id:str) -> Optional[List[str]]:
        pass

    @abc.abstractmethod
    def _getCodeWordsBySession(self, session_id:str) -> Optional[List[str]]:
        pass

    @abc.abstractmethod
    def _getCodesByGame(self, game_id:str) -> Optional[List[Code]]:
        pass

    @abc.abstractmethod
    def _getCodesByCoder(self, coder_id:str) -> Optional[List[Code]]:
        pass

    @abc.abstractmethod
    def _getCodesBySession(self, session_id:str) -> Optional[List[Code]]:
        pass

    @abc.abstractmethod
    def _createCode(self, code:str, coder_id:str, events:List[Code.EventID], notes:Optional[str]=None) -> bool:
        pass

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self):
        super().__init__()

    def __del__(self):
        self.Close()

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def AllCoders(self) -> Optional[List[Coder]]:
        ret_val = None
        if self.IsOpen:
            ret_val = self._allCoders()
        else:
            Logger.Log("Can't retrieve list of all Coders, the source interface is not open!")
        return ret_val

    def CreateCoder(self, coder_name:str) -> bool:
        ret_val = False
        if self.IsOpen:
            ret_val = self._createCoder(coder_name=coder_name)
        else:
            Logger.Log("Can't create Coder, the source interface is not open!")
        return ret_val

    def GetCodes(self, mode:IDMode, id:str):
        match mode:
            case IDMode.GAME:
                self._getCodesByGame(game_id=id)
            case IDMode.USER:
                self._getCodesByCoder(coder_id=id)
            case IDMode.SESSION:
                self._getCodesBySession(session_id=id)
            case _:
                raise NotImplementedError(f"The given retrieval mode '{mode}' is not supported for retrieving codes!")

    def GetCodeWords(self, mode:IDMode, id:str):
        match mode:
            case IDMode.GAME:
                self._getCodeWordsByGame(game_id=id)
            case IDMode.USER:
                self._getCodeWordsByCoder(coder_id=id)
            case IDMode.SESSION:
                self._getCodeWordsBySession(session_id=id)
            case _:
                raise NotImplementedError(f"The given retrieval mode '{mode}' is not supported for retrieving code words!")

    def CreateCode(self, code:str, coder_id:str, events:List[Code.EventID], notes:Optional[str]=None) -> bool:
        ret_val = False
        if self.IsOpen:
            ret_val = self._createCode(code=code, coder_id=coder_id, events=events, notes=notes)
        else:
            Logger.Log("Can't create Code, the source interface is not open!")
        return ret_val

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
