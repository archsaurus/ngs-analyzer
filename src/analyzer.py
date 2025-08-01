from . import *
from src.core.analyzer import *

class Analyzer(metaclass=SingletonMeta):
    def __init__(
        self,
        configurator: Configurator,
        cmd_caller: Union[CommandExecutor, callable]=None
    ):
        self.configurator = configurator

        if isinstance(cmd_caller, CommandExecutor): self.cmd_caller = cmd_caller
        elif isinstance(cmd_caller, type(callable)): self.cmd_caller = cmd_caller
        else: self.cmd_caller = os.system

        self.context = {}

    def prepareData(self, sample: SampleDataContainer) -> dict[str, dict[str, PathLike[AnyStr]]]:
        bwa2mem = SequenceAligner(self.configurator)
        picardGroupReads = BamGrouper(self.configurator)
        gatk4BQSR = BQSRPerformer(self.configurator)
        piscesVariantCaller = VariantCallerFactory.create_caller(caller_config={'name': 'pisces'}, configurator=self.configurator)
        snpEff = SnpEffAnnotationAdapter(self.configurator)

        pTrimmer = PrimerCutter.create_primer_cutter(self.configurator, 'ptrimmer')

        # No needed with pTrimmer, but it is with cutPrimers
        # trimmomatic = AdapterTrimmer(self.configurator)
        # sample.R1_source, sample.R2_source = trimmomatic.perform(sample, os.system)

        sample.R1_source, sample.R2_source = pTrimmer.perform(sample, os.system)
        
        sample.bam_filepath = bwa2mem.perform(sample, self.configurator.config['reference'], self.configurator.output_dir, os.system)
        bam_index_filepath, sample.bam_filepath = picardGroupReads.perform(sample, os.system)

        sample.bam_filepath = gatk4BQSR.perform(sample, os.system)
        os.rename(bam_index_filepath, sample.bam_filepath+".bai")
        sample.vcf_filepath = piscesVariantCaller.call_variant(sample, os.system)
        annotated_sample_filepath = snpEff.annotate(sample, 'hg19', os.system)
        
        cmd = ' '.join([
            self.configurator.config['convert2annovar'],
            '-format', 'vcf4',
            '-includeinfo',
            '-allsample',
            '-withfreq',
            annotated_sample_filepath, '>', annotated_sample_filepath+'.avinput'
        ])
        self.cmd_caller(cmd)
        
        return {sample.id: {'bam_filepath': sample.bam_filepath, 'recalibrated_bam_filepath': ''}}

    def analyze(self): pass

    def __repr__(self): return f"{self.__class__}(configurator={self.configurator}, cmd_caller={self.cmd_caller}, context={self.context})"
    def __str__(self): return f"{self.context}"
