"""
    This module provides command-line argument parsing functionality
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

import argparse

from typing import Protocol

class IArgumentParser(Protocol):
    """
        Interface for argument parser classes.
        Defines a method parse() that returns parsed command-line arguments.
    """
    def parse(self):
        """
            Parses command-line arguments
            and returns a Namespace object containing the arguments.
        """

class ArgumentParser(IArgumentParser):
    """
        Implements argument parsing using argparse
        for sequencing data processing.

        Defines command-line arguments such as log file,
        output directory, report language, etc.
    """
    @staticmethod
    def parse() -> argparse.Namespace:
        """
            Set a list of command line arguments and return
            a compiled object stored these arguments attributes.
        """
        parser = argparse.ArgumentParser(
            description='This script do all processing of BRCA sequencing data')
        arguments = [
            {'name': ('--log-file', '-l'), 'kwargs': {
                'dest': 'logFilename',
                'type': str,
                'default': 'brca_analyzer.log',
                'help':
                    'Use non-default logger. '
                    'Default logger named "./brca_analyzer.log"',
                }},
            {'name': ('--output-dir', '-o'), 'kwargs': {
                'dest': 'outputDir',
                'type': str,
                'required': True,
                'help': 'Directory for output'}},
            {'name': ('--report-language', '-L'), 'kwargs': {
                'dest': 'lang',
                'type': str,
                'default': 'english',
                'help':
                    'Language of report text (russian or english). '
                    'Default is english'}},
            {'name': ('--threads', '-th'), 'kwargs': {
                'dest': 'threads',
                'type': int,
                'default': 2,
                'help': 'Number of threads'}},
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
        return parser.parse_args()
