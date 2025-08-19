"""
    This module defines an interface for managing table data.
    It includes a Protocol for managing table data, including aggregation
    and saving to a file.
"""

import logging

from os import PathLike
from typing import Protocol, AnyStr, Optional

import pandas

class ITableManager(Protocol):
    """Interface for managing table data."""
    def aggregate_data(
        self,
        *args,
        **kwargs
        ) -> Optional[pandas.DataFrame]:
        """
            Aggregates data and returns a Pandas DataFrame.
            Returns:
                pandas.DataFrame:
                    If data has been agregated properly
                    None othervise
        """
        raise NotImplementedError

    def save_dump(
        self,
        path: PathLike[AnyStr],
        data: pandas.DataFrame
        ) -> bool:
        """
            Saves the DataFrame to a file.

            Args:
                path:
                    The path to save the file.
                data:
                    The DataFrame to save.

            Returns:
                True if the save was successful, False otherwise.
        """
        raise NotImplementedError

    def set_logger(
        self,
        logger: logging.Logger
        ) -> None:
        """
            Sets the logger for the table manager.

            Args:
                logger:
                    The logger instance.
            """
        raise NotImplementedError
