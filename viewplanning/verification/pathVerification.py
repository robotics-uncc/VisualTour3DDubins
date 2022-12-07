from viewplanning.verification.verificationStrategy import VerificationStrategy
from viewplanning.models import RegionType, Region, Edge
from viewplanning.store import readObj
from viewplanning.sampling import polygonFromBody, containsPoint2d
from viewplanning.plotting import makePath3d
import numpy as np

class PathVerification(VerificationStrategy):
    def verify(self, edges: 'list[Edge]', bodies: 'list[Region]', radius: float, **kwargs) -> bool:
        if not super().verify(edges, bodies, radius):
            return False
        i = 0
        verified = [False] * len(bodies)
        polygons = {}
        for edge in edges:
            for i in range(len(bodies)):
                region = bodies[i]
                if region.type != RegionType.WAVEFRONT_VRIO or verified[i]:
                    continue
                obj = readObj(region.verificationRegion, region.rotationMatrix)
                x, y, z = makePath3d(edge)
                points = np.stack([x, y, z], axis=1)
                containedPoint = False
                for point in points:
                    z = np.round(point[2], 2)
                    key = str(z) + '_' + str(i)
                    if key not in polygons.keys():
                        polygons[key] = polygonFromBody(z, obj)
                    containedPoint = containedPoint or (polygons[key] is not None and containsPoint2d(point[:2], polygons[key]))
                    if containedPoint:
                        verified[i] = True
                        break       

        return sum(verified)