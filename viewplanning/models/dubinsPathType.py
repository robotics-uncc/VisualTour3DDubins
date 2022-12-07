from enum import IntEnum


class DubinsPathType(IntEnum):
    UNKNOWN = 0
    LSL = 1
    LSR = 2
    RSL = 3
    RSR = 4
    LRL = 5
    RLR = 6
    RLSL = 7
    RLSR = 8
    LRSL = 9
    LRSR = 10
    LSLR = 13
    LSRL = 14
    RSLR = 15
    RSRL = 16

    @staticmethod
    def fromString(string: str):
        string = string.upper()
        for name, member in DubinsPathType.__members__.items():
            if name == string:
                return member
        return DubinsPathType.UNKNOWN.name
