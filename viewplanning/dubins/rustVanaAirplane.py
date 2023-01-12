'''
Authors
-------
Collin Hague

References
----------
Vana, P., Alves Neto, A., Faigl, J.; MacHaret, D. G. (2020). Minimal 3D Dubins Path with Bounded Curvature and Pitch Angle.
'''

from .dubinsPath import DubinsPathType, DubinsFailureException
from .dubins_rust import vana_airplane
from .dubinsAirplane import DubinsAirplane
from viewplanning.models import Edge3D, Vertex3D


class RustVanaAirplane(DubinsAirplane):
    '''
    Applies Vana to make Dubins airplane paths
    '''

    def __init__(self):
        pass

    def calculatePath(self, x0, y0, z0, p0, g0, x1, y1, z1, p1, g1, r, faMin, faMax):
        try:
            start = Vertex3D(x=x0, y=y0, z=z0, theta=p0, phi=g0)
            end = Vertex3D(x=x1, y=y1, z=z1, theta=p1, phi=g1)
            path = vana_airplane([x0, y0, z0, p0, g0], [x1, y1, z1, p1, g1], r, faMin, faMax)
        except:
            raise DubinsFailureException(f'Failed to Compute Vana Path for s: {start} e: {end}')

        return Edge3D(
            start=start,
            end=end,
            cost=path.cost,
            aParam=path.a,
            bParam=path.b,
            cParam=path.c,
            dParam=path.d,
            eParam=path.e,
            fParam=path.f,
            pathType=DubinsPathType(path.path_type),
            pathTypeSZ=DubinsPathType(path.path_type_z),
            radius=path.radius,
            radiusSZ=path.radius_z
        )
