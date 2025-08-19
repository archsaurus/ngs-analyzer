"""
    This module defines an interface for a sample data factory
    and a base class for sample data containers.

    It provides a way to parse sample data from various sources,
    storing the information in a structured manner.

    The `ISampleDataFactory` protocol defines the required method
    for parsing sample data, and `SampleDataContainer` provides a common
    structure for storing sample data paths and identifiers.

    The module utilizes the `logging` module for logging operations.
"""

# region Imports
import logging
import os
import re

from os import PathLike
from typing import Protocol
from typing import AnyStr

from src.core.base import LoggerMixin
from src.core.sample_data_container import SampleDataContainer
# endregion

class ISampleDataFactory(Protocol):
    """
        Interface for a sample data factory.

        Defines the method parse_sample_data
        to be implemented by concrete classes.
    """
    def parse_sample_data(
        self,
        path: PathLike[AnyStr],
        sample_id: AnyStr
    ) -> SampleDataContainer:
        """
            Parses sample data from the given path
                for the specified sample ID.

            Args:
                path (PathLike[AnyStr]):
                    Directory path containing sample files.
                sample_id (AnyStr):
                    Identifier for the sample.

            Returns:
                SampleDataContainer:
                    An instance containing parsed sample data.
        """

class SampleDataFactory(LoggerMixin, ISampleDataFactory):
    """
        Concrete implementation of the ISampleDataFactory interface.

        Uses logging for error reporting and parsing sample data from files.
    """
    def __init__(self, logger: logging.Logger=None):
        """
            Initializes the factory with an optional custom logger.

            Args:
                logger (logging.Logger, optional):
                    Logger instance. Defaults to None.
        """
        super().__init__()

    def parse_sample_data(
        self, path:
        PathLike[AnyStr],
        sample_id: AnyStr
        ) -> SampleDataContainer:
        """
            Parses sample data files from a directory based on the sample ID.

            Looks for files containing
                the sample ID and 'R1' or 'R2' in their names.

            Args:
                path (PathLike[AnyStr]):
                    Directory path containing sample files.
                sample_id (AnyStr):
                    Identifier for the sample.

            Returns:
                SampleDataContainer:
                    An instance with source paths for R1 and R2,
                    or None if files are not found.
        """
        regexp_filter = re.compile(rf"^.*{sample_id}.*")
        sample_reads_source_pathes = filter(
            regexp_filter.match, os.listdir(path))

        sample_r1_path, sample_r2_path = None, None
        for read in sample_reads_source_pathes:
            if 'R1' in read:
                sample_r1_path = read
                continue
            if 'R2' in read:
                sample_r2_path = read
                continue

        if all((
            sample_r1_path is not None,
            sample_r2_path is not None)):
            sample_data = SampleDataContainer(
                sid=sample_id,
                r1_source=os.path.join(path, sample_r1_path),
                r2_source=os.path.join(path, sample_r2_path))

            return sample_data

        self.logger.critical(
            "Can't find '%s' file for sample '%s'",
            'R1' if sample_r1_path is None else 'R2',
            sample_id.strip())

        return None
