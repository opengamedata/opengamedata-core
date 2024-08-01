"""IDMode Module
"""

# import standard libraries
from enum import IntEnum

class IDMode(IntEnum):
    """Enum representing the different kinds of IDs in OpenGameData.

    Namely:

    * Session IDs
    * User IDs (or Player IDs)
    * App IDs (or Game IDs)

    :param IntEnum: _description_
    :type IntEnum: _type_
    :return: _description_
    :rtype: _type_
    """
    SESSION = 1
    USER = 2
    GAME = 3

    def __str__(self):
        return self.name
