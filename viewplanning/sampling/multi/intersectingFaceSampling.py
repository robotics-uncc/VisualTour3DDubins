from .helpers import MultiSampleStrategy, Volume
from viewplanning.models import Region, VertexMulti, Vertex3DMulti
from viewplanning.sampling.sampleHelpers import SamplingFailedException
import pyvista as pv
import numpy as np


class IntersectingFaceSampling(MultiSampleStrategy):
    '''
    Randomly samples the surface of the volumes.
    Pitch angles are sampled uniformly over the supplied range.
    Considers the intersction of visiblity volumes
    '''
    def __init__(self, numSamples, numPhi, phiRange, headingStrategy):
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
        super().__init__(numSamples, headingStrategy)
        self.numPhi = numPhi
        self.phiRange = phiRange

    def sampleMeshes(self, volumes: 'list[Volume]', meshes: 'list[pv.PolyData]', regions: 'list[Region]') -> 'list[VertexMulti]':
        samples = []
        for volume in volumes:
            if volume.samples <= 0:
                continue

            areas = np.array([.5 * np.linalg.norm(np.cross(
                volume.volume.points[volume.volume.faces.reshape(
                    -1, 4)[i, 1], :] - volume.volume.points[volume.volume.faces.reshape(-1, 4)[i, 2], :],
                volume.volume.points[volume.volume.faces.reshape(
                    -1, 4)[i, 1], :] - volume.volume.points[volume.volume.faces.reshape(-1, 4)[i, 3], :]
            )) for i in range(volume.volume.n_faces)])
            # get random faces
            indexes = np.random.choice(range(areas.shape[0]), size=[
                                       volume.samples], p=areas / np.sum(areas))
            points = volume.volume.points[volume.volume.faces.reshape(
                [-1, 4])[indexes, 1:]]
            # transform random point into triangle barycentric coordinate
            r1 = np.sqrt(np.random.random(size=[volume.samples, 1]))
            r2 = np.random.random(size=[volume.samples, 1])
            d = points[:, 0, :] * (1 - r1) + points[:, 1, :] * \
                r1 * (1 - r2) + points[:, 2, :] * r1 * r2
            if np.isnan(d).any():
                raise SamplingFailedException(
                    'got a nan value when trying barycentric coordiantes'
                )
            phiMag = self.phiRange[1] - self.phiRange[0]
            for point in d:
                for theta in self.headingStrategy.getHeadings(point, mesh=volume.volume, dwellMultiplier=len(volume.parents)):
                    for j in range(self.numPhi):
                        samples.append(Vertex3DMulti(
                            group=volume.parents[0],
                            visits=set(map(str, volume.parents)),
                            x=point[0],
                            y=point[1],
                            z=point[2],
                            theta=theta,
                            phi=self.phiRange[0] + phiMag * j / (self.numPhi)
                        ))
        return samples
