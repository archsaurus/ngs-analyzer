"""
    This module contains classes for variant calling
    in genomic data analysis.

    It defines a base class `VariantCaller` and specific implementations
    for different variant calling tools such as
        Pisces,
        GATK's UnifiedGenotyper,
        and FreeBayes.

    The classes provide methods to execute variant calling commands,
    handle logging, and manage configurations.

    The design promotes modularity and extensibility,
    allowing easy integration of additional
    variant callers by subclassing `VariantCaller`.

    The use of a configurator object ensures flexible parameter management
    across different tools.

    Usage:
        - Instantiate the specific variant caller class
        with the configuration.
        - Call the `call_variant()` method with a sample data container
        and executor to perform variant calling.

    Note:
        - The `UnifiedGenotyperVariantCaller` is deprecated;
        consider updating to newer GATK tools.
"""

# region Imports
import os
import sys
import logging

from typing import Optional, Union

from src.configurator import Configurator

from src.core.base import LoggerMixin
from src.core.base import CommandExecutor

from src.core.base import execute

from src.core.sample_data_container import SampleDataContainer

from src.core.analyzer.i_variant_caller import IVariantCaller
# endregion

class VariantCaller(LoggerMixin, IVariantCaller):
    """
        Base class for variant callers.

        Provides a common interface and shared functionality
        for specific variant caller implementations.
        Manages configuration and logging setup.

        Attributes:
            configurator (Configurator):
                Configuration object containing parameters and paths.
    """
    def __init__(
        self,
        configurator: Configurator,
        logger: Optional[logging.Logger]=None
        ):
        """
            Initializes the VariantCaller with
                configuration and optional logger.

            Args:
                configurator (Configurator):
                    Configuration object with paths and parameters.
                logger (Optional[logging.Logger]):
                    Logger for logging.
        """
        self.configurator = configurator
        super().__init__(logger=self.configurator.logger or None)

    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
        ):
        """
            Method to perform variant calling.
            To be implemented in subclasses.
        """
        raise NotImplementedError(
            "Subclasses should implement this method.")

class PiscesVariantCaller(VariantCaller):
    """
        Variant caller implementation using Pisces.

        Executes the Pisces command-line tool
        for variant calling on a given sample.

        Methods:
            call_variant(sample, executor):
                Performs variant calling and returns output VCF path.
    """
    def __init__(self,
        configurator: Configurator,
        logger: Optional[logging.Logger]=None
        ):
        if configurator:
            super().__init__(configurator, logger)
        else:
            sys.exit(os.EX_USAGE)

    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
        ):
        """
            Executes variant calling using Pisces.

            Args:
                sample (SampleDataContainer):
                    Sample information including BAM path.
                executor (Union[CommandExecutor, callable]):
                    Command executor.

            Returns:
                str:
                    Path to the output VCF file.
        """
        self.logger.info("Starting variant calling with Pisces")

        base_logpath = os.path.join(sample.processing_logpath, 'pisces.log')

        cmd = ' '.join([
            self.configurator.config['pisces'],
            # '--coveragemethod, f'"exact"',
            # '--sbfilter' str(0.1),
            '--coveragemethod', 'exact', # 'exact' (greedy) or 'approximate'.
            '--multiprocess', 'true',
            '--gvcf false',
            '--minbasecallquality', str(10),
            '--minmapquality', str(10),
            '--minimumvariantfrequency', str(0.01),
            '--minvariantqscore', str(1),
            '--bampaths', sample.bam_filepath,
            '--genomefolders', os.path.dirname(
                self.configurator.config['reference']),
            '--outfolder', sample.processing_path,
            '--baselogname', base_logpath,
            '>>', base_logpath,
            '2>&1'])

        self.logger.info("Executing Pisces command")
        self.logger.debug("Command: %s", cmd)

        execute(executor, cmd)

        self.logger.info(
            "Variant calling successfully done. See it's log on %s",
            base_logpath)

        return os.path.splitext(sample.bam_filepath)[0]+".vcf"

class UnifiedGenotyperVariantCaller(VariantCaller):
    """
        Deprecated GATK UnifiedGenotyper variant caller.

        Issue warning indicating deprecation.
        Intended for use with older GATK versions.

        Methods:
            call_variant(sample, executor):
                Placeholder with warning; does not perform actual calling.
    """
    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
        ) -> None:
        self.logger.warning(
            "GATK UnifiedGenotyper depricated since version 4.0.0. "
            "Configure older versions for using it")

            # cmd=[ # for 3.x.x versions
            #    self.configurator.config['java'], '-jar',
            #    self.configurator.config['gatk'], 'UnifiedGenotyper',
            #    ' -R'+configs[7],
            #    ' -I '+outDir+'patient_'+patNum+'/patient_'+patNum+
            #        '.sorted.read_groups.realigned.recal.'+cutPrimers+
            #            'bam',
            #    ' -o '+outDir+'patient_'+patNum+'/patient_'+patNum+
            #        '.sorted.read_groups.realigned.recal.'+cutPrimers+
            #            'unifiedGenotyper.vcf',
            #    ' -dfrac 1',
            #    ' -glm BOTH',
            #    ' -minIndelFrac 0.01',
            #    ' -mbq 10',
            #    ' -L chr13:32889617-32973809',
            #    ' -L chr17:41196312-41279700 -nt '+threads]

class FreebayesVariantCaller(VariantCaller):
    """
        Variant caller implementation using FreeBayes.

        Executes the FreeBayes command-line tool
        for variant calling on a given sample.

        Methods:
            call_variant(sample, executor):
                Performs variant calling.
    """
    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
        ):
        """
            Executes variant calling using FreeBayes.

            Args:
                sample (SampleDataContainer): \
                    Sample information including BAM and VCF paths.
                executor (Union[CommandExecutor, callable]): \
                    Command executor.
        """
        cmd = ' '.join([
            self.configurator.config['freebayes'],
            '--fasta-reference', self.configurator.config['reference'],
            '--ploidy', str(4),
            '--standard-filters',
            '--min-alternate-fraction', str(0.01), # default value is 0.05
            '--no-population-priors',
            '--region', self.configurator.config['chr13-interval'],
            '--region', self.configurator.config['chr17-interval'],
            '--bam', sample.bam_filepath, # input file
            '--vcf', sample.vcf_filepath]) # output file

        # alternate_cmd = ' '.join([
        #    self.configurator.config['freebayes'],
        #    '--fasta-reference', self.configurator.config['reference'],
        #    '--ploidy', str(4),
        #    '--standard-filters',
        #    '--min-alternate-fraction', str(0.01), # default value is 0.05
        #    '--no-population-priors',
        #    '--region', self.configurator.config['chr13-interval'],
        #    '--region', self.configurator.config['chr17-interval'],
        #    '--bam', sample.bam_filepath, # input file
        #    '|', 'vcfallelicprimitives', '-kg', '>', sample.vcf_filepath])

        execute(executor, cmd)
