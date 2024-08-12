from viewplanning.models import Region, RegionType
from viewplanning.sampling.single import BodySampleStrategy
from viewplanning.sampling.heading import UniformHeadings
import numpy as np


def testSphere():
    sphere = [Region(type=RegionType.WAVEFRONT, file='data/viewRegions/sphere.obj',
                     rotationMatrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
    sampleStrategy = BodySampleStrategy(
        50,
        1,
        [0, 0],
        UniformHeadings(8, [0, 2 * np.pi])
    )

    result = sampleStrategy.getSamples(sphere)
    assert (np.linalg.norm([r.asPoint() for r in result], axis=1) < 20).all()


def testViewRegion():
    viewVol = [Region(type=RegionType.WAVEFRONT, file='data/viewRegions/vv_g_000_t_005_v_000.obj',
                      rotationMatrix=[[1, 0, 0], [0, 0, 1], [0, 1, 0]])]
    sampleStrategy = BodySampleStrategy(
        50,
        1,
        [0, 0],
        UniformHeadings(4, [0, 2 * np.pi])
    )
    result = sampleStrategy.getSamples(viewVol)
    assert len(result) == 50 * 4 * 1
