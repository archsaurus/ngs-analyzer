"""This module defines a container class for storing
    sample-related data paths and identifiers.

    It includes attributes for R1 and R2 file paths,
    patient identifiers, and processing log paths.
"""

# region Imports
import os
import re
import logging

from warnings import deprecated

from os import PathLike
from typing import Optional
from typing import AnyStr

from src.configurator import Configurator
from src.utils.util import reg_tuple_generator
# endregion


class SampleDataContainer:
    """A container class for storing sample-related
        data paths and identifiers.

        Attributes:
            r1_source (PathLike[AnyStr]):
                Path to the R1 file.
            r2_source (Optional[PathLike[AnyStr]]):
                Path to the R2 file (optional).
            id (str):
                Patient identifier.
            processing_path (PathLike[AnyStr]):
                Path for storing processing logs.
            processing_logpath (PathLike[AnyStr]):
                Path to processing logs.
            bam_filepath (Optional[PathLike[AnyStr]]):
                Path to BAM file (optional).
            vcf_filepath (Optional[PathLike[AnyStr]]):
                Path to VCF file (optional).
            report_path (PathLike[AnyStr]):
                Path to the report directory.
        """

    def __init__(
        self,
        r1_source: PathLike[AnyStr],
        r2_source: PathLike[AnyStr] = None,
        sid: str = '1',
        processing_path: PathLike[AnyStr] = None,
        processing_logpath: PathLike[AnyStr] = None,
        target_regions: list[tuple[str, str]] = None,
        bam_filepath: Optional[PathLike[AnyStr]] = None,
        vcf_filepath: Optional[PathLike[AnyStr]] = None,
        report_path: PathLike[AnyStr] = None
    ):
        """Initializes a sample data container.

            Args:
                r1_source (PathLike[AnyStr]):
                    Path to the R1 file.
                r2_source (PathLike[AnyStr], optional):
                    Path to the R2 file. Defaults to None.
                id (str, optional):
                    Sample identifier. Defaults to '1'.
                processing_path (PathLike[AnyStr], optional):
                    Path for processing logs.
                    Defaults to None, which sets a default path.
                processing_logpath (PathLike[AnyStr], optional):
                    Path to processing logs.
                    Defaults to None, which sets a default path.
                target_regions (list[tuple[str, str]]):
                    A list of tuples like (pileup filepath, region name).
                    Region name must coincide with the region
                    field name from configuration file.
                bam_filepath (Optional[PathLike[AnyStr]], optional):
                    Path to BAM file. Defaults to None.
                vcf_filepath (Optional[PathLike[AnyStr]], optional):
                    Path to VCF file. Defaults to None.
                report_path (PathLike[AnyStr], optional):
                    Path to report directory.
                    Defaults to None, which sets a default path.
        """
        self.r1_source = r1_source
        self.r2_source = r2_source

        self.sid = sid

        self.processing_path = processing_path or os.path.abspath(
            os.path.join(os.path.curdir, self.sid))

        self.processing_logpath = processing_logpath or os.path.abspath(
            os.path.join(self.processing_path, 'log', self.sid))

        self.report_path = report_path or os.path.abspath(
            os.path.join(self.processing_path, "report"))

        self.target_regions = target_regions

        self.bam_filepath = bam_filepath
        self.vcf_filepath = vcf_filepath

    @deprecated('Dont work with GRCv38 cause change in read headers structure')
    def parse_regions_from_sam_file(
        self,
        configurator: Configurator,
        path: PathLike[AnyStr] = None,
        logger: logging.Logger = None
    ):
        """Parses target regions from a SAM file
            and updates the object's target_regions attribute.

            This method reads a SAM file (defaulting to a path
            based on the object's processing_path and sid) and extracts
            chromosome information from sequence headers (@SQ lines).
            It formats the chromosome identifiers into interval
            strings (e.g., 'chr01-interval') and generates corresponding region
            tuples using the provided configurator.

            Args:
                configurator (Configurator):
                    An instance used to generate region tuples
                    from interval strings.
                path (PathLike[AnyStr], optional):
                    Path to the SAM file. If None, a default path based on the
                    object's processing_path and sid is used.
                logger (logging.Logger, optional):
                    Logger for logging critical errors encountered
                    during file processing.

            Raises:
                FileNotFoundError, PermissionError, IOError, OSError:
                    If the file cannot be opened or read, an exception
                    is raised after logging the error if a logger is provided.

            Side Effects:
                Updates the object's `target_regions` attribute with a list
                of region tuples generated from parsed chromosome intervals.
        """
        target_chromosomes = []
        default_sam_filepath = os.path.abspath(os.path.join(
            self.processing_path, self.sid + ".sam"))
        try:
            with open(
                path if path is not None else default_sam_filepath,
                mode='r',
                encoding='utf-8'
            ) as fd:
                for region in re.finditer(r"@SQ.*\n", fd.read()):
                    sn_field = region.group().split('\t')[1].strip()
                    chromosome_number = sn_field.split('chr')[1]

                    if len(chromosome_number) == 1:
                        chromosome_number = "0"+str(chromosome_number)

                    chromosome_number = f"chr{chromosome_number}-interval"
                    target_chromosomes.append(chromosome_number)

            self.target_regions = [reg_tuple_generator(
                configurator, interval) for interval in target_chromosomes]

        except (FileNotFoundError, PermissionError, IOError, OSError) as e:
            if logger is not None:
                logger.critical(
                    "Can't parse intervals from '%s' "
                    "because an error '%s' occurred",
                    path if path is not None else default_sam_filepath, e)
                raise e

    def __str__(self):
        """Returns a string representation of the object.

        Returns:
            str:
                String with sample ID and file paths for R1 and R2.
        """
        return '{' \
            f"id: '{self.sid}', " \
            f"r1: '{self.r1_source}', r2: '{self.r2_source}'" '}'

    def __repr__(self):
        """Returns a detailed string representation of the object.

        Returns:
            str:
                String with class name and attribute values.
        """
        return f"{self.__class__}({self.r1_source}, {self.r2_source}, " \
               f"{self.sid}, {self.processing_path}, " \
               f"{self.processing_logpath}, {self.report_path})"
