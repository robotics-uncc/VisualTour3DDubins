from viewplanning.models import Region, RegionType
from viewplanning.sampling import MaxAreaEdgeSampleStrategy
import numpy as np


def testSphere():
    sphere = [Region(type=RegionType.WAVEFRONT, file='data/viewRegions/sphere.obj',
                     rotationMatrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
    sampleStrategy = MaxAreaEdgeSampleStrategy(2, 4)
    result = sampleStrategy.getSamples(sphere)
    assert (np.linalg.norm([r.asPoint() for r in result], axis=1) < 20).all()
