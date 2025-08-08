from . import *

class SequenceAligner(LoggerMixin, IDataPreparator):
    def __init__(self, configurator):
        super().__init__(logger=configurator.logger)
        self.configurator = configurator

    def perform(self,
        sample: SampleDataContainer,
        reference_source: PathLike[AnyStr],
        output_path: PathLike[AnyStr],
        executor: Union[CommandExecutor, callable]
    ) -> PathLike[AnyStr]:
        """
            Mapping reads to the reference human genome.

            This is the stage at which, for each read, it is determined
            where a similar sequence is located in the reference genome,
            and their alignment is performed relative to each other.

            Args:
                sample (SampleDataContainer): \
                    The container holding sample's sequencing data, \
                        including raw reads path.
                reference_source (PathLike[AnyStr]): \
                    Path to the reference genome file to which reads \
                        will be aligned.
                output_path (PathLike[AnyStr]): \
                    Path where the alignment results, \
                    including CIGAR strings, will be saved.
            Returns:
                PathLike[AnyStr]: \
                    A path to mapped reads file
        """

        aligning_logpath = os.path.abspath(os.path.join(
            sample.processing_logpath,
            os.path.basename(
                os.path.splitext(self.configurator.config['bwa-mem2'])[0]
                ))+'-mem'+'.log'
            )

        if not os.path.exists(os.path.dirname(aligning_logpath)):
            os.makedirs(os.path.dirname(aligning_logpath))

        try:
            aligning_outpath = os.path.abspath(
                os.path.join(sample.processing_path, sample.id+'.sam'))

            reads_mapping_cmd = ' '.join([
                self.configurator.config['bwa-mem2'], 'mem',
                reference_source,
                sample.R1_source,
                sample.R2_source if not sample.R2_source else '',
                '-o', aligning_outpath,
                '-t', str(self.configurator.args.threads),
                '2>', aligning_logpath])

            self.configurator.logger.info(
                f"Starting to map sample '{sample.id}' reads"
                f"to reference '{self.configurator.config['reference']}'")

            self.configurator.logger.debug(f"Command: {reads_mapping_cmd}")

            execute(executor, reads_mapping_cmd)

            self.configurator.logger.info(
                f"Alignment completed successfully. "
                f"See the log at '{aligning_logpath}'")

            return aligning_outpath
        except Exception as e:
            self.configurator.logger.critical(
                f"A fatal error '{e.__repr__()}' occured "
                f"at '{e.__traceback__.tb_frame}'")
            raise e
