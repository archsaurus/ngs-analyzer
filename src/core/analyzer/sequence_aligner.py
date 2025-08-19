"""
    This module defines the SequenceAligner class,
    responsible for mapping sequencing reads to a reference genome
    using an aligner such as BWA-MEM2.

    It handles the construction and execution of alignment commands,
    logging the process, and managing output files.

    Classes:
        - SequenceAligner:
            Performs read alignment to a reference genome,
            logs the process, and returns the path
            to the aligned reads file.

    Main Features:
        - Constructs command-line instructions for BWA-MEM2.
        - Ensures log directories exist.
        - Handles sample information and reference genome input.
        - Manages output paths for alignment results.
        - Implements error handling with logging.
"""

# region Imports
import os

from os import PathLike
from typing import Union, AnyStr

from src.core.base import LoggerMixin
from src.core.base import CommandExecutor
from src.core.base import execute

from src.core.analyzer.i_data_preparator import IDataPreparator
from src.core.sample_data_container import SampleDataContainer
# endregion

class SequenceAligner(LoggerMixin, IDataPreparator):
    """
        Class responsible for mapping sequencing reads to a reference genome.
        Utilizes an aligner like BWA-MEM2 to perform
        the mapping and logs the process.
    """
    def __init__(self, configurator):
        """
            Initializes the SequenceAligner with a configurator instance.

            Args:
                configurator:
                    Configuration object containing paths,
                    parameters, and logger.
        """
        super().__init__(logger=configurator.logger)
        self.configurator = configurator

    def perform(self,
        sample: SampleDataContainer,
        reference_source: PathLike[AnyStr],
        executor: Union[CommandExecutor, callable]
        ) -> PathLike[AnyStr]:
        """
            Mapping reads to the reference human genome.

            This is the stage at which, for each read, it is determined
            where a similar sequence is located in the reference genome,
            and their alignment is performed relative to each other.

            Args:
                sample (SampleDataContainer):
                    The container holding sample's sequencing data,
                    including raw reads path.
                reference_source (PathLike[AnyStr]):
                    Path to the reference genome file to which reads
                    will be aligned.
                output_path (PathLike[AnyStr]):
                    Path where the alignment results,
                    including CIGAR strings, will be saved.
            Returns:
                PathLike[AnyStr]:
                    A path to mapped reads file
        """

        aligning_logpath = os.path.abspath(os.path.join(
            sample.processing_logpath, os.path.basename(
                os.path.splitext(self.configurator.config['bwa-mem2'])[0]
                ))+'-mem'+'.log')

        if not os.path.exists(os.path.dirname(aligning_logpath)):
            os.makedirs(os.path.dirname(aligning_logpath))

        try:
            aligning_outpath = os.path.abspath(
                os.path.join(sample.processing_path, sample.sid+'.sam'))

            reads_mapping_cmd = ' '.join([
                self.configurator.config['bwa-mem2'], 'mem',
                reference_source,
                sample.r1_source,
                sample.r2_source if not sample.r2_source else '',
                '-o', aligning_outpath,
                '-t', str(self.configurator.args.threads),
                '2>', aligning_logpath,
                '-M'])

            self.configurator.logger.info(
                "Starting to map sample '%s' reads to reference '%s'",
                sample.sid,
                self.configurator.config['reference'])

            self.configurator.logger.debug(
                "Command: %s",
                reads_mapping_cmd)

            execute(executor, reads_mapping_cmd)

            self.configurator.logger.info(
                "Alignment completed successfully. See the log at '%s'",
                aligning_logpath)

            return aligning_outpath
        except Exception as e:
            self.configurator.logger.critical(
                "A fatal error '%s' occured at '%s'",
                repr(e),
                e.__traceback__.tb_frame)
            raise e
