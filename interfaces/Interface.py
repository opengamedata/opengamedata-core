## import standard libraries
import abc
from typing import Any, Dict

# import local files
from schemas.IDMode import IDMode

class Interface(abc.ABC):

    # *** ABSTRACTS ***

    @abc.abstractmethod
    def _open(self) -> bool:
        pass

    @abc.abstractmethod
    def _close(self) -> bool:
        pass

    # *** BUILT-INS & PROPERTIES ***

    def __init__(self, config:Dict[str,Any]):
        self._config  : Dict[str, Any] = config
        self._is_open : bool = False

    def __del__(self):
        self.Close()

    # *** PUBLIC STATICS ***

    # *** PUBLIC METHODS ***

    def Open(self, force_reopen:bool = False) -> bool:
        if (not self._is_open) or force_reopen:
            self._is_open = self._open()
        return self._is_open
    
    def IsOpen(self) -> bool:
        return True if self._is_open else False

    def Close(self) -> bool:
        if self.IsOpen():
            return self._close()
        else:
            return True

    # *** PROPERTIES ***

    # *** PRIVATE STATICS ***

    # *** PRIVATE METHODS ***
