from argparse import Namespace, ArgumentParser


class Subapplication(object):
    def __init__(self, key):
        self.key = key
        self.description = ''

    def modifyParser(self, parser: ArgumentParser):
        parser.set_defaults(application=lambda x: self.run(x))

    def run(self, args: Namespace):
        pass
