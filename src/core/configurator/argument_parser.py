"""This module provides command-line argument parsing functionality
    for a sequencing data processing script.

    It defines:
        - `IArgumentParser`:
            An interface (via Protocol) specifying a `parse()` method
            that returns parsed arguments.
        - `ArgumentParser`:
            Implements `IArgumentParser` using Python's `argparse` module
            to define and parse command-line arguments.

    Main features:
        - Supports arguments for log file, output directory,
        report language, number of threads,
        and flags for demultiplexor and table manager.
        - Provides a clear and extendable way to
        handle command-line inputs for the script.

    Usage:
        Create an instance of `ArgumentParser` and call its `parse()` method
        to get an `argparse.Namespace` object with all parsed arguments.
"""

import os
import argparse

from typing import Protocol

from src.core.base import get_unique_path


class IArgumentParser(Protocol):
    """Interface for argument parser classes.
    Defines a method parse() that returns parsed command-line arguments.
    """

    @staticmethod
    def parse() -> argparse.Namespace:
        """Parses command-line arguments
        and returns a Namespace object containing the arguments.
        """


class ArgumentParser(IArgumentParser):
    """Implements argument parsing using argparse
        for sequencing data processing.

        Defines command-line arguments such as log file,
        output directory, report language, etc.
    """

    @staticmethod
    def parse() -> argparse.Namespace:
        """Set a list of command line arguments and return
            a compiled object stored these arguments attributes.
        """
        parser = argparse.ArgumentParser(
            description="This script does all processing "
                        "of BRCA sequencing data")

        arguments = [
            {'name': ('--log-file', '-l'), 'kwargs': {
                'dest': 'logFilename',
                'type': str,
                'default': 'ngs-analyzer.log',
                'help':
                    'Use non-default logger. '
                    f'Default logger named {os.sep}"ngs-analyzer.log"',
                }},
            {'name': ('--output-dir', '-o'), 'kwargs': {
                'dest': 'outputDir',
                'type': str,
                'default': None,
                'help': 'Directory for output'}},
            # {'name': ('--report-language', '-L'), 'kwargs': {
            #    'dest': 'lang',
            #    'type': str,
            #    'default': 'english',
            #    'help':
            #        'Language of report text (russian or english). '
            #        'Default is english'}},
            {'name': ('--threads', '-th'), 'kwargs': {
                'dest': 'threads',
                'type': int,
                'default': 2,
                'help': 'Number of threads'}},
            {'name': ('--configuration', '-c'), 'kwargs': {
                'dest': 'configFilepath',
                'type': str,
                'default': None,
                'help': 'This is a path to a single configuration file '
                'for a certain run or a list of pathes '
                'to configuration files, that maps to a list '
                'of library types using with the current run.'}},
            {'name': ('--demultiplexor', '-de'), 'kwargs': {
                'dest': 'demultiplexor_flag',
                'type': bool,
                'default': False,
                'help': ''}},
            {'name': ('--table-manager', '-tm'), 'kwargs': {
                'dest': 'table_manager_flag',
                'type': bool,
                'default': False,
                'help': ''}}
        ]

        for arg in arguments:
            parser.add_argument(*arg['name'], **arg['kwargs'])

        namespace = parser.parse_args()

        if namespace.outputDir is None:
            namespace.outputDir = get_unique_path()

        if namespace.configFilepath is None:
            namespace.configFilepath = os.path.abspath(os.path.join(
                os.curdir, 'src', 'conf', 'config.ini'
            ))

        return namespace
