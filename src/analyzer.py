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
        elif callable(cmd_caller): self.cmd_caller = CommandExecutor(cmd_caller)
        elif cmd_caller is None: self.cmd_caller = os.system
        else: raise TypeError(f"Command caller must be callable, '{type(cmd_caller)}' given")

    def prepareData(self, sample: SampleDataContainer) -> SampleDataContainer:
        
        bwa2mem = SequenceAligner(self.configurator)
        picardGroupReads = BamGrouper(self.configurator)
        gatk4BQSR = BQSRPerformer(self.configurator)

        pTrimmer = PrimerCutter.create_primer_cutter(
            configurator = self.configurator,
            cutter_name  = 'ptrimmer'
        )

        # trimmomatic = AdapterTrimmer(self.configurator)
        # sample.R1_source, sample.R2_source = trimmomatic.perform(sample, executor=self.cmd_caller)

        sample.R1_source, sample.R2_source = pTrimmer.perform(sample, executor=self.cmd_caller)

        sample.bam_filepath = bwa2mem.perform(
            sample,
            self.configurator.config['reference'],
            self.configurator.output_dir,
            executor=self.cmd_caller
        )

        bam_index_filepath, sample.bam_filepath = picardGroupReads.perform(sample, executor=self.cmd_caller)

        sample.bam_filepath = gatk4BQSR.perform(sample, executor=self.cmd_caller)
        os.rename(bam_index_filepath, sample.bam_filepath+".bai")

        return sample

    def analyze(self, sample: SampleDataContainer) -> SampleDataContainer:
        piscesVariantCaller = VariantCallerFactory.create_caller(caller_config={'name': 'pisces'}, configurator=self.configurator)
        snpEff = SnpEffAnnotationAdapter(self.configurator)
        sample.vcf_filepath = piscesVariantCaller.call_variant(sample, executor=self.cmd_caller)
        annotated_sample_filepath = snpEff.annotate(sample, 'hg19', executor=self.cmd_caller)
        
        convert2annovar_logpath = os.path.join(sample.processing_logpath, "convert2annovar.log")

        convert2annovar_cmd = ' '.join([
            self.configurator.config['convert2annovar'],
            '-format', 'vcf4',
            '-includeinfo',
            #'-allsample',
            '-withfreq',
            '2>', convert2annovar_logpath,
            annotated_sample_filepath, '>', annotated_sample_filepath+'.avinput',
        ])

        self.configurator.logger.info("Starting to execute convert2annovar")
        self.configurator.logger.debug(f"Command: {convert2annovar_cmd}")

        execute(self.cmd_caller, convert2annovar_cmd)
        
        self.configurator.logger.info(
            f"""Convertation to avinput format successfully done. See it's output on {annotated_sample_filepath+'.avinput'}"""
            )

        table_annovar_logpath = os.path.join(sample.processing_logpath, "table_annovar.log")
        table_annovar_cmd = ' '.join([
            self.configurator.config['table_annovar'],
            '--buildver',   'hg19',
            '--operation',  ','.join(['g',       'f',                ]),
            '--protocol',   ','.join(['refGene', 'clinvar_20250721', ]),
            '--outfile',    os.path.join(sample.processing_path, sample.id+".ann"),
            '--remove',
            '--csvout',
            '--otherinfo',
            annotated_sample_filepath+'.avinput',
            self.configurator.config['annovar_humandb'],
            '>', table_annovar_logpath,
            '2>&1'
        ])
        
        self.configurator.logger.info("Starting to execute annotation with table_annovar")
        self.configurator.logger.debug(f"Command: {table_annovar_cmd}")

        execute(self.cmd_caller, table_annovar_cmd)

        self.configurator.logger.info(
            f"""Annotation with annovar successfully done. See it's output on {os.path.join(sample.processing_path, sample.id+".ann.hg19_multianno.csv")}"""
            )

        return sample

    def __repr__(self): return f"{self.__class__}(configurator={self.configurator.__repr__()}, cmd_caller={self.cmd_caller.__repr__()}"
    def __str__(self): return f"{self.context}"
