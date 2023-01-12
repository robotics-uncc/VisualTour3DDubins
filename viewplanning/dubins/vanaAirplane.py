"""
Authors
-------
    Collin Hague
References
----------
    https://github.com/robotics-uncc/RobustDubins
    Lumelsky, V. (2001). Classification of the Dubins set.
    Vana, P., Alves Neto, A., Faigl, J.; MacHaret, D. G. (2020). Minimal 3D Dubins Path with Bounded Curvature and Pitch Angle.
"""
from viewplanning.dubins.dubinsAirplane import DubinsAirplane
from viewplanning.models import DubinsPathType, Edge2D, Edge3D, Vertex3D, Vertex2D
from math import nan, inf, sqrt, isinf


APPROX_ZERO = .1e-10
MAX_ITER = 1000


# a, b, c, c*, d, e, f, cost, xyType, szType
DEFUALT_DUBINS = (nan, nan, nan, nan, nan, nan, nan, inf, DubinsPathType.UNKNOWN, DubinsPathType.UNKNOWN)


class VanaAirplane(DubinsAirplane):
    def calculatePath(self, x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, faMin, faMax):
        b = 2
        xyEdge, szEdge = self.decoupled(x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, r * b)
        i = 0
        while not self.isFeasible(szEdge, faMin, faMax) and i < MAX_ITER:
            b *= 2
            xyEdge, szEdge = self.decoupled(x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, r * b)
            i += 1
        delta = .1
        i = 0
        while abs(delta) > APPROX_ZERO and i < MAX_ITER:
            c = max(1, b + delta)
            xyEdgePrime, szEdgePrime = self.decoupled(x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, r * c)
            if self.isFeasible(szEdgePrime, faMin, faMax) and szEdgePrime.cost < szEdge.cost:
                szEdge = szEdgePrime
                xyEdge = xyEdgePrime
                b = c
                delta *= 2
            else:
                delta = -.1 * delta
            i += 1
        return Edge3D(
            start=Vertex3D(x=x0, y=y0, z=z0, theta=h0, phi=p0),
            end=Vertex3D(x=x1, y=y1, z=z1, theta=h1, phi=p1),
            aParam=xyEdge.aParam,
            bParam=xyEdge.bParam,
            cParam=xyEdge.cParam,
            dParam=szEdge.aParam,
            eParam=szEdge.bParam,
            fParam=szEdge.cParam,
            pathType=xyEdge.pathType,
            pathTypeSZ=szEdge.pathType,
            cost=szEdge.cost,
            radius=xyEdge.radius,
            radiusSZ=szEdge.radius
        )

    def decoupled(self, x0, y0, z0, h0, p0, x1, y1, z1, h1, p1, r, rHorizontal):
        xyEdge = super().calculatePath(x0, y0, h0, x1, y1, h1, rHorizontal)
        if r == rHorizontal:
            szEdge = Edge2D(
                start=Vertex2D(x=0, y=z0, theta=p0),
                end=Vertex2D(x=xyEdge.cost, y=z1, theta=p1),
                aParam=0,
                bParam=0,
                cParam=0,
                pathType=DubinsPathType.UNKNOWN,
                cost=inf
            )
            return xyEdge, szEdge

        rVertical = 1 / sqrt(r ** -2 - rHorizontal ** -2)
        szEdge = super().calculatePath(0, z0, p0, xyEdge.cost, z1, p1, rVertical)
        return xyEdge, szEdge

    def isFeasible(self, szEdge: Edge2D, faMin, faMax):
        if szEdge.pathType == DubinsPathType.LRL or szEdge.pathType == DubinsPathType.RLR or szEdge.pathType == DubinsPathType.UNKNOWN:
            return False
        if szEdge.pathType.name[0] == 'R':
            if szEdge.start.theta - szEdge.aParam / szEdge.radius < faMin:
                return False
        else:
            if szEdge.start.theta + szEdge.aParam / szEdge.radius > faMax:
                return False
        return True
