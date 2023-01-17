class VerificationStrategy(object):
    def verify(self, edges, bodies, radius, **kwargs) -> int:
        '''
        verifies solution to TSP

        Parameters
        ----------
        edges: list[Edge]
            list of TSP edges
        bodies: list[Region]
            list of view volumes
        radius: float
            turn radius of the vehicle

        Returns
        -------
        bool
            True if solution solves view planning problem
        '''
        return len(edges)
