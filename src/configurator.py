"""
    This module contains the implementation of the Configurator class,
    which manages the configuration setup for an analysis pipeline.

    It handles command-line argument parsing, logging configuration,
    output directory validation/creation, and loading configuration
    parameters from a configuration file.

    The Configurator class is designed as a singleton to ensure
    a single point of configuration management throughout the application.

    It utilizes other components such as PathValidator,
    LoggingConfigurator, and ConfigLoader to perform its tasks.

    Usage:
        Instantiate the Configurator class to initialize configuration,
        logging, and output directories.
"""

# region Imports
import os
import sys
import argparse
import logging

from os import PathLike
from typing import AnyStr

from src.core.base import SingletonMeta

from src.core.configurator.path_validator import PathValidator
from src.core.configurator.argument_parser import ArgumentParser
from src.core.configurator.config_loader import ConfigLoader
from src.core.configurator.logging_configurator import LoggingConfigurator
# endregion

class Configurator(metaclass=SingletonMeta):
    """
        Singleton class responsible for managing configuration,
        logging, and output directory setup for the analysis pipeline.

        This class handles parsing command-line arguments,
        setting up logging, validating and creating the output directory,
        and loading configuration parameters from a configuration file.

        Attributes:
            args (argparse.Namespace):
                Parsed command-line arguments.
            log_path (str):
                Absolute path to the log file.
            logger (logging.Logger):
                Logger instance for logging messages.
            output_dir (str):
                Path to the output directory where results will be stored.
            config (dict):
                Dictionary containing configuration parameters.

        Methods:
            _parse_args():
                Parses command-line arguments.
            _setup_logger(log_filename):
                Sets up the logging configuration.
            _setup_output_directory(output_dir):
                Validates or creates the output directory.
            _load_configuration(config_path):
                Loads configuration parameters.
            parse_configuration(base_config_filepath, target_section):
                Loads specific configuration sections.
    """
    def __init__(
        self,
        args: argparse.Namespace = None,
        config_path: PathLike[AnyStr] = None,
        log_path: PathLike[AnyStr] = None,
        output_dir: PathLike[AnyStr] = None
        ):
        """
            Initializes the Configurator, setting up logging,
            output directory, and configuration.

            Args:
                args (argparse.Namespace, optional):
                    Parsed command-line arguments. If None, parsed internally.
                config_path (PathLike[AnyStr], optional):
                    Path to configuration file. Defaults to None.
                log_path (PathLike[AnyStr], optional):
                    Path to log file. Defaults to None.
                output_dir (PathLike[AnyStr], optional):
                    Path to output directory. Defaults to None.
        """
        self.log_path, self.logger = self._setup_logger(
            log_path or 'default.log')

        self.args = args or self._parse_args()

        self.output_dir = self._setup_output_directory(output_dir or self.args.outputDir)

        self.config = self.parse_configuration(
            target_section='Pathes')

    def _parse_args(self) -> argparse.Namespace:
        """
            Parses command-line arguments using argparse.

            Returns:
                argparse.Namespace:
                    Parsed arguments object containing
                    command-line parameters.
        """
        parser = ArgumentParser()
        return parser.parse()

    def _setup_logger(
        self,
        log_filename: PathLike[AnyStr]
        ) -> (PathLike[AnyStr], logging.Logger):
        """
            Sets up the logging system with the specified log file.

            Args:
                log_filename (PathLike[AnyStr]): Path to the log file.

            Returns:
                tuple:
                    A tuple containing the absolute path
                    to the log file and the configured Logger object.
        """
        logger = LoggingConfigurator(
            path_validator=PathValidator())
        return (
            os.path.abspath(log_filename),
            logger.set_logger(silent=False))

    def _setup_output_directory(
        self,
        output_dir: PathLike[AnyStr]
        ) -> PathLike[AnyStr]:
        """
            Validates the output directory path,
            creates it if it doesn't exist,
            and handles existing directory conflicts based on user input.

            Args:
                output_dir (PathLike[AnyStr]):
                    Path to the desired output directory.

            Returns:
                PathLike[AnyStr]:
                    Absolute path to the validated or created
                    output directory.
        """
        output_dir = os.path.abspath(os.path.normpath(output_dir))

        if os.path.exists(output_dir): # Create output directory
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)
            else:
                msg = f"Directory '{output_dir}' already exists"
                self.logger.warning(msg)
                match input(
                    f"Do you want to use existing directory '{output_dir}'"
                    f" as the current output directory [y/n]: ").lower():
                    case 'n':
                        sys.exit(os.EX_OK)
                    case  _ :
                        pass
        else:
            os.mkdir(output_dir)

        self.logger.info("Use '%s' directory as output", output_dir)
        return output_dir

    def parse_configuration(
        self,
        base_config_filepath: PathLike[AnyStr]=os.path.abspath(os.path.join(
            os.path.curdir, 'src', 'conf', 'config.ini')),
        target_section: AnyStr='Pathes'
        ) -> dict:
        """
            Loads a specific section of the configuration
            from a base configuration file.

            Args:
                base_config_filepath (PathLike[AnyStr], optional):
                    Path to the base configuration file.
                    Defaults to 'src/conf/config.ini'
                    relative to current directory.
                target_section (str, optional):
                    The section within the configuration file to load.
                    Defaults to 'Pathes'.

            Returns:
                dict:
                    Dictionary of configuration parameters
                    from the specified section.
        """
        return ConfigLoader(logger=self.logger).load(
            base_config_filepath, target_section)
