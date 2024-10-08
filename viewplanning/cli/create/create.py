from viewplanning.cli.subapplication import Subapplication
from argparse import ArgumentParser
from .viewVolumes import ViewVolumes
from .montecarloExperiments import MonteCarloExperiments
from .fixViewVolumes import FixViewVolumes
from .fromjson import FromJson


class Create(Subapplication):
    '''
    Container for creational application flows
    '''

    def __init__(self):
        super().__init__('create')
        self.subapplications: 'list[Subapplication]' = [
            ViewVolumes(),
            MonteCarloExperiments(),
            FixViewVolumes(),
            FromJson()
        ]
        self.description = 'Create view volumes or experiments.'

    def modifyParser(self, parser: ArgumentParser):
        subparsers = parser.add_subparsers()
        for app in self.subapplications:
            subparser = subparsers.add_parser(app.key)
            app.modifyParser(subparser)
