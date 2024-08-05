from typing import Iterator
import numpy as np
import pyvista as pv
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.models import Region, Vertex3D
from viewplanning.sampling.sampleHelpers import iterateRegions


class FaceSampleStrategy(SampleStrategy[Region]):
    '''
    Randomly samples the surface of the volumes. Heading angles are sampled uniformly on [0, 2pi).
    Pitch angles are sampled uniformly over the supplied range.
    '''

    def __init__(self, numSamples, numTheta, numPhi, phiRange: 'list[float]'):
        '''
        Parameters
        ----------
        numSamples: int
            number of (x, y, z) samples per volume
        numTheta: int
            number of heading angles per (x, y, z) sample
        numPhi: int
            number of pitch anlges per (X, y, z, theta) sample
        phiRange: list[float]
            acceptable range of pitch angles
        '''
        self.numSamples = numSamples
        self.numTheta = numTheta
        self.numPhi = numPhi
        self.phiRange = phiRange

    def getSamples(self, bodies: Iterator[Region]) -> 'list[Vertex3D]':
        samples = []
        for group, body in enumerate(iterateRegions(bodies)):
            areas = np.array([.5 * np.linalg.norm(np.cross(body.cell_points(i)[:, 0] - body.cell_points(i)[:, 1],
                                                           body.cell_points(i)[:, 0] - body.cell_points(i)[:, 2]))
                              for i in range(body.n_cells)])
            # get random faces
            indexes = np.random.choice(range(areas.shape[0]), size=[self.numSamples, 1], p=areas / np.sum(areas))
            points = np.apply_along_axis(lambda i: body.cell_points(int(i))[:3], axis=1, arr=indexes)
            # transform random point into triangle barycentric coordinate
            r1 = np.sqrt(np.random.random(size=[self.numSamples, 1]))
            r2 = np.random.random(size=[self.numSamples, 1])
            d = points[:, 0, :] * (1 - r1) + points[:, 1, :] * r1 * (1 - r2) + points[:, 2, :] * r1 * r2
            phiMag = self.phiRange[1] - self.phiRange[0]
            for point in d:
                for i in range(self.numTheta):
                    for j in range(self.numPhi):
                        samples.append(Vertex3D(group=str(group), x=point[0], y=point[1], z=point[2], theta=i * 2 * np.pi / self.numTheta, phi=self.phiRange[0] + phiMag * j / (self.numPhi)))
        return samples
