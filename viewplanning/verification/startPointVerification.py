from ssl import VerifyFlags
from viewplanning.verification.verificationStrategy import VerificationStrategy
from viewplanning.models import RegionType, Region, Edge
from viewplanning.store import readObj
from viewplanning.sampling import containsPoint3d


class StartPointVerification(VerificationStrategy):
    def verify(self, edges: 'list[Edge]', bodies: 'list[Region]', **kwargs) -> bool:
        if not super().verify(edges, bodies):
            return False
        i = 0
        verified = [False] * len(bodies)
        for edge in edges:
            for i in range(len(bodies)):
                region = bodies[i]
                if region.type != RegionType.WAVEFRONT_VRIO or verified[i]:
                    continue
                obj = readObj(region.verificationRegion, region.rotationMatrix)
                if containsPoint3d(edge.start.asPoint(), obj):
                    verified[i] = True
                    break

        return sum(verified)
