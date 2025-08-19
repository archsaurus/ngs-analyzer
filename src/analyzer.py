"""
    This module defines the Analyzer class,
    responsible for orchestrating
    the entire genomic data analysis pipeline.

    It manages data preparation, alignment, variant calling,
    annotation, and conversion steps, using various
    components like SequenceAligner, BamGrouper, BQSRPerformer,
    and variant callers. It also handles command execution,
    logging, and file management throughout the process.

    Main Features:
    - Initializes with a configurator and command caller.
    - Prepares data by performing sequence alignment, grouping reads,
    and recalibration.
    - Analyzes samples by calling variants, annotating them,
    converting formats, and generating reports.
    - Manages paths, logs, and subprocess execution.
"""

# region Imports
import os

from typing import Union

from src.core.base import SingletonMeta
from src.core.base import CommandExecutor
from src.core.base import execute

from src.configurator import Configurator

from src.core.sample_data_container import SampleDataContainer

from src.core.analyzer.bam_grouper import BamGrouper
from src.core.analyzer.bqsr_performer import BQSRPerformer
from src.core.analyzer.primer_cutter import PrimerCutter
from src.core.analyzer.sequence_aligner import SequenceAligner
from src.core.analyzer.annotation_adapter import SnpEffAnnotationAdapter
from src.core.analyzer.variant_caller_factory import VariantCallerFactory

from src.utils.util import reg_tuple_generator
# endregion

