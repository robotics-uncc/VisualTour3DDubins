from viewplanning.models import Region, RegionType
from viewplanning.store import readObj
from viewplanning.sampling import BodySampleStrategy, iterateRegions
import numpy as np


def testSphere():
    sphere = [Region(type=RegionType.WAVEFRONT, file='data/viewRegions/sphere.obj',
                     rotationMatrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
    sampleStrategy = BodySampleStrategy(50, 8, 1, [0, 0])

    result = sampleStrategy.getSamples(sphere)
    assert (np.linalg.norm([r.asPoint() for r in result], axis=1) < 20).all()


def testViewRegion():
    viewVol = [Region(type=RegionType.WAVEFRONT, file='data/viewRegions/vv_g_000_t_005_v_000.obj',
                      rotationMatrix=[[1, 0, 0], [0, 0, 1], [0, 1, 0]])]
    sampleStrategy = BodySampleStrategy(50, 4, 1, [0, 0])
    result = sampleStrategy.getSamples(viewVol)
    assert len(result) == 50 * 4 * 1
