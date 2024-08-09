import argparse
from viewplanning.configuration import ConfigurationFactory
from viewplanning.cli import RunExperiments, Create, TestExperiments, View
import logging
from logging.handlers import RotatingFileHandler
import sys
import os


def main():
    subCommands = [
        RunExperiments(),
        Create(),
        TestExperiments(),
        View()
    ]
    parser = argparse.ArgumentParser(prog='viewplanning', help='solve the view planning problem for the 3D Dubins airplane')
    parser.add_argument('-c', '--config', type=str, default='./viewplanning/config.yaml', help='yaml configuration file for the solver')
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
            handler = logging.StreamHandler(stream)
        elif log['out'] == 'stderr':
            stream = sys.stderr
            handler = logging.StreamHandler(stream)
        else:
            handler = RotatingFileHandler(log['out'], log['mode'], maxBytes=100 * 2 ** 20, backupCount=3)
        form = logging.Formatter(log['format'])
        handler.setLevel(log['level'])
        handler.setFormatter(form)
        logger.addHandler(handler)
    logger.setLevel('DEBUG')
    if 'application' not in args._get_args():
        parser.print_help()
        return
    try:
        args.application(args)
    except:
        logger.critical('Critial Error')


if __name__ == '__main__':
    main()
