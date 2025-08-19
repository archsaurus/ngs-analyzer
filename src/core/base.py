"""
    This module provides utility classes and functions for
    system command execution, file management, archive extraction,
    platform detection, and logging.

    Main components include:
        - SingletonMeta:
            A metaclass implementing the singleton pattern.
        - LoggerMixin:
            A mixin class to add logging capabilities to other classes.
        - ICommandExecutor:
            Protocol defining an interface for command execution.
        - CommandExecutor:
            A class to execute system commands via a callable.
        - execute:
            Utility function to run commands with an executor.
        - touch:
            Creates or updates the timestamp of a file.
        - insert_processing_infix:
            Inserts a string into a filename before its extension.
        - extract_archive:
            Extracts various archive formats (zip, tar, gzip).
        - get_platform:
            Detects the current operating system platform.

    This module facilitates building robust scripts and applications
    that require system command execution, file handling,
    archive processing, and environment detection.
"""

# region Imports
import os
import sys
import platform
import logging

from os import PathLike
from typing import Protocol, AnyStr, Optional, Union

import tarfile
import gzip
import zipfile
# endregion

class SingletonMeta(type):
    """
        Metaclass implementing the Singleton pattern.

        Ensures that only one instance of a class is created.
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        """
            Returns the singleton instance of the class.
            Creates one if it does not exist.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class LoggerMixin:
    """
        Mixin class providing logging capabilities.

        Attributes:
            logger (logging.Logger):
                Logger instance used for logging.
    """
    def __init__(self, logger: logging.Logger=None):
        """
            Initializes the LoggerMixin with an optional logger.

            Args:
                logger (Optional[logging.Logger]):
                    Custom logger instance.
        """
        self.logger = logger
        self.set_logger(logger)

    def set_logger(self, logger: logging.Logger=None) -> None:
        """
            Sets the logger instance.

            Args:
                logger (Optional[logging.Logger]):
                    New logger to set.
        """
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)

            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setFormatter(
                logging.Formatter(
                    r'%(asctime)s - %(levelname)s - %(message)s'))

            self.logger.addHandler(stdout_handler)

        else: self.logger = logger

class ICommandExecutor(Protocol):
    """
        Protocol for command executor classes.

        Defines the interface for executing system commands.
    """
    def run(self, command):
        """
            Executes a command.

            Args:
                command (Union[list[str], str, dict[str, str]]):
                    Command to execute.
        """

class CommandExecutor(LoggerMixin, ICommandExecutor):
    """
        Executes system commands using a provided callable.

        Attributes:
            caller (callable):
                Function that executes commands, defaults to os.system.
            logger (logging.Logger):
                Logger instance for logging.
    """
    def __init__(
        self,
        caller: callable=os.system,
        logger: Optional[logging.Logger]=None
    ):
        """
            Initializes the CommandExecutor.

            Args:
                caller (callable):
                    Callable that executes commands.
                logger (Optional[logging.Logger]):
                    Logger instance.
        """
        super().__init__(logger)

        if callable(caller):
            self.caller = caller
        else: raise TypeError(
            "Command caller must be callable, "
            f"'{type(caller)}' given")

    def run(
        self,
        command: Union[list[str], str,
        dict[str, str]]
    ) -> bool:
        """
            Executes the given command.

            Args:
                command (Union[list[str], str, dict[str, str]]):
                    Command to run.

            Returns:
                bool:
                    True if command executed successfully, False otherwise.
        """
        if   isinstance(command, list):
            self.caller(' '.join(command))
        elif isinstance(command, str):
            self.caller(command)
        elif isinstance(command, dict):
            self.caller(' '.join(
                [f"{key} {value}" for (key, value) in command.items()]))

        else:
            raise TypeError(f"Unsupported command type: {type(command)}")

        self.logger.debug(
            "'%s' got '%s' command as type '%s'",
            self.__class__.__name__,
            str(command), type(command))

        try:
            self.caller(command)
            return True

        except (OSError, SystemError, PermissionError, IOError) as e:
            self.logger.critical(e)
            return False

