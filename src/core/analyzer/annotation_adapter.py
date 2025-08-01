from . import *

class IAnnotationAdapter(Protocol):
    def annotate(
        self,
        sample: SampleDataContainer,
        reference_ident: str,
        executor: Union[CommandExecutor, callable]
    ) -> PathLike[AnyStr]: ...

class SnpEffAnnotationAdapter(LoggerMixin, IAnnotationAdapter):
    def __init__(self, configurator: Configurator):
        self.configurator = configurator
        super().__init__(logger=self.configurator.logger)

    def annotate(
        self,
        sample: SampleDataContainer,
        reference_ident: str,
        executor: Union[CommandExecutor, callable]
    ) -> PathLike[AnyStr]:
        annotated_vcf = insert_processing_infix('.ann', sample.vcf_filepath)
        
        cmd = ' '.join([
            self.configurator.config['java'], '-jar',
            self.configurator.config['snpeff'], reference_ident,
            '-stats', os.path.join(sample.processing_logpath, f"{sample.id}_snpEff_summary.html"),
            '-csvStats', os.path.join(sample.processing_logpath, f"{sample.id}_snpEff_summary.csv"),
            sample.vcf_filepath, '>', annotated_vcf
        ])

        execute(executor, cmd)

        return insert_processing_infix('.ann', sample.vcf_filepath)
