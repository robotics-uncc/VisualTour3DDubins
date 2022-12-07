class VerificationStrategy(object):
    def verify(self, edges, bodies, radius, **kwargs) -> int:
        return len(edges)
