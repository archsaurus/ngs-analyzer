"""
    This module contains the BamGrouper class, which manages the conversion,
    sorting, and indexing of SAM files into BAM format for sequencing data.

    Classes:
        - BamGrouper:
            Converts SAM files to sorted BAM files,
            adds read group information, and indexes
            the BAM files using Picard tools.

    Main Functionality:
        - Takes a sample's SAM file output from mapping.
        - Uses Picard tools to add read groups, sort the BAM file, \
        and create an index.
        - Produces space-efficient, indexed BAM files optimized
        for downstream analysis and fast interaction.

    This class is designed to streamline BAM file
    preparation steps in sequencing pipelines,
    improving efficiency and facilitating downstream processing.
"""

# region Imports
import os
import datetime

from os import PathLike
from typing import Union, AnyStr

from src.configurator import Configurator

from src.core.base import LoggerMixin
from src.core.base import CommandExecutor

from src.core.base import execute

from src.core.sample_data_container import SampleDataContainer

from src.core.analyzer.i_data_preparator import IDataPreparator
# endregion

class BamGrouper(LoggerMixin, IDataPreparator):
    """
        The BamGrouper class handles the conversion of SAM files
        to sorted BAM files, adds read group information, and
        indexes the BAM files using Picard tools.

        BAM files are more space-efficient,
        faster for interaction, and support indexing.
    """
    def __init__(
        self,
        configurator: Configurator):
        """
            Initializes the BamGrouper with the provided configuration.

            Args:
                configurator:
                    Configuration object containing paths and parameters.
        """
        super().__init__(logger=configurator.logger)
        self.configurator = configurator

    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> (PathLike[AnyStr], PathLike[AnyStr]):
        """
            Conversion of the read mapping output on the reference (SAM file)
            to a BAM file, sorting of reads, addition of read group information,
            and indexing of the BAM file using Picard.

            BAM files occupy less disk space,
            and due to indexing and their binary format,
            interaction speed with these files is significantly higher.
            Args:
                sample (SampleDataContainer):
                    The container with sample's data,
                    may be used for naming or metadata.
                input_path (PathLike[AnyStr]):
                    Path to the input SAM file generated from mapping.

            Returns:
                tuple: A pair of paths -
                    (index_path, bam_path)
                    where index_path is the path to the BAM index file (.bai),
                    and bam_path is the path to the sorted BAM file.
        """

        picard_grouping_logpath = os.path.abspath(os.path.join(
            sample.processing_logpath,
            f"{os.path.splitext(
                os.path.basename(self.configurator.config['picard'])
                )[0]}-AddOrReplaceReadGroups.log")
            )

        picard_grouping_outpath = os.path.join(
            sample.processing_path, f"{sample.sid}.sorted.read_groups")

        group_reads_cmd = ' '.join([
            self.configurator.config['java'], '-jar', '-Xmx8g',
            self.configurator.config['picard'], 'AddOrReplaceReadGroups',
            '-INPUT', os.path.join(sample.processing_path, sample.bam_filepath),
            '-OUTPUT', picard_grouping_outpath+'.bam',
            '-SORT_ORDER', 'coordinate',
            '-CREATE_INDEX', 'TRUE',
            '2>', picard_grouping_logpath,
            '-RGDT', str(datetime.date.today()),
            '-RGLB', 'MiSeq',
            '-RGPL', 'Illumina',
            '-RGPU', 'barcode',
            '-RGSM', f"{sample.sid}"])

        self.configurator.logger.info("Start grouping aligned reads")
        self.configurator.logger.debug("Command: %s", group_reads_cmd)

        execute(executor, group_reads_cmd)

        self.configurator.logger.info(
            "Grouping reads has successfully done. See the log at '%s'",
            picard_grouping_logpath)

        return (picard_grouping_outpath + ext for ext in [".bai", ".bam"])
