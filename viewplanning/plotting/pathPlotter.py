import matplotlib.pyplot as plt
from viewplanning.models import Edge, Region


class SolutionPlotter(object):
    def plot(self, regions: 'list[Region]', edges: 'list[Edge]', **kwargs):
        pass

    def savePlot(self, name):
        '''
        save plot to file

        Parameters
        ----------
        name: str
            name of the file
        '''
        plt.savefig(name)

    def close(self):
        '''
        Dispose of any plotting resouces
        '''
        plt.close()
