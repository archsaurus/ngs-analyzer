"""
    This module contains the AdapterTrimmer class,
    which manages the removal of adapter sequences from sequencing
    reads using the Trimmomatic program.

    This preprocessing step is crucial for ensuring that primer sequences
    are positioned close to the read ends,
    allowing for more accurate downstream analysis.

    Classes:
        - AdapterTrimmer:
        Responsible for executing adapter trimming on sequencing reads.
        Utilizes Trimmomatic, supports both single-end and paired-end modes, and logs
        the trimming process.

    Main Features:
        - Validates the existence of input read files.
        - Constructs and executes the Trimmomatic command with appropriate parameters.
        - Handles output directories and logging.
        - Returns paths to the processed, adapter-trimmed read files.

    Dependencies:
        - os: Standard library for filesystem operations.
        - src.core.base: Provides logging and command execution utilities.
        - src.core.sample_data_container: Defines the SampleDataContainer class.
        - src.core.analyzer.i_data_preparator: Interface for data preparator classes.

    This class is designed to be integrated into sequencing data pipelines, automating
    the adapter trimming process with configurable options.
"""

# region Imports
import os

from os import PathLike
from typing import Union, AnyStr

from src.core.base import LoggerMixin
from src.core.base import CommandExecutor

from src.core.base import execute
from src.core.base import insert_processing_infix

from src.core.sample_data_container import SampleDataContainer

from src.core.analyzer.i_data_preparator import IDataPreparator
# endregion

class AdapterTrimmer(LoggerMixin, IDataPreparator):
    """
        The AdapterTrimmer class is responsible for
        removing adapter sequences
        from sequencing reads using the Trimmomatic program.
        This step is essential to ensure that primer sequences are
        positioned close to the read ends,
        enabling more accurate identification.
        
        Inherits from LoggerMixin and IDataPreparator,
        implementing the data preparation interface.
    """
    def __init__(self, configurator):
        """
            Initializes the AdapterTrimmer with a configuration object.
            
            Args:
                configurator (object):
                    The configuration object containing parameters and settings,
                    including logger, file paths, and Trimmomatic options.
        """
        super().__init__(logger=configurator.logger)
        self.configurator = configurator

    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> list[PathLike[AnyStr]]:
        """
            Executes adapter sequence trimming
                on the provided sequencing sample.
            
            Args:
                sample (SampleDataContainer):
                    The container holding sample sequencing data,
                    including paths to raw reads.
                executor (Union[CommandExecutor, callable]):
                    The command executor or callable
                    responsible for running system commands.
            
            Returns:
                list[PathLike[AnyStr]]:
                    A list of paths to the processed (trimmed) read files,
                    specifically the paired read files.
            
            Raises:
                FileNotFoundError: If any of the input read files are missing.
        """

        if not os.path.exists(sample.R1_source):
            msg = f"R1 reads file '{sample.R1_source}' not found. Abort"
            self.logger.critical(msg)
            raise FileNotFoundError(msg)

        trim_outpath = os.path.abspath(os.path.join(
            sample.processing_path, 'trimmed_reads'))
        os.makedirs(trim_outpath, exist_ok=True)
        os.makedirs(sample.processing_logpath, exist_ok=True)

        trimmer_args = self.configurator.parse_configuration(
            target_section='Trimmomatic')

        outpathes = [t for t in [insert_processing_infix(
            infix, os.path.abspath(
                os.path.join(
                    trim_outpath,
                    os.path.basename(sample.R1_source))
                )
            ) for infix in ['.paired', '.unpaired']]]

        if sample.R2_source is None: # SE
            trimmer_args.update({
                'mode': 'SE',
                'basein': sample.R1_source,
                'baseout': tuple(outpathes)})

        else: # PE
            if not os.path.exists(sample.R2_source):
                msg = f"R2 reads file '{sample.R2_source}' not found. Abort"

                self.logger.critical(msg)
                raise FileNotFoundError(msg)

            outpathes.extend(
                [t for t in [insert_processing_infix(
                    infix, os.path.abspath(
                        os.path.join(
                            trim_outpath,
                            os.path.basename(sample.R2_source))
                    )
                ) for infix in ['.paired', '.unpaired']]])

            trimmer_args.update({
                'mode': 'PE',
                'basein': (sample.R1_source, sample.R2_source),
                'baseout': tuple(outpathes)})

        os.makedirs(os.path.dirname(sample.processing_logpath), exist_ok=True)

        trimmer_logging_basepath =  os.path.basename(
            os.path.splitext(self.configurator.config['trimmomatic'])[0])
        trimmer_summary_path = os.path.abspath(os.path.join(
            sample.processing_logpath, trimmer_logging_basepath+'.summary'))
        trimmer_log_path = os.path.abspath(os.path.join(
            sample.processing_logpath, trimmer_logging_basepath+'.log'))

        trimmer_cmd = ' '.join([
            self.configurator.config['java'], '-jar',
            self.configurator.config['trimmomatic'], trimmer_args['mode'],
            '-threads', str(self.configurator.args.threads),
            f"-{trimmer_args['phred']}",
            '-summary', trimmer_summary_path,
            '', ' '.join(trimmer_args['basein']),
            '', ' '.join(trimmer_args['baseout']),
            f"ILLUMINACLIP:{
                os.path.abspath(trimmer_args['adapters'])}:{trimmer_args['illuminaclip']}",
            f"LEADING:{trimmer_args['leading']}" if 'leading' in trimmer_args else '',
            f"TRAILING:{trimmer_args['trailing']}" if 'trailing' in trimmer_args else '',
            f"SLIDINGWINDOW:{
                trimmer_args['slightwindow']}" if 'slightwindow' in trimmer_args else '',
            f"MINLEN:{trimmer_args['minlen']}" if 'minlen' in trimmer_args else '',
            f"CROP:{trimmer_args['crop']}" if 'crop' in trimmer_args else '',
            f"HEADCROP:{trimmer_args['headcrop']}" if 'headcrop' in trimmer_args else '',
            '>>', trimmer_summary_path,
            '1>', trimmer_log_path,
            '2>&1',])

        self.logger.info("Starting to trim adapters with Trimmomatic")
        self.logger.debug("Command: %s", trimmer_cmd)

        execute(executor, trimmer_cmd)

        self.logger.info(
            "Adapter trimming completed successfully. See the log at '%s'",
            trimmer_summary_path)

        paired_trimmed_reads = []
        for path in trimmer_args['baseout']:
            if '.paired' in path:
                paired_trimmed_reads.append(path)
        return paired_trimmed_reads
