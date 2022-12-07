import argparse
from viewplanning.configuration import ConfigurationFactory
from viewplanning.cli import RunExperiments, Create, TestExperiments, View
import logging
import sys


def main():
    subCommands = [
        RunExperiments(),
        Create(),
        TestExperiments(),
        View()
    ]
    parser = argparse.ArgumentParser(prog='viewplanning')
    parser.add_argument('-c', '--config', type=str, default='./viewplanning/config.yaml')
    subparsers = parser.add_subparsers()
    for subCommand in subCommands:
        subparser = subparsers.add_parser(subCommand.key)
        subCommand.modifyParser(subparser)

    args = parser.parse_args()
    config = ConfigurationFactory.getInstance(args.config)['logging']
    logger = logging.getLogger()
    for log in config['handlers']:
        if log['out'] == 'stdout':
            stream = sys.stdout
        elif log['out'] == 'stderr':
            stream = sys.stderr
        else:
            stream = open(log['out'], log['mode'])
        form = logging.Formatter(log['format'])
        handler = logging.StreamHandler(stream)
        handler.setLevel(log['level'])
        handler.setFormatter(form)
        logger.addHandler(handler)
    logger.setLevel('DEBUG')
    args.application(args)


if __name__ == '__main__':
    main()
