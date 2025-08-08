from . import *

class VariantCaller(LoggerMixin, IVariantCaller):
    def __init__(
        self,
        configurator: Configurator,
        logger: Optional[logging.Logger]=None
    ):
        self.configurator = configurator
        super().__init__(logger=self.configurator.logger if not logger is None else None)

    def call_variant(
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ): pass

class PiscesVariantCaller(VariantCaller):
    def __init__(self,
        configurator: Configurator,
        logger: Optional[logging.Logger]=None
    ):
        super().__init__(configurator, logger)

    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ):
        self.logger.info(f"Starting variant calling with Pisces")

        base_logpath = os.path.join(sample.processing_logpath, 'pisces.log')

        cmd = ' '.join([
            self.configurator.config['pisces'],
            # '--coveragemethod, f'"exact"',
            # '--sbfilter' str(0.1),
            '--coveragemethod', 'exact', # 'exact' or 'approximate'. 'exect' is greedy
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
        self.logger.debug("Command: {cmd}")

        execute(executor, cmd)

        self.logger.info(
            "Variant calling successfully done. "
            f"See it's log on {base_logpath}")

        return os.path.splitext(sample.bam_filepath)[0]+".vcf"

class UnifiedGenotyperVariantCaller(VariantCaller):
    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> IVariantCaller:
        self.logger.warning(
            "GATK UnifiedGenotyper depricated since version 4.0.0. "
            "Configure older versions for using it")
        """ for 3.x.x versions
            cmd=[
                self.configurator.config['java'], '-jar',
                self.configurator.config['gatk'], 'UnifiedGenotyper',
                ' -R'+configs[7],
                ' -I '+outDir+'patient_'+patNum+'/patient_'+patNum+
                    '.sorted.read_groups.realigned.recal.'+cutPrimers+
                        'bam',
                ' -o '+outDir+'patient_'+patNum+'/patient_'+patNum+
                    '.sorted.read_groups.realigned.recal.'+cutPrimers+
                        'unifiedGenotyper.vcf',
                ' -dfrac 1',
                ' -glm BOTH',
                ' -minIndelFrac 0.01',
                ' -mbq 10',
                ' -L chr13:32889617-32973809',
                ' -L chr17:41196312-41279700 -nt '+threads]
        """

        return

class FreebayesVariantCaller(VariantCaller):
    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ):
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

        alternate_cmd = ' '.join([
            self.configurator.config['freebayes'],
            '--fasta-reference', self.configurator.config['reference'],
            '--ploidy', str(4),
            '--standard-filters',
            '--min-alternate-fraction', str(0.01), # default value is 0.05
            '--no-population-priors',
            '--region', self.configurator.config['chr13-interval'],
            '--region', self.configurator.config['chr17-interval'],
            '--bam', sample.bam_filepath, # input file
            '|', 'vcfallelicprimitives', '-kg', '>', sample.vcf_filepath])

        execute(executor, cmd)
