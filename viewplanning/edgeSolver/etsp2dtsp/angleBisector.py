import numpy as np
from viewplanning.models import Vertex3D
from .etsp2Dtsp import Etsp2Dtsp


class AngleBisector(Etsp2Dtsp):
    def findHeadings(self, vertices: 'list[Vertex3D]', faMin: float, faMax: float, r: float) -> 'list[Vertex3D]':

        for i in range(len(vertices)):
            vertices[i].theta, vertices[i].phi = self._bisectAnglePerpendicular(
                vertices[i - 1],
                vertices[i],
                vertices[(i + 1) % len(vertices)]
            )
            vertices[i].phi = np.clip(vertices[i].phi, faMin, faMax)
        return vertices

    def _bisectAnglePerpendicular(self, a: Vertex3D, b: Vertex3D, c: Vertex3D):
        vA = np.array([[a.x, a.y, a.z]])
        vB = np.array([[b.x, b.y, b.z]])
        vC = np.array([[c.x, c.y, c.z]])
        ba = vB - vA
        bc = vC - vB
        thetaBa, phiBa = self._vectorAngle(ba)
        thetaBc, phiBc = self._vectorAngle(bc)
        heading = ((thetaBc + thetaBa) / 2 + 2 * np.pi) % (2 * np.pi)
        u = np.array([np.cos(heading), np.sin(heading)])
        if (np.dot(u, ba[0, :2]) < 0).all() and (np.dot(u, bc[0, :2]) < 0).all():
            heading = (heading + np.pi) % (2 * np.pi)
        zHeading = (phiBa + phiBc) / 2
        return heading, zHeading

    def _vectorAngle(self, vector):
        theta = np.arctan2(vector[0, 1], vector[0, 0])
        phi = np.arctan2(vector[0, 2], np.linalg.norm(vector[0, :2]))  # phi in [-pi/2 to pi/2]

        return theta, phi
