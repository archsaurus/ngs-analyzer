"""
    This module provides functions for validating and potentially creating
    file and directory paths.  It aims to ensure consistent path handling
    throughout a larger system, preventing errors related to missing or
    incorrectly specified paths.  The module leverages the `IPathValidator`
    interface for flexibility and maintainability.

    Functions:
        - validate_path:
            Validates a path and optionally creates it if it doesn't exist.

    Classes:
        - FileValidator:
            Validates file paths, checking for existence
            and potentially raising exceptions.
        - DirectoryValidator:
            Validates directory paths, checking for
            existence and potentially creating directories.
        - IPathValidator:
            Abstract base class defining the contract for path validation.
"""

# region Imports
import argparse
import logging
import os
import sys

from os import PathLike
from typing import Protocol
from typing import AnyStr

from src.core.configurator.path_validator import IPathValidator
# endregion

class ILoggingConfigurator(Protocol):
    """
        Protocol for configuring logging.
        Implementations should provide a method to set a logger instance.
    """
    def set_logger(
        self,
        silent: bool=False) -> logging.Logger:
        """
            Configures and returns a logger instance.

            Args:
                silent (bool, optional):
                    If True, suppresses output to console.
                    Defaults to False.

            Returns:
                logging.Logger:
                    Configured logger instance.
        """

class LoggingConfigurator(ILoggingConfigurator):
    """Configures logging to a specified file or console."""
    def __init__(
        self,
        path_validator: IPathValidator,
        log_path: PathLike[AnyStr]=os.curdir,
        args: argparse.Namespace=None):
        """
            Initializes the LoggingConfigurator with dependencies
            and parameters.

            Args:
                path_validator (IPathValidator):
                    Instance for verifying log file path.
                log_path (PathLike[AnyStr], optional):
                    Base directory for logs. Defaults to current directory.
                args (argparse.Namespace, optional):
                    Parsed command-line arguments.
        """
        self.args = args if args is not None else None
        self.log_path = log_path
        self.path_validator = path_validator

    def set_logger(
        self,
        silent: bool=False) -> logging.Logger:
        """
            Sets up logging configuration,
                creating log files and handlers.

            Args:
                silent (bool):
                    If True, disables console output. Defaults to False.

            Returns:
                logging.Logger:
                    Configured logger instance.

            Raises:
                SystemExit:
                    If verification or creation of log path fails.
        """
        try:
            if not self.args is None:
                base_logpath = os.path.abspath(os.path.join(
                    self.log_path, self.args.logFilename))
            else:
                base_logpath = os.path.abspath(os.path.join(
                    self.log_path, 'default_analyzer.log'))

            if not self.path_validator.verify_path(
                base_logpath, create_if_missing=True):
                sys.exit(os.EX_SOFTWARE)

            handlers=[logging.FileHandler(
                filename=base_logpath)]

            if not silent:
                handlers.append(logging.StreamHandler(
                    stream=sys.stdout))

            logging.basicConfig(
                level=logging.INFO,
                format=r'%(asctime)s - %(levelname)s - %(message)s',
                handlers=handlers)

            configuration_logger = logging.getLogger()
            configuration_logger.propagate = False

            return configuration_logger

        except (IOError, FileNotFoundError, SystemError, OSError) as e:
            print(
                f"A fatal error '{repr(e)}' occured at "
                f"'{e.__traceback__.tb_frame}'", file=sys.stdout)

            sys.exit(os.EX_SOFTWARE)
