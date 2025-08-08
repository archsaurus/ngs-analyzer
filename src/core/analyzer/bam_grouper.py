from . import *

class BamGrouper(LoggerMixin, IDataPreparator):
    def __init__(self, configurator):
        super().__init__(logger=configurator.logger)
        self.configurator = configurator

    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> (PathLike[AnyStr], PathLike[AnyStr]):
        """
            Conversion of the read mapping output on the reference (SAM file) to a BAM file,
            sorting of reads, addition of read group information, \
                and indexing of the BAM file using Picard.

            BAM files occupy less disk space, and due to indexing and their binary format,
            interaction speed with these files is significantly higher.
            Args:
                sample (SampleDataContainer): The container with sample's data, \
                    may be used for naming or metadata.
                input_path (PathLike[AnyStr]): \
                    Path to the input SAM file generated from mapping.

            Returns:
                tuple: A pair of paths -
                    (index_path, bam_path)
                    where index_path is the path to the BAM index file (.bai),
                    and bam_path is the path to the sorted BAM file.
        """

        picard_grouping_logpath = os.path.abspath(os.path.join(
            sample.processing_logpath,
            f"{os.path.splitext(
                os.path.basename(self.configurator.config['picard'])
                )[0]}-AddOrReplaceReadGroups.log")
            )

        picard_grouping_outpath = os.path.join(
            sample.processing_path, f"{sample.id}.sorted.read_groups")

        group_reads_cmd = ' '.join([
            self.configurator.config['java'], '-jar', '-Xmx8g',
            self.configurator.config['picard'], 'AddOrReplaceReadGroups',
            '-INPUT', os.path.join(sample.processing_path, sample.bam_filepath),
            '-OUTPUT', picard_grouping_outpath+'.bam',
            '-SORT_ORDER', 'coordinate',
            '-CREATE_INDEX', 'TRUE',
            '2>', picard_grouping_logpath,
            '-RGDT', str(datetime.date.today()),
            '-RGLB', 'MiSeq',
            '-RGPL', 'Illumina',
            '-RGPU', 'barcode', # TODO: Copmlete grouping option
            '-RGSM', f"{sample.id}"])

        self.configurator.logger.info("Start grouping aligned reads")
        self.configurator.logger.debug(f"Command: {group_reads_cmd}")

        execute(executor, group_reads_cmd)
        
        self.configurator.logger.info(
            f"Grouping reads has successfully done. "
            f"See the log at '{picard_grouping_logpath}'")

        return (picard_grouping_outpath + ext for ext in [".bai", ".bam"])