class Analyzer(metaclass=SingletonMeta):
    """
        Singleton class that manages the entire
        genomic data analysis pipeline.

        This class orchestrates the steps involved
        in processing sequencing data, including data preparation,
        read alignment, variant calling, annotation, and format conversion.
        It leverages various components such as SequenceAligner,
        BamGrouper, BQSRPerformer, variant callers,
        and annotation tools to perform the analysis systematically.

        Attributes:
            configurator (Configurator):
                Configuration object containing paths, parameters, and logger.
            cmd_caller (Union[CommandExecutor, callable]):
                Function or object to execute system commands.

        Methods:
            prepare_data(sample):
                Prepares raw sequencing data by trimming, aligning,
                and recalibrating.
            analyze(sample):
                Performs variant calling, annotation,
                and converts formats for reporting.
    """
    def __init__(
        self,
        configurator: Configurator,
        cmd_caller: Union[CommandExecutor, callable]=None
        ):
        self.configurator = configurator

        if isinstance(cmd_caller, CommandExecutor):
            self.cmd_caller = cmd_caller
        elif callable(cmd_caller):
            self.cmd_caller = CommandExecutor(cmd_caller)
        elif cmd_caller is None:
            self.cmd_caller = os.system
        else: raise TypeError(
            "Command caller must be callable, "
            f"'{type(cmd_caller)}' given")

    def prepare_data(
        self,
        sample: SampleDataContainer
        ) -> SampleDataContainer:
        """
            Prepares raw sequencing data for analysis, including alignment,
            read grouping, and recalibration.

            Args:
                sample (SampleDataContainer):
                    Sample with raw data and metadata.

            Returns:
                SampleDataContainer:
                    Updated sample with paths to intermediate and final files.
        """
        target_regions=[
            reg_tuple_generator(self.configurator, 'chr03-interval'),
            reg_tuple_generator(self.configurator, 'chr06-interval'),
            reg_tuple_generator(self.configurator, 'chr10-interval'),
            reg_tuple_generator(self.configurator, 'chr13-interval'),
            reg_tuple_generator(self.configurator, 'chr14-interval'),
            reg_tuple_generator(self.configurator, 'chr17-interval'),
            reg_tuple_generator(self.configurator, 'chr19-interval')]

        bwa2mem = SequenceAligner(self.configurator)
        picard_group_reads = BamGrouper(self.configurator)
        gatk4_bqsr = BQSRPerformer(self.configurator, target_regions)

        ptrimmer = PrimerCutter.create_primer_cutter(
            configurator = self.configurator,
            cutter_name  = 'ptrimmer')

        # cutPrimers = PrimerCutter.create_primer_cutter(
        #     configurator = self.configurator,
        #     cutter_name  = 'cutprimers')
        # cutPrimers.perform(
        #     sample, executor=self.cmd_caller)

        # trimmomatic = AdapterTrimmer(self.configurator)
        # sample.r1_source, sample.r2_source = trimmomatic.perform(
        #     sample, executor=self.cmd_caller)

        sample.r1_source, sample.r2_source = ptrimmer.perform(
            sample, executor=self.cmd_caller)

        sample.bam_filepath = bwa2mem.perform(
            sample,
            self.configurator.config['reference'],
            executor=self.cmd_caller)

        bam_index_filepath, sample.bam_filepath = picard_group_reads.perform(
            sample, executor=self.cmd_caller)

        sample.bam_filepath = gatk4_bqsr.perform(
            sample, executor=self.cmd_caller)
        os.rename(bam_index_filepath, sample.bam_filepath+".bai")

        return sample

    def analyze(
        self,
        sample: SampleDataContainer
        ) -> SampleDataContainer:
        """
            Performs variant calling, annotation, and format conversion.

            Args:
                sample (SampleDataContainer):
                    Sample with aligned data.

            Returns:
                SampleDataContainer:
                    Updated sample with annotated variants and reports.
        """
        pisces_variant_caller = VariantCallerFactory.create_caller(
            caller_config={'name': 'pisces'}, configurator=self.configurator)
        snpeff = SnpEffAnnotationAdapter(self.configurator)

        sample.vcf_filepath = pisces_variant_caller.call_variant(
            sample, executor=self.cmd_caller)

        annotated_sample_filepath = snpeff.annotate(
            sample, 'hg19', executor=self.cmd_caller)

        convert2annovar_logpath = os.path.join(
            sample.processing_logpath, "convert2annovar.log")

        outpath = annotated_sample_filepath+'.avinput'

        convert2annovar_cmd = ' '.join([
            self.configurator.config['convert2annovar'],
            '-format', 'vcf4',
            '-includeinfo',
            #'-allsample',
            '-withfreq',
            '2>', convert2annovar_logpath,
            annotated_sample_filepath,
            '>', outpath])

        self.configurator.logger.info(
            "Starting to execute convert2annovar")
        self.configurator.logger.debug(
            "Command: %s", convert2annovar_cmd)

        execute(self.cmd_caller, convert2annovar_cmd)

        self.configurator.logger.info(
            "Convertation to avinput format successfully done. "
            "See it's output on %s", outpath)

        table_annovar_logpath = os.path.join(
            sample.processing_logpath, "table_annovar.log")

        table_annovar_cmd = ' '.join([
            self.configurator.config['table_annovar'],
            '--buildver', 'hg19',
            '--operation', ','.join([
                'g', 'f', 'f']),
            '--protocol', ','.join([
                'refGene', 'clinvar_20250721', 'ALL.sites.2015_08']),
            '--outfile', os.path.join(
                sample.processing_path, sample.sid+".ann"),
            '--remove',
            '--otherinfo',
            outpath,
            self.configurator.config['annovar_humandb'],
            '>', table_annovar_logpath,
            '2>&1'])

        self.configurator.logger.info(
            "Starting to execute annotation with table_annovar")
        self.configurator.logger.debug(
            "Command: %s",
            table_annovar_cmd)

        execute(self.cmd_caller, table_annovar_cmd)

        annotation_result_filepath = os.path.join(
            sample.processing_path, sample.sid+".ann.hg19_multianno.csv")

        self.configurator.logger.info(
            "Annotation with annovar successfully done. "
            "See it's output on %s",
            annotation_result_filepath)

        return sample

    def __repr__(self):
        return ''.join([
            f"{self.__class__}(configurator={self.configurator.__repr__()}, "
            f"cmd_caller={self.cmd_caller.__repr__()}"])
