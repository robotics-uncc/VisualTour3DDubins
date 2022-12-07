from enum import IntEnum


class SolverType(IntEnum):
    UNKNOWN = 0
    TWO_D = 1
    THREE_D = 2
    THREE_D_TSP_FIRST = 3
    THREE_D_MODIFIED_DISTANCE = 4
