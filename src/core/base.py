import configparser
import argparse
import platform
import logging
import os
import sys
import re

from os import PathLike
from importlib.util import find_spec
from types import FunctionType
from abc import (
    ABC,
    abstractmethod)

from typing import (
    Protocol,
    AnyStr,
    Optional,
    Union,
    Any)

class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class LoggerMixin:
    def __init__(self, logger: logging.Logger=None):
        self.logger = logger
        self.set_logger(logger)

    def set_logger(self, logger: logging.Logger=None) -> None:
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
    def run(cmd): ...

class CommandExecutor(LoggerMixin, ICommandExecutor):
    def __init__(
        self,
        caller: callable=os.system,
        logger: Optional[logging.Logger]=None
    ):
        super().__init__(logger)

        if callable(caller): self.caller = caller
        else: raise TypeError(
            "Command caller must be callable, "
            f"'{type(caller)}' given")

    def run(
        self,
        command: Union[list[str], str,
        dict[str, str]]
    ) -> bool:
        if   isinstance(command, list):
            self.caller(' '.join(command))
        elif isinstance(command, str):
            self.caller(command)
        elif isinstance(command, dict):
            self.caller(' '.join(list(
                [f"{key} {value}" for (key, value) in command.items()])
                ))

        else: raise TypeError(f"Unsupported command type: {type(command)}")

        self.logger.debug(
            f"'{self.__class__.__name__}' "
            f"got '{command.__str__()}' "
            f"command as type '{type(command)}'")

        try:
            self.caller(command)
            return True

        except Exception as e:
            self.logger.critical(e)
            return False

def execute(executor, command) -> None:
    if hasattr(executor, 'run'): executor.run(command)
    elif callable(executor): executor(command)
    else: raise TypeError(f"Unsupported executor type: {type(executor)}")

def touch(path: PathLike[AnyStr]) -> None:
    with open(path, 'a'): os.utime(path, None)

def insert_processing_infix(
    infix_str: str,
    filename: PathLike[AnyStr]
) -> PathLike:
    base, ext = os.path.splitext(filename)
    if ext in [".gz", ".zip"]:
        sub_base, sub_ext = os.path.splitext(base)
        return f"{sub_base}{infix_str}{sub_ext}{ext}"
    else: return f"{base}{infix_str}{ext}"

def extract_archive(archive_filepath: PathLike[AnyStr]) -> PathLike[AnyStr]:
    archive_absolute_filepath = os.path.abspath(archive_filepath)

    if os.path.exists(archive_absolute_filepath) and os.path.isfile(archive_absolute_filepath):
        file_basename, ext = os.path.splitext(archive_absolute_filepath)
        base_dir = os.path.dirname(archive_absolute_filepath)
        match ext:
            case '.zip':
                import zipfile

                with zipfile.ZipFile(archive_absolute_filepath, 'r') as zf:
                    zf.extractall(base_dir)
                    return zf.namelist()

            case '.tar' | '.tar.gz' | '.tar.bz2' | '.tar.xz':
                import tarfile

                with tarfile.open(
                    archive_absolute_filepath, f'r:{ext.split('.')[-1]}') as tf:
                    tf.extractall(base_dir)
                    return tf.getnames()

            case '.gz':
                import gzip

                with gzip.open(archive_absolute_filepath, 'rb') as gf:
                    try:
                        with open(file_basename, 'wb') as output:
                            while True:
                                # read input files in 64KB chunks to avoid
                                # high memory usage while handling large files
                                chunk = gf.read(1024 * 64)
                                if not chunk: break
                                output.write(chunk)
                            return gf.name

                    except Exception as e:
                        raise e(
                            f"A fatal error '{e.__repr__()}' occured "
                            f"at '{e.__traceback__.tb_frame}'")

            case _:
                raise IOError(
                    "The program doesn't support decompression "
                    f"of '{ext}' files")

    else: raise FileNotFoundError

def get_platform() -> str:
    sys_platform = platform.system().lower()
    if sys_platform.startswith('linux'):
        return 'linux'
    elif sys_platform.startswith('freebsd'):
        return 'freebsd'
    elif sys_platform.startswith('aix'):
        return 'aix'
    elif sys_platform.startswith('darwin'):
        return 'macos'
    elif sys_platform.startswith('win') or sys_platform.startswith('cygwin'):
        return 'windows'
    else:
        return 'unknown'
