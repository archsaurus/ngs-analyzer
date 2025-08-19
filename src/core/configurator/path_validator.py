"""
    This module defines an interface for validating file paths.

    The `IPathValidator` protocol outlines the method for verifying
    the existence of a given path.
    
    It's designed to be used by classes that need to ensure the validity
    of file paths before proceeding with operations.

    The module also imports necessary modules, including `logging` for logging,
    `os` for path manipulation, and `typing` for type hinting.

    Crucially, it imports `touch` from `src.core.base` which provides a function
    to create a file or directory if it doesn't exist.
"""

# region Imports
import logging
import os

from os import PathLike
from typing import Protocol
from typing import AnyStr

from src.core.base import LoggerMixin
from src.core.base import touch
# endregion

class IPathValidator(Protocol):
    """
        Interface for validating file or directory paths.

        This abstract class defines the contract for classes responsible
        for verifying the existence and potentially creating paths.

        Subclasses must implement the verify_path method.

        This class is intended to be used in a larger system to enforce
        consistent path handling and validation.
    """
    def verify_path(
        self,
        src: PathLike[AnyStr],
        create_if_missing: bool=False
        ) -> bool:
        """
            Verifies the existence of the specified path.

            Args:
                path (PathLike[AnyStr]):
                    The file or directory path to verify.
                create_if_missing (bool, optional):
                    If True, creates the path if it does not exist.
                    Defaults to False.

            Returns:
                bool:
                    True if the path exists or was successfully created;
                    otherwise, False.
        """

class PathValidator(LoggerMixin, IPathValidator):
    """
        Validates the existence of a file path,
        optionally creating it if missing.
    """
    def __init__(
        self,
        logger: logging.Logger=None):
        """
            Initializes the PathValidator with an optional logger.

            Args:
                logger (logging.Logger, optional): \
                    Logger instance for logging messages.
        """
        super().__init__(logger=logger)

    def verify_path(
        self,
        src: PathLike[AnyStr],
        create_if_missing: bool=False
        ) -> bool:
        """
            Checks the existence of the file
            or directory at the given path src.

            If the path does not exist, creates
            the necessary directories and the file.

            Args:
                src (PathLike[AnyStr]):
                    The path to the file or directory to check or create.
                create_if_missing (bool):
                    Whether to create the path if it doesn't exist.
                    Defaults to False.
            Returns:
                bool:
                    True if the path exists or was successfully created,
                    otherwise False.
        """
        try:
            if not os.path.exists(src):
                src_dirname = os.path.dirname(src)

                if not os.path.exists(src_dirname):
                    if create_if_missing:
                        try:
                            os.makedirs(src_dirname, exist_ok=True)
                            touch(src)

                            self.logger.info(
                                "File '%s' has been successfully created",
                                src)
                            return True

                        except (FileNotFoundError, IOError, SyntaxError) as e:
                            self.logger.critical(
                                "A fatal error '%s' occured at '%s'",
                                repr(e), e.__traceback__.tb_frame)
                else:
                    if create_if_missing:
                        try:
                            touch(src)
                            return True

                        except (FileNotFoundError, IOError, SyntaxError) as e:
                            self.logger.critical(
                                "A fatal error '%s' occured at '%s'",
                                repr(e), e.__traceback__.tb_frame)
            elif os.path.isfile(src):
                return True
            return False

        except OSError as e:
            self.logger.critical(
                "Error creating directory structure: '%s'",
                repr(e))
        return False