def execute(executor, command) -> None:
    """
        Executes a command using the provided executor.

        Args:
            executor (Union[ICommandExecutor, callable]):
                Executor object or callable.
            command (Union[list[str], str, dict[str, str]]):
                Command to execute.
    """
    if hasattr(executor, 'run'):
        executor.run(command)
    elif callable(executor):
        executor(command)
    else:
        raise TypeError(f"Unsupported executor type: {type(executor)}")

def touch(path: PathLike[AnyStr]) -> None:
    """
        Creates an empty file or updates the timestamp if it exists.

        Args:
            path (PathLike[AnyStr]):
                Path to the file.
    """
    with open(path, 'a', encoding='utf-8'):
        os.utime(path, None)

def insert_processing_infix(
    infix_str: str,
    filename: PathLike[AnyStr]
    ) -> PathLike:
    """
        Inserts an infix string into a filename before its extension.

        Args:
            infix_str (str):
                String to insert.
            filename (PathLike[AnyStr]):
                Original filename.

        Returns:
            PathLike:
                Modified filename with infix inserted.
    """
    base, ext = os.path.splitext(filename)
    if ext in [".gz", ".zip"]:
        sub_base, sub_ext = os.path.splitext(base)
        return f"{sub_base}{infix_str}{sub_ext}{ext}"
    return f"{base}{infix_str}{ext}"

def extract_archive(archive_filepath: PathLike[AnyStr]) -> PathLike[AnyStr]:
    """
        Extracts an archive file (zip, tar, gzip).

        Args:
            archive_filepath (PathLike[AnyStr]):
                Path to archive file.

        Returns:
            PathLike:
                List of extracted file names or extracted filename for gzip.

        Raises:
            FileNotFoundError:
                If the archive file does not exist.
            IOError:
                If the archive format is unsupported or extraction fails.
    """
    archive_absolute_filepath = os.path.abspath(archive_filepath)

    if os.path.exists(archive_absolute_filepath) and \
        os.path.isfile(archive_absolute_filepath):

        file_basename, ext = os.path.splitext(archive_absolute_filepath)
        base_dir = os.path.dirname(archive_absolute_filepath)
        match ext:
            case '.zip':
                with zipfile.ZipFile(archive_absolute_filepath, 'r') as zf:
                    zf.extractall(base_dir)
                    return zf.namelist()

            case '.tar' | '.tar.gz' | '.tar.bz2' | '.tar.xz':
                with tarfile.open(
                    archive_absolute_filepath, f'r:{ext.split('.')[-1]}') as tf:
                    tf.extractall(base_dir)
                    return tf.getnames()

            case '.gz':
                with gzip.open(archive_absolute_filepath, 'rb') as gf:
                    try:
                        with open(file_basename, 'wb') as output:
                            while True:
                                # read input files in 64KB chunks to avoid
                                # high memory usage while handling large files
                                chunk = gf.read(1024 * 64)
                                if not chunk:
                                    break
                                output.write(chunk)
                            return gf.name

                    except (OSError, SystemError, PermissionError, IOError) as e:
                        print(
                            "A fatal error '%s' occured at '%s'",
                            repr(e), e.__traceback__.tb_frame)
                        raise e

            case _:
                raise IOError(
                    "The program doesn't support decompression "
                    f"of '{ext}' files")

    else:
        raise FileNotFoundError

def get_platform() -> str:
    """
        Detects the current operating system platform.

        Returns:
            str:
                Platform name (
                'linux',
                'freebsd',
                'aix',
                'macos',
                'windows',
                'unknown').
    """
    sys_platform = platform.system().lower()
    if sys_platform.startswith('linux'):
        return 'linux'
    if sys_platform.startswith('freebsd'):
        return 'freebsd'
    if sys_platform.startswith('aix'):
        return 'aix'
    if sys_platform.startswith('darwin'):
        return 'macos'
    if sys_platform.startswith('win') or sys_platform.startswith('cygwin'):
        return 'windows'
    return 'unknown'
