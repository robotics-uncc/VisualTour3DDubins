from viewplanning.models.edge import Edge
from .dubinsPath import DubinsPath, DubinsPathType, DubinsFailureException
from .dubins_rust import dubins_car
from viewplanning.models import Edge2D, Vertex2D


class RustDubinsCar(DubinsPath):
    def __init__(self):
        pass

    def calculatePath(self, x0, y0, h0, x1, y1, h1, r):
        try:
            start = Vertex2D(x=x0, y=y0, theta=h0)
            end = Vertex2D(x=x1, y=y1, theta=h1)
            path = dubins_car([x0, y0, h0], [x1, y1, h1], r)
        except Exception:
            raise DubinsFailureException(f'Failed to Calculate Dubins Path s: {start} e: {end}')
        return Edge2D(
            start=start,
            end=end,
            cost=path.cost,
            aParam=path.a,
            bParam=path.b,
            cParam=path.c,
            pathType=DubinsPathType(path.path_type),
            radius=r,
        )
