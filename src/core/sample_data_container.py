"""
    This module defines a container class for storing
    sample-related data paths and identifiers.

    It includes attributes for R1 and R2 file paths,
    patient identifiers, and processing log paths.
"""

# region Imports
import os

from os import PathLike
from typing import Optional
from typing import AnyStr
# endregion

class SampleDataContainer:
    """
        A container class for storing sample-related
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
        r2_source: PathLike[AnyStr]=None,
        sid: str='1',
        processing_path: PathLike[AnyStr]=None,
        processing_logpath: PathLike[AnyStr]=None,
        bam_filepath: Optional[PathLike[AnyStr]]=None,
        vcf_filepath: Optional[PathLike[AnyStr]]=None,
        report_path: PathLike[AnyStr]=None
    ):
        """
            Initializes a sample data container.

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

        self.bam_filepath = bam_filepath
        self.vcf_filepath = vcf_filepath

    def __str__(self):
        """
            Returns a string representation of the object.

            Returns:
                str:
                    String with sample ID and file paths for R1 and R2.
        """
        return "{id: '%s', r1: ''%s'', r2: '%s'}".format(
            self.sid,
            self.r1_source,
            self.r2_source)

    def __repr__(self):
        """
            Returns a detailed string representation of the object.

            Returns:
                str:
                    String with class name and attribute values.
        """
        return "%s(%s, %s, %s, %s, %s, %s)".format(
            self.__class__,
            self.r1_source, self.r2_source,
            self.sid,
            self.processing_path,
            self.processing_logpath,
            self.report_path)
