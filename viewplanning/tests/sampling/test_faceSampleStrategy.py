from viewplanning.models import Region, RegionType
from viewplanning.sampling import FaceSampleStrategy
import numpy as np


def testSphere():
    sphere = [Region(type=RegionType.WAVEFRONT, file='data/viewRegions/sphere.obj',
                     rotationMatrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
    sampleStrategy = FaceSampleStrategy(50, 8, 1, [0, 0])
    result = sampleStrategy.getSamples(sphere)
    assert (np.linalg.norm([r.asPoint() for r in result], axis=1) < 20).all()
