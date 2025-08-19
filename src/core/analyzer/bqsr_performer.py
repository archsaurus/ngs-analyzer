"""
This module contains the BQSRPerformer class, which manages
Base Quality Score Recalibration (BQSR) using GATK's BaseRecalibrator
and ApplyBQSR tools.

It performs the following key steps:
    1. Generates a recalibration table with BaseRecalibrator. \
    2. Applies the recalibration to produce a recalibrated BAM file \
    with ApplyBQSR.

The process enhances variant calling accuracy by adjusting
quality scores based on known sites and covariates,
improving downstream analyses.

Classes:
    - BQSRPerformer:
        Executes BQSR by running GATK commands, managing logs, \
        and handling input/output files.

Main Features:
    - Constructs command-line strings for GATK tools.
    - Executes commands with logging and error handling.
    - Handles input sample data and target regions.
    - Renames output files post-processing.
"""

# region Imports
import os
import sys

from os import PathLike
from typing import Union, AnyStr

from src.configurator import Configurator

from src.core.base import LoggerMixin
from src.core.base import CommandExecutor

from src.core.base import insert_processing_infix
from src.core.base import execute

from src.core.sample_data_container import SampleDataContainer

from src.core.analyzer.i_data_preparator import IDataPreparator
# endregion

class BQSRPerformer(LoggerMixin, IDataPreparator):
    """
        Handles Base Quality Score Recalibration (BQSR) using GATK's tools.

        Performs two main steps:
            1. Generates a recalibration table with BaseRecalibrator.
            2. Applies the recalibration with ApplyBQSR
            to produce a corrected BAM file.

        This process improves the accuracy of variant calling
        by adjusting quality scores based on known sites and covariates.
    """
    def __init__(
        self,
        configurator: Configurator,
        target_regions: list[str]
        ):
        """
            Initializes the BQSRPerformer
            with configuration and target regions.

            Args:
                configurator (Configurator):
                    Contains paths and parameters.
                target_regions (list[str]):
                    List of genomic intervals for targeted recalibration.
        """
        super().__init__(logger=configurator.logger)
        self.configurator = configurator
        self.target_regions = target_regions

    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
        ) -> PathLike[AnyStr]:
        """
            Executes BQSR using GATK's BaseRecalibrator and ApplyBQSR.

            Args:
                sample (SampleDataContainer):
                    The sample data to process.
                executor (Union[CommandExecutor, callable]):
                    Function or object to run commands.

            Returns:
                PathLike[AnyStr]:
                    Path to the recalibrated BAM file.

            Raises:
                Propagates exceptions from command execution
                or file operations.
        """
        base_recal_logpath = os.path.abspath(os.path.join(
            sample.processing_logpath,
            f"{os.path.basename(
                self.configurator.config['gatk'])}-BaseRecalibrator.log"))

        racalibration_table_path = os.path.abspath(os.path.join(
            sample.processing_path, f"{sample.sid}.table"))

        base_recal_cmd_str = ' '.join([
            self.configurator.config['gatk'], 'BaseRecalibrator',
            '--input', sample.bam_filepath,
            '--output', racalibration_table_path,
            '--reference', self.configurator.config['reference'],
            # TODO: Have to make it works with a list of sites
            '--known-sites', self.configurator.config['annotation-database'],
            ' '.join(
                [f"--intervals {interval}" for interval in
                [self.target_regions[i][0] for i in range(len(self.target_regions))]]),
            '2>', base_recal_logpath,
            '>>', base_recal_logpath])

        try:
            self.logger.info(
                "Executing BaseRecalibrator command")
            self.configurator.logger.debug(
                "Command: %s",
                base_recal_cmd_str)

            execute(executor, base_recal_cmd_str)

            self.configurator.logger.info(
                f"BaseRecalibrator completed successfully. "
                f"See the log at '{base_recal_logpath}'")

            recalibrated_outpath = insert_processing_infix(
                '.recalibrated', sample.bam_filepath)

            apply_bqsr_logpath = base_recal_logpath.replace(
                'BaseRecalibrator', 'ApplyBQSR')

            # Construct the ApplyBQSR command by
            # modifying the original BaseRecalibrator command string
            apply_bqsr_cmd_str = ' '.join([
                base_recal_cmd_str
                .replace('BaseRecalibrator', 'ApplyBQSR')
                .replace(racalibration_table_path, recalibrated_outpath)
                .replace(base_recal_logpath, apply_bqsr_logpath)
                .replace('--known-sites', '')
                .replace(self.configurator.config['annotation-database'], ''),
                '--bqsr-recal-file', racalibration_table_path])

            self.logger.info("Executing ApplyBQSR command")
            self.logger.debug("Command: %s", apply_bqsr_cmd_str)

            execute(executor, apply_bqsr_cmd_str)
            os.rename(sample.bam_filepath, recalibrated_outpath)

            self.logger.info(
                "ApplyBQSR completed successfully. See the log at '%s'",
                apply_bqsr_logpath)

            return recalibrated_outpath
        except (
            OSError,
            IOError,
            SystemError,
            FileNotFoundError,
            PermissionError) as e:
            self.logger.critical(
                "Error '%s' occured at line '%s' during BQSR",
                repr(e),
                e.__traceback__.tb_frame.f_lineno)

            sys.exit(os.EX_SOFTWARE)
