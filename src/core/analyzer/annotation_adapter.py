"""
    This module defines interfaces and implementations
    for variant annotation adapters, specifically using SnpEff.

    It provides a protocol interface for annotation adapters
    and a concrete implementation that uses SnpEff
    to annotate variant data in VCF files.

    Classes:
        - IAnnotationAdapter:
            Protocol interface for annotation adapters.
        - SnpEffAnnotationAdapter:
            Implements variant annotation using SnpEff.

    Main Features:
        - Annotates VCF files with variant effect predictions.
        - Generates summary reports in HTML and CSV formats.
        - Supports integration with command execution frameworks.
"""

# region Imports
import os

from os import PathLike
from typing import Protocol, Union, AnyStr

from src.configurator import Configurator

from src.core.base import LoggerMixin
from src.core.base import CommandExecutor
from src.core.base import execute
from src.core.base import insert_processing_infix

from src.core.sample_data_container import SampleDataContainer
# endregion

class IAnnotationAdapter(Protocol):
    """
        Interface for annotation adapters that perform
        variant annotation on sequencing data.
    """
    def annotate(
        self,
        sample: SampleDataContainer,
        reference_ident: str,
        executor: Union[CommandExecutor, callable]
        ) -> PathLike[AnyStr]:
        """
            Performs annotation on the given sample's variant data.

            Args:
                sample (SampleDataContainer):
                    The sample containing variant data (e.g., VCF file).
                reference_ident (str):
                    Identifier for the reference genome or annotation database.
                executor (callable or CommandExecutor):
                    Function or object to execute system commands.

            Returns:
                PathLike:
                    Path to the annotated variant file (e.g., annotated VCF).
        """

class SnpEffAnnotationAdapter(LoggerMixin, IAnnotationAdapter):
    """
        Implementation of the IAnnotationAdapter interface using
        SnpEff for variant annotation.
    """
    def __init__(self, configurator: Configurator):
        """
            Initializes the SnpEffAnnotationAdapter
            with configuration settings.

            Args:
                configurator (Configurator):
                    The configuration object with paths and parameters.
        """
        self.configurator = configurator
        super().__init__(logger=self.configurator.logger)

    def annotate(
        self,
        sample: SampleDataContainer,
        reference_ident: str,
        executor: Union[CommandExecutor, callable]
        ) -> PathLike[AnyStr]:
        """
            Annotates variants in the sample's VCF file using SnpEff.

            Args:
                sample (SampleDataContainer):
                    The sample with VCF data to annotate.
                reference_ident (str):
                    The reference genome or database identifier.
                executor (callable):
                    Function or object to execute system commands.

            Returns:
                PathLike:
                    Path to the annotated VCF file.
        """
        annotated_vcf = insert_processing_infix('.ann', sample.vcf_filepath)

        html_stats_path = os.path.join(
            sample.processing_logpath, f"{sample.sid}_snpEff_summary.html")

        csv_stats_path = os.path.join(
            sample.processing_logpath, f"{sample.sid}_snpEff_summary.csv")

        cmd = ' '.join([
            self.configurator.config['java'], '-jar',
            self.configurator.config['snpeff'], reference_ident,
            '-stats', html_stats_path,
            '-csvStats', csv_stats_path,
            sample.vcf_filepath, '>', annotated_vcf])

        execute(executor, cmd)

        return insert_processing_infix('.ann', sample.vcf_filepath)
