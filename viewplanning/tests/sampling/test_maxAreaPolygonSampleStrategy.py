from viewplanning.sampling.single import MaxAreaPolygonSampleStrategy
from viewplanning.models import Region, RegionType
from viewplanning.sampling.heading import UniformHeadings
import numpy as np

TOLERANCE = .0005


def testCricle():
    sampleStrategy = MaxAreaPolygonSampleStrategy(
        50,
        UniformHeadings(8, [0, 2 * np.pi])
    )
    circle = [Region(type=RegionType.WAVEFRONT, file='data/viewRegions/sphere.obj',
                     rotationMatrix=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])]
    result = sampleStrategy.getSamples(circle)[0]
    assert result.x - 0 < TOLERANCE
    assert result.y - 0 < TOLERANCE
    assert result.theta < TOLERANCE
