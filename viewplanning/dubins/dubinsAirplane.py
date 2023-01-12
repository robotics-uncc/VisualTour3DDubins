"""
Authors
-------
    Collin Hague
References
----------
    https://www.autonomousrobotslab.com/dubins-airplane.html
    https://github.com/robotics-uncc/RobustDubins
    Lumelsky, V. (2001). Classification of the Dubins set.
    Owen, M., Beard, R. W.; McLain, T. W. (2015). Implementing dubins airplane paths on fixed-wing uavs.
    Vana, P., Alves Neto, A., Faigl, J.; MacHaret, D. G. (2020). Minimal 3D Dubins Path with Bounded Curvature and Pitch Angle.
"""
from viewplanning.dubins.dubinsPath import DubinsPath
from viewplanning.models import DubinsPathType, Vertex3D, Edge3D
from math import nan, pi, sin, cos, inf, tan
from .helpers import norm2
import logging


PATH_ERROR = .001
LEARNING_RATE = .1
LEARNING_DECAY = .05


# a, b, c, c*, d, e, f, cost, xyType, szType
DEFUALT_DUBINS = (nan, nan, nan, nan, nan, nan, nan, inf, DubinsPathType.UNKNOWN, DubinsPathType.UNKNOWN)


class DubinsAirplane(DubinsPath):
    '''
    Applies Obermeyer like path length extensions to Dubins paths to create 3D Dubins airplane paths
    '''

    def calculatePath(self, x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, faMin, faMax):
        '''
        Calcualte the Dubins airplane path between [x0, y0, z0, h0, p0] and [x1, y1, z1, h1, p1] with turn radius r minimum pitch angle faMin and maximum pitch angle faMax

        Parameters
        ----------
        x0: float
            starting x position
        y0: float
            starting y position
        z0:
            starting z position
        h0: float
            starting heading angle
        p0: float
            starting pitch angle
        x1: float
            ending x position
        y1: float
            ending y position
        z1: float
            ending z position
        h1: float
            ending heading angle
        p1: float
            ending pitch angle
        r: float
            turn radius
        faMin: float
            minimum pitch angle
        faMax: float
            maximum pitch angle

        Returns
        -------
        Edge2D
            Dubins path between two positions
        '''
        # angles only 0 to 2pi
        h0 = (h0 + 2 * pi) % (2 * pi)
        h1 = (h1 + 2 * pi) % (2 * pi)
        # 2d dubins path
        cStar = 0
        xyEdge = super().calculatePath(
            x0,
            y0,
            h0,
            x1,
            y1,
            h1,
            r
        )
        # add extra path based on flight angle
        # starts creating helix
        deltaZ = z1 - z0
        minCost = deltaZ / tan(faMax if deltaZ > 0 else faMin)
        costDiff = minCost - xyEdge.cost
        cccOptimal = norm2(x0, y0, x0, y0) < 6 * r
        # low case
        if costDiff < 0:
            pass
        # medium case
        elif not cccOptimal and costDiff < 2 * pi * r:
            try:
                xyEdge.aParam, xyEdge.bParam, xyEdge.cParam, cStar, xyEdge.cost, xyEdge.pathType = self._dubinsMediumCase(x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, abs(faMin) if deltaZ < 0 else faMax, xyEdge.pathType)
            except MediumAltitudeOptimizationException as e:
                logging.warn('Failed to optimize the dubins airplane medium case. Using High Altitude case instead.')
                xyEdge.cParam, xyEdge.cost = self._dubinsHighCase(xyEdge.cParam, xyEdge.cost, minCost, r)
        # high case
        else:
            xyEdge.cParam, xyEdge.cost = self._dubinsHighCase(xyEdge.cParam, xyEdge.cost, minCost, r)
        # dubins path along z axis
        szEdge = super().calculatePath(0, 0, p0, xyEdge.cost, deltaZ, p1, r)
        return Edge3D(
            start=Vertex3D(x=x0, y=y0, z=z0, theta=h0, phi=p0),
            end=Vertex3D(x=x1, y=y1, z=z1, theta=h1, phi=p1),
            aParam=xyEdge.aParam,
            bParam=xyEdge.bParam,
            cParam=xyEdge.cParam,
            dParam=szEdge.aParam,
            eParam=szEdge.bParam,
            fParam=szEdge.cParam,
            starParam=cStar,
            pathType=xyEdge.pathType,
            pathTypeSZ=szEdge.pathType,
            cost=szEdge.cost,
            radius=xyEdge.radius,
            radiusSZ=szEdge.radius
        )

    def _dubinsHighCase(self, c, cost, minCost, r):
        while minCost > cost:
            increase = pi * 2 * r
            c += increase
            cost += increase
        return c, cost

    def _dubinsMediumCase(self, x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, flightAngle, pathType: DubinsPathType):
        # https://www.autonomousrobotslab.com/dubins-airplane.html
        pi2 = pi / 2
        dz = z1 - z0
        # add extra curve at beginning
        if dz > 0:
            pathTypeStr = pathType.name
            center = None
            psi = pi2
            dir = 1
            if pathTypeStr.startswith('R'):
                pathTypeStr = pathTypeStr[0] + 'L' + pathTypeStr[1:]
                dir = -1
            else:
                pathTypeStr = pathTypeStr[0] + 'R' + pathTypeStr[1:]
            cx, cy = x0 + r * cos(h0 + dir * pi2), y0 + r * sin(h0 + dir * pi2)
            zx, zy = cx + r * cos(dir * pi2 + h0), cy + r * sin(dir * pi2 + h0)
            thetai = h0 + dir * (psi + pi2)
            edge = super().solveType(zx, zy, thetai, x1, y1, h1, r, DubinsPathType.fromString(pathTypeStr[1:]))
            error = edge.cost + abs(r * (psi + pi2)) - dz / tan(flightAngle)
            t = 0
            while abs(error) > PATH_ERROR:
                psi = psi - error / r * LEARNING_RATE
                t += 1
                zx, zy = cx + r * cos(dir * pi2 + h0), cy + r * sin(dir * pi2 + h0)
                thetai = h0 + dir * (psi + pi2)
                edge = super().solveType(zx, zy, thetai, x1, y1, h1, r, DubinsPathType.fromString(pathTypeStr[1:]))
                error = edge.cost + abs(r * (psi + pi2)) - dz / tan(flightAngle)
                # fail to optimize
                if t > 1000 or type == DubinsPathType.UNKNOWN:
                    raise MediumAltitudeOptimizationException()
            return (psi + pi2) * r, edge.aParam, edge.bParam, edge.cParam, edge.cost + (psi + pi2) * r, DubinsPathType.fromString(pathTypeStr)

        # add extra curve at end
        else:
            dz *= -1
            pathTypeStr = pathType.name
            psi = pi2
            dir = 1
            if pathTypeStr.endswith('L'):
                pathTypeStr = pathTypeStr[:-1] + 'R' + pathTypeStr[-1]
                dir = -1
            else:
                pathTypeStr = pathTypeStr[:-1] + 'L' + pathTypeStr[-1]
            cx, cy = x1 + r * cos(h1 - dir * pi2), y1 + r * sin(h1 - dir * pi2)
            zx, zy = cx + r * cos(h1 - dir * pi2), cy + r * sin(h1 - dir * pi2)
            thetai = h1 + dir * (pi2 + psi)
            edge = super().solveType(x0, y0, h0, zx, zy, thetai, r, DubinsPathType.fromString(pathTypeStr[:-1]))
            error = edge.cost + abs(r * (2 * pi2)) - dz / tan(flightAngle)
            t = 0
            while abs(error) > PATH_ERROR:
                psi = psi - error / r * LEARNING_RATE
                t += 1
                zx, zy = cx + r * cos(h1 - dir * pi2), cy + r * sin(h1 - dir * pi2)
                thetai = h1 + dir * (pi2 + psi)
                edge = super().solveType(x0, y0, h0, zx, zy, thetai, r, DubinsPathType.fromString(pathTypeStr[:-1]))
                error = edge.cost + abs(r * (psi + pi2)) - dz / tan(flightAngle)
                # fail to optimize
                if t > 1000 or type == DubinsPathType.UNKNOWN:
                    raise MediumAltitudeOptimizationException()
            return edge.aParam, edge.bParam, edge.cParam, (psi + pi2) * r, edge.cost + abs(psi + pi2) * r, DubinsPathType.fromString(pathTypeStr)


class MediumAltitudeOptimizationException(Exception):
    pass
