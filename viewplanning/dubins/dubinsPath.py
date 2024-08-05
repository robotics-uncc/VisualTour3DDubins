from typing import Tuple
from viewplanning.models import DubinsPathType, Edge2D
from viewplanning.models.vertex import Vertex2D
from math import nan, inf, cos, sin, sqrt, pi, atan2, isnan, acos, floor


PATH_COMPARE_TOLERANCE = 1e-6
POSSIBLE_A_ZERO = 1e-6
HEADING_ALMOST_ZERO = 1e-6
DEFAULT_DUBINS = (nan, nan, nan, inf, 0)


class DubinsPath(object):
    '''
    Calculates Dubins paths
    '''

    def calculatePath(self, x0, y0, h0, x1, y1, h1, r, **kwargs):
        '''
        Calcualte the Dubins path between [x0, y0, h0] and [x1, y1, h1] with turn radius r

        Parameters
        ----------
        x0: float
            starting x position
        y0: float
            starting y position
        h0: float
            starting heading angle
        x1: float
            ending x position
        y1: float
            ending y position
        h1: float
            ending heading angle
        r: float
            turn radius

        Returns
        -------
        Edge2D
            Dubins path between two positions
        '''
        x, y, h = self._normalize(x0, y0, h0, x1, y1, h1, r)
        m_cth = cos(h)
        m_sth = sin(h)

        results = [
            list(self._solveLSL(x, y, h, m_cth, m_sth)),
            list(self._solveLSR(x, y, h, m_cth, m_sth)),
            list(self._solveRSL(x, y, h, m_cth, m_sth)),
            list(self._solveRSR(x, y, h, m_cth, m_sth)),
            list(self._solveLRL(x, y, h)),
            list(self._solveRLR(x, y, h))
        ]

        # transform back to r = r
        for result in results:
            result[0] *= r
            result[1] *= r
            result[2] *= r
            result[3] *= r
        results.sort(key=lambda x: x[3])
        return Edge2D(
            Vertex2D(x=x0, y=y0, theta=h0),
            Vertex2D(x=x1, y=y1, theta=h1),
            aParam=results[0][0],
            bParam=results[0][1],
            cParam=results[0][2],
            cost=results[0][3],
            pathType=results[0][4],
            radius=r
        )

    def solveType(self, x0, y0, h0, x1, y1, h1, r, pathType):
        x, y, h = self._normalize(x0, y0, h0, x1, y1, h1, r)
        m_cth = cos(h)
        m_sth = sin(h)
        result = DEFAULT_DUBINS
        if pathType == DubinsPathType.LSL:
            result = self._solveLSL(x, y, h, m_cth, m_sth)
        elif pathType == DubinsPathType.LSR:
            result = self._solveLSR(x, y, h, m_cth, m_sth)
        elif pathType == DubinsPathType.RSL:
            result = self._solveRSL(x, y, h, m_cth, m_sth)
        elif pathType == DubinsPathType.RSR:
            result = self._solveRSR(x, y, h, m_cth, m_sth)
        elif pathType == DubinsPathType.LRL:
            result = self._solveLRL(x, y, h)
        elif pathType == DubinsPathType.RLR:
            result = self._solveRLR(x, y, h)
        result = list(result)
        result[0] *= r
        result[1] *= r
        result[2] *= r
        result[3] *= r
        return Edge2D(
            Vertex2D(x=x0, y=y0, theta=h0),
            Vertex2D(x=x1, y=y1, theta=h1),
            aParam=result[0],
            bParam=result[1],
            cParam=result[2],
            cost=result[3],
            pathType=result[4],
            radius=r
        )

    def _normalize(self, x0, y0, h0, x1, y1, h1, r):
        # transform to (0, 0, 0) with r = 1
        x = (x1 - x0) / r
        y = (y1 - y0) / r
        x, y = x * cos(h0) + y * sin(h0), -x * sin(h0) + y * cos(h0)
        h = mod(h1 - h0, 2 * pi)
        return x, y, h

    def _solveLSL(self, x: float, y: float, h: float, m_cth: float, m_sth: float) -> 'Tuple[float, float, float, float, int]':
        r = DEFAULT_DUBINS
        b = (x - m_sth) * (x - m_sth) + (y + m_cth - 1.0) * (y + m_cth - 1.0)
        if b > 0:
            b = sqrt(b)
        else:
            return r
        a = atan2(y + m_cth - 1.0, x - m_sth)

        # check to see if a is nan
        if isnan(a):
            return r

        # make sure a > 0
        while a < 0:
            a += pi

        # 2 solutions on 0, 2pi
        for a in [a, a + pi]:
            c = mod(h - a, 2 * pi)
            newEnd = self._getEndpointBSB(a, b, c, 1, 1, 1)
            if self._compareVector(newEnd, [x, y, h]) == 0:
                r = (a, b, c, a + b + c, DubinsPathType.LSL)
        return r

    def _solveLSR(self, x: float, y: float, h: float, m_cth: float, m_sth: float) -> 'Tuple[float, float, float, float, int]':
        r = DEFAULT_DUBINS
        b = (x + m_sth) * (x + m_sth) + (y - m_cth - 1) * (y - m_cth - 1) - 4
        if b > 0:
            b = sqrt(b)
        else:
            return r
        a = atan2(2 * (x + m_sth) + b * (y - m_cth - 1), b * (x + m_sth) - 2 * (y - m_cth - 1))

        # check to see if a is nan
        if isnan(a):
            return r

        # make sure a > 0
        while a < 0:
            a += pi

        # 2 solutions on 0, 2pi
        for a in [a, a + pi]:
            c = mod(a - h, 2.0 * pi)

            # ensure endpoint is going to correct point
            newEnd = self._getEndpointBSB(a, b, c, 1, 1, -1)
            if self._compareVector(newEnd, [x, y, h]) == 0:
                r = (a, b, c, a + b + c, DubinsPathType.LSR)

        return r

    def _solveRSL(self, x: float, y: float, h: float, m_cth: float, m_sth: float) -> 'Tuple[float, float, float, float, int]':
        r = DEFAULT_DUBINS
        b = (x - m_sth) * (x - m_sth) + (y + m_cth + 1) * (y + m_cth + 1) - 4
        if b > 0:
            b = sqrt(b)
        else:
            return r
        a = atan2(2 * (x - m_sth) - b * (y + m_cth + 1), b * (x - m_sth) + 2 * (y + m_cth + 1))

        # check to see if a is nan
        if isnan(a):
            return r

        # make sure a > 0
        while a < 0:
            a += pi

        # 2 solutions on 0, 2pi
        for a in [a, a + pi]:
            c = mod(a + h, 2.0 * pi)

            # ensure endpoint is going to correct point
            newEnd = self._getEndpointBSB(a, b, c, -1, 1, 1)
            if self._compareVector(newEnd, [x, y, h]) == 0:
                r = (a, b, c, a + b + c, DubinsPathType.RSL)

        # no correct points return default
        return r

    def _solveRSR(self, x: float, y: float, h: float, m_cth: float, m_sth: float) -> 'Tuple[float, float, float, float, int]': 
        r = DEFAULT_DUBINS
        b = (x + m_sth) * (x + m_sth) + (y - m_cth + 1.0) * (y - m_cth + 1.0)
        if b > 0:
            b = sqrt(b)
        else:
            return r
        a = atan2(m_cth - y - 1, x + m_sth)

        # check to see if a is nan
        if isnan(a):
            return r

        # make sure a > 0
        while a < 0:
            a += pi

        # 2 solutions on 0, 2pi
        for a in [a, a + pi]:
            if abs(a) < POSSIBLE_A_ZERO:
                if abs(h) < HEADING_ALMOST_ZERO:
                    c = 0  # straight line
                else:
                    c = 2 * pi - h
            else:
                # heading angle > 2pi
                # check if turn 1 has good heading angle
                h_cw = 2 * pi - mod(h,  2 * pi)
                if a >= h_cw:
                    c = h_cw + 2 * pi - a
                else:
                    c = 2 * pi - h - a

            # ensure endpoint is going to correct point
            newEnd = self._getEndpointBSB(a, b, c, -1, 1, -1)
            if self._compareVector(newEnd, [x, y, h]) == 0:
                r = a, b, c, a + b + c, DubinsPathType.RSR

        # no correct points return default
        return r

    def _solveRLR(self, x, y, h):
        possibleB = []
        v = (x + sin(h)) / 2
        w = (-y - 1 + cos(h)) / 2
        t = 1 - (v ** 2 + w ** 2) / 2
        r = DEFAULT_DUBINS
        if t < -1 or t > 1:
            return r
        possibleB.append(acos(t))

        possibleB[0] = possibleB[0] if possibleB[0] >= 0 else -possibleB[0]
        possibleB.append(2 * pi - possibleB[0])
        for b in possibleB:
            A = (v ** 2 - w ** 2) / (2 * (1 - cos(b)))
            B = v * w / (1 - cos(b))
            a = .5 * atan2(B * cos(b) + A * sin(b), A * cos(b) - B * sin(b))

            # a is nan skip current b value
            if isnan(a):
                continue

            while a < 0:
                a += pi / 2

            # 4 possible a values
            possibleA = [
                mod(a, 2 * pi),
                mod(a + pi / 2, 2 * pi),
                mod(a + pi, 2 * pi),
                mod(a + 3 * pi / 2, 2 * pi)
            ]
            for a in possibleA:
                c = mod(b - a - h, 2 * pi)
                # check for valid point
                newEnd = self._getEndpointBBB(a, b, c, -1, 1, -1)
                # check for valid a b and c values
                if self._compareVector(newEnd, [x, y, h]) == 0 and max(a, c) < b and min(a, c) < b + pi:
                    r = a, b, c, a + b + c, DubinsPathType.RLR

        return r

    def _solveLRL(self, x, y, h):
        possibleB = []
        v = (x - sin(h)) / 2
        w = (y - 1 + cos(h)) / 2
        t = 1 - (v ** 2 + w ** 2) / 2
        r = DEFAULT_DUBINS
        if t < -1 or t > 1:
            return r
        possibleB.append(acos(t))

        possibleB[0] = possibleB[0] if possibleB[0] >= 0 else -possibleB[0]
        possibleB.append(2 * pi - possibleB[0])
        for b in possibleB:
            A = (v ** 2 - w ** 2) / (2 * (1 - cos(b)))
            B = v * w / (1 - cos(b))
            a = .5 * atan2(B * cos(b) + A * sin(b), A * cos(b) - B * sin(b))

            # a is nan skip current b value
            if isnan(a):
                continue

            while a < 0:
                a += pi / 2

            # 4 possible a values
            possibleA = [
                mod(a, 2 * pi),
                mod(a + pi / 2, 2 * pi),
                mod(a + pi, 2 * pi),
                mod(a + 3 * pi / 2, 2 * pi)
            ]
            for a in possibleA:
                c = mod(b - a + h, 2 * pi)
                # check for valid point
                newEnd = self._getEndpointBBB(a, b, c, 1, -1, 1)
                # check for valid a b and c values
                if self._compareVector(newEnd, [x, y, h]) == 0 and max(a, c) < b and min(a, c) < b + pi:
                    r = a, b, c, a + b + c, DubinsPathType.LRL
        # no solution found
        return r

    def _compareVector(self, a: 'list[float]', b: 'list[float]') -> int:
        result = 0
        for i in range(len(a)):
            result += (a[i] - b[i]) ** 2
        if result < PATH_COMPARE_TOLERANCE:
            return 0
        return result

    def _getEndpointBSB(self, a, b, c, ki, km, kf):
        a *= ki
        c *= kf
        v0 = ki * sin(a) + b * cos(a) + kf * (sin(a + c) - sin(a))
        v1 = ki * (-cos(a) + 1) + b * sin(a) + kf * (-cos(a + c) + cos(a))
        v2 = mod(a + c, 2 * pi)
        return [v0, v1, v2]

    def _getEndpointBBB(self, a, b, c, ki, km, kf):
        a *= ki
        b *= km
        c *= kf
        v0 = ki * (2 * sin(a) - 2 * sin(a + b) + sin(a + b + c))
        v1 = ki * (1 - 2 * cos(a) + 2 * cos(a + b) - cos(a + b + c))
        v2 = mod(a + b + c, 2 * pi)
        return [v0, v1, v2]

def mod(a, b):
    v = a - floor(a / b) * b
    w = a % b
    assert v == w
    return v
class DubinsFailureException(Exception):
    pass
