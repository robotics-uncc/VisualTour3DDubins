from viewplanning.models import Region, RegionType
from viewplanning.sampling.single import GlobalPerimeterWeightedFaceSampleStrategy
import numpy as np


def testSphereAndHouse():
    bodies = [
        Region(type=RegionType.WAVEFRONT, file='data/viewRegions/sphere.obj',
               rotationMatrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
        Region(type=RegionType.WAVEFRONT, file='data/viewRegions/house.obj',
               rotationMatrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    ]
    sampleStrategy = GlobalPerimeterWeightedFaceSampleStrategy(50, 8, 1, [0, 0], 5)
    result = sampleStrategy.getSamples(bodies)
    assert (np.linalg.norm([r.asPoint() for r in result if r.group == '0'], axis=1) - 20 < .001).all()


def testViewRegion():
    rot = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]])
    bodies = [
        Region(type=RegionType.WAVEFRONT, file='data/viewRegions/vv_g_000_t_005_v_000.obj', rotationMatrix=rot),
        Region(type=RegionType.WAVEFRONT, file='data/viewRegions/vv_g_000_t_005_v_001.obj', rotationMatrix=rot),
        Region(type=RegionType.WAVEFRONT, file='data/viewRegions/vv_g_000_t_005_v_002.obj', rotationMatrix=rot),
        Region(type=RegionType.WAVEFRONT, file='data/viewRegions/vv_g_000_t_005_v_003.obj', rotationMatrix=rot),
        Region(type=RegionType.WAVEFRONT, file='data/viewRegions/vv_g_000_t_005_v_004.obj', rotationMatrix=rot),
    ]
    sampleStrategy = GlobalPerimeterWeightedFaceSampleStrategy(16, 8, 1, [0, 0], 5)
    result = sampleStrategy.getSamples(bodies)
    result
