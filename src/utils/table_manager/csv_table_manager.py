"""
    This module defines the CsvTableManager class, which manages
    reading from and writing to CSV files containing table data.
    It provides functionalities to set the delimiter used in CSV files,
    aggregate data from CSV files into a pandas DataFrame,
    and save DataFrames back to CSV files.

    The class extends LoggerMixin to incorporate logging capabilities
    and implements the ITableManager interface to conform to a standardized
    table management structure.

    Main functionalities include:
    - set_delimeter:
        Sets the delimiter character used for CSV reading
        and writing, with validation.
    - aggregate_data:
        (Placeholder) Method to read and combine data from CSV files
        into a pandas DataFrame.
    - save_dump:
        Saves a pandas DataFrame to a CSV file, using the specified delimiter.

    Dependencies:
    - pandas:
        For data manipulation and CSV handling.
    - src.core.base.LoggerMixin:
        Provides logging capabilities.
    - src.utils.table_manager.i_table_manager.ITableManager:
        Interface for table management behaviors.

    Usage:
        Instantiate CsvTableManager with an optional delimiter and logger,
        then use its methods to manage CSV data.
"""

import logging

from os import PathLike
from typing import AnyStr

import pandas

from src.core.base import LoggerMixin

from src.utils.table_manager.i_table_manager import ITableManager

class CsvTableManager(LoggerMixin, ITableManager):
    """
        Manages CSV file operations for tabular data,
        including reading, writing, and setting delimiters
        used in CSV formatting.

        Extends LoggerMixin to provide logging capabilities
        and conforms to the ITableManager interface
        for standardized table management.

        Attributes:
            delimeter (str):
                The character used to separate values in CSV files.
    """
    def __init__(
        self,
        delimeter: str=',',
        logger: logging.Logger=None
        ):
        super().__init__(logger=logger)
        self.delimeter = delimeter

    def set_delimeter(self, delimeter: str) -> None:
        """
            Sets the delimiter character used in CSV operations.

            Args:
                delimeter (str):
                    A single-character string to set as the delimiter.

            Raises:
                SyntaxError:
                    If the passed delimiter is not a single character.
        """
        if len(delimeter) == 1:
            if self.delimeter != delimeter:
                self.delimeter = delimeter
        else:
            raise SyntaxError(
                f"Passed non one-character delimeter '{delimeter}'")

    def aggregate_data(self, *args, **kwargs) -> pandas.DataFrame:
        """
            Placeholder method for aggregating data from CSV files
            into a pandas DataFrame.

            Returns:
                pandas.DataFrame:
                    The combined data from CSV sources.
        """

    def save_dump(
        self,
        path: PathLike[AnyStr],
        data: pandas.DataFrame
        ) -> bool:
        """
            Saves a pandas DataFrame to a CSV file
            with the specified delimiter.

            Args:
                path (PathLike[AnyStr]):
                    The file path where the CSV will be saved.
                data (pandas.DataFrame):
                    The DataFrame to write to CSV.

            Returns:
                bool:
                    True if the file was successfully written,
                    False otherwise.
        """
