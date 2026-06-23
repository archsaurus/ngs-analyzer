"""This module provides command-line argument parsing functionality \
    for a sequencing data processing script.

    Usage:
        Create an instance of `ArgumentParser` and call its `parse()` method
        to get an `argparse.Namespace` object with all parsed arguments.
"""

import argparse
import os
from typing import Protocol

from ngs_analyzer.core.base.helpers.path_utils import get_unique_path


class IArgumentParser(Protocol):
    """Interface for argument parser classes.

    Defines a method parse() that returns parsed command-line arguments.
    """

    @staticmethod
    def parse() -> argparse.Namespace:
        """Parse command-line arguments and returns a Namespace object \
            containing the arguments."""


class ArgumentParser(IArgumentParser):
    """Implements argument parsing using argparse \
        for sequencing data processing.

    Defines command-line arguments such as log file,
    output directory, report language, etc.
    """

    @staticmethod
    def parse() -> argparse.Namespace:
        """Set a list of command line arguments and return \
            a compiled object stored these arguments attributes."""
        parser = argparse.ArgumentParser(
            description='This script does all processing of NGS data',
        )

        arguments = [
            {
                'name': ('--log-file', '-l'), 'kwargs': {
                    'dest': 'logFilename',
                    'type': str,
                    'default': 'ngs-analyzer.log',
                    'help':
                        'Use non-default logger. '
                        f'Default logger named {os.sep}"ngs-analyzer.log"',
                },
            },
            {
                'name': ('--output-dir', '-o'),
                'kwargs': {
                    'dest': 'outputDir',
                    'type': str,
                    'default': None,
                    'help': 'Directory for output',
                },
            },
            {
                'name': ('--threads', '-th'),
                'kwargs': {
                    'dest': 'threads',
                    'type': int,
                    'default': 2,
                    'help': 'Number of threads',
                },
            },
            {
                'name': ('--configuration', '-c'),
                'kwargs': {
                    'dest': 'configFilepath',
                    'type': str,
                    'default': None,
                    'help': 'This is a path to a single configuration file '
                    'for a certain run or a list of pathes '
                    'to configuration files, that maps to a list '
                    'of library types using with the current run.',
                },
            },
            {
                'name': ('--demultiplexor', '-de'),
                'kwargs': {
                    'dest': 'demultiplexor_flag',
                    'type': bool,
                    'default': False,
                    'help': '',
                },
            },
            {
                'name': ('--table-manager', '-tm'),
                'kwargs': {
                    'dest': 'table_manager_flag',
                    'type': bool,
                    'default': False,
                    'help': '',
                },
            },
            {
                'name': ('--workers', '-w'),
                'kwargs': {
                    'dest': 'workers',
                    'type': int,
                    'default': 1,
                    'help': 'Number of parallel workers',
                },
            },
        ]

        for arg in arguments:
            parser.add_argument(*arg['name'], **arg['kwargs'])

        namespace = parser.parse_args()

        if namespace.outputDir is None:
            namespace.outputDir = get_unique_path()

        if namespace.configFilepath is None:
            namespace.configFilepath = os.path.abspath(os.path.join(
                os.curdir, 'config.ini',
            ))

        return namespace
