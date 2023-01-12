from viewplanning.models import Vertex3D


class Etsp2Dtsp:
    def findHeadings(self, vertices: 'list[Vertex3D]', faMin: float, faMax, r: float) -> 'list[Vertex3D]':
        """
        Finds headings for vertex. Function mutates input vertex list.

        Parameters
        ----------
        vertices: list[Vertex3D]
            list of vertices to find headings for
        faMin: float
            minimum pitch angle
        faMax: float
            maximum pitch angle
        r: float
            curvature constraint

        Returns
        -------
        list[Vertex3D]
            vertices with headings
        """
        return vertices
