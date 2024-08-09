from typing import Iterator
import numpy as np
import pyvista as pv
from viewplanning.sampling.sampleStrategy import SampleStrategy
from viewplanning.models import Region, Vertex3D
from viewplanning.sampling.sampleHelpers import iterateRegions


class FaceSampleStrategy(SampleStrategy[Region]):
    '''
    Randomly samples the surface of the volumes.
    Pitch angles are sampled uniformly over the supplied range.
    '''
    def __init__(self, numSamples, numPhi, phiRange: 'list[float]', headingStrategy):
        '''
        Parameters
        ----------
        numSamples: int
            number of (x, y, z) samples per volume
        numPhi: int
            number of pitch anlges per (X, y, z, theta) sample
        phiRange: list[float]
            acceptable range of pitch angles
        headingStrategy: HeadingStrategy
            how to allocate headings to the samples theta
        '''
        super().__init__(headingStrategy)
        self.numSamples = numSamples
        self.numPhi = numPhi
        self.phiRange = phiRange

    def getSamples(self, bodies: Iterator[Region]) -> 'list[Vertex3D]':
        samples = []
        for group, body in enumerate(iterateRegions(bodies)):
            body: pv.PolyData
            areas = np.array([.5 * np.linalg.norm(np.cross(
                body.points[body.faces.reshape(-1, 4)[i, 1], :] - body.points[body.faces.reshape(-1, 4)[i, 2], :],
                body.points[body.faces.reshape(-1, 4)[i, 1], :] - body.points[body.faces.reshape(-1, 4)[i, 3], :]
            )) for i in range(body.n_cells)])
            # get random faces
            indexes = np.random.choice(range(areas.shape[0]), size=[self.numSamples], p=areas / np.sum(areas))
            points = body.points[body.faces.reshape([-1, 4])[indexes, 1:]]
            normals = body.face_normals[indexes, :]
            # transform random point into triangle barycentric coordinate
            r1 = np.sqrt(np.random.random(size=[self.numSamples, 1]))
            r2 = np.random.random(size=[self.numSamples, 1])
            d = points[:, 0, :] * (1 - r1) + points[:, 1, :] * r1 * (1 - r2) + points[:, 2, :] * r1 * r2
            phiMag = self.phiRange[1] - self.phiRange[0]
            for k, point in enumerate(d):
                for theta in self.headingStrategy.getHeadings(point, mesh=body):
                    for j in range(self.numPhi):
                        samples.append(Vertex3D(
                            group=str(group),
                            x=point[0],
                            y=point[1],
                            z=point[2],
                            theta=theta,
                            phi=self.phiRange[0] + phiMag * j / max(self.numPhi - 1, 1)
                        ))
        return samples
