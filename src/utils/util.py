"""
    This module provides utility functions for handling \
    configuration-based data generation and other helper operations. \

    Currently, it includes:
    - reg_tuple_generator: \
        Generates a tuple containing a region identifier \
            and the corresponding mpileup file path \
            based on a given configuration and chromosome interval.

    Dependencies:
    - src.configurator.Configurator: \
        A configuration handler that provides configuration data.

    Usage:
        Import functions from this module to facilitate region \
            and file path generation based on configured settings.
"""

# region Imports
import os
import logging
import tempfile

from src.configurator import Configurator

from os import PathLike
from typing import AnyStr, Optional, Union
# endregion

def reg_tuple_generator(
    configurator: Configurator,
    chr_interval: str) -> (str, str):
    """
        Generate a tuple (region, mpileup_filepath) based on the configuration.
    """
    return (
        configurator.config[chr_interval].replace('chr', '').strip(),
        f"mpileup{chr_interval[3:5]}")

def depth_filter(
    filepath: PathLike[AnyStr],
    depth: int=10,
    logger: Optional[logging.Logger]=None
    ) -> None:
    """
        Filters lines in a mpileup file based on a depth value
        in the fourth field.

        Reads the specified file line by line, and writes only those lines
        where the integer value in the fourth field (index 3) is greater
        than or equal to the specified 'depth' threshold.
        The original file is atomically replaced with the filtered content.

        Args:
            filepath (PathLike[AnyStr]):
                Path to the input file to be filtered.
            depth (int, optional):
                Minimum depth value to retain lines. Defaults to 10.
            logger (Optional[logging.Logger], optional):
                Logger instance for warnings and critical messages.
                If None, messages are printed to standard output.

        Raises:
            FileNotFoundError:
                If the input file does not exist.
            PermissionError:
                If there are insufficient permissions to read/write the file.
            SystemError, IOError, OSError:
                For other I/O related errors.

        Example:
            depth_filter('data.txt', depth=15)
    """
    try:
        with open(
            file=filepath,
            mode='r',
            encoding='utf-8'
            ) as fd, tempfile.NamedTemporaryFile(
                mode='w',
                delete=False,
                dir=os.path.dirname(filepath),
                encoding='utf-8'
            ) as temp_fd:
            for line in fd:
                fields = line.strip().split()
                if len(fields) < 4:
                    continue
                try:
                    depth_value = int(fields[3])
                    if depth_value >= depth:
                        temp_fd.write(line)
                except (ValueError, IndexError):
                    msg = f"An error '{repr(e)}' occured at " \
                        f"'{e.__traceback__.tb_frame.f_lineno}'. " \
                        f"Skip the line '{line}'"

                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    continue
            os.replace(temp_fd.name, filepath)
    except (
        FileNotFoundError,
        PermissionError,
        SystemError,
        IOError,
        OSError) as e:
        msg = f"A critical error '{repr(e)}' occured " \
            f"at {e.__traceback__.tb_frame.f_lineno}"
        if logger:
            logger.critical(msg)
        else:
            print(msg)
        raise e
