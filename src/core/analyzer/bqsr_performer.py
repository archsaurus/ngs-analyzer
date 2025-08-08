from . import *

class BQSRPerformer(LoggerMixin, IDataPreparator):
    def __init__(
        self,
        configurator: Configurator,
        target_regions: list[str]
    ):
        super().__init__(logger=configurator.logger)
        self.configurator = configurator
        self.target_regions = target_regions

    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> PathLike[AnyStr]:
        """
            Performs Base Quality Score Recalibration (BQSR) using \
                GATK's BaseRecalibrator and ApplyBQSR tools.

            This method executes two sequential GATK commands:
            1. BaseRecalibrator to generate a recalibration table.
            2. ApplyBQSR to produce a recalibrated BAM file.

            Args:
                sample (SampleDataContainer): \
                    The sample data container with processing info.

            Returns:
                PathLike[AnyStr]: Path to the recalibrated BAM file.

            Raises:
                Exception: Propagates any exceptions raised during command execution.
        """
        base_recal_logpath = os.path.abspath(os.path.join(
            sample.processing_logpath,
            f"{os.path.basename(self.configurator.config['gatk'])}-BaseRecalibrator.log"))

        racalibration_table_path = os.path.abspath(os.path.join(
            sample.processing_path, f"{sample.id}.table"))

        intervals_argstr_builder = lambda intervals: ' '.join([f"--intervals {interval}" for interval in intervals[0]])

        base_recal_cmd_str = ' '.join([
            self.configurator.config['gatk'], 'BaseRecalibrator',
            '--input', sample.bam_filepath,
            '--output', racalibration_table_path,
            '--reference', self.configurator.config['reference'],
            # TODO: Have to make it works with a list of sites
            '--known-sites', self.configurator.config['annotation-database'],
            intervals_argstr_builder(self.target_regions),
            #'--intervals', self.configurator.config['chr13-interval'],
            #'--intervals', self.configurator.config['chr17-interval'],
            #'--intervals', self.configurator.config['chr10-interval'],
            #'--intervals', self.configurator.config['chr14-interval'],
            #'--intervals', self.configurator.config['chr19-interval'],
            '2>', base_recal_logpath,
            '>>', base_recal_logpath])

        try:
            self.logger.info("Executing BaseRecalibrator command")
            self.configurator.logger.debug(f"Command: {base_recal_cmd_str}")

            execute(executor, base_recal_cmd_str)

            self.configurator.logger.info(
                f"BaseRecalibrator completed successfully. See the log at '{base_recal_logpath}'")

            recalibrated_outpath = insert_processing_infix('.recalibrated', sample.bam_filepath)
            apply_bqsr_logpath = base_recal_logpath.replace('BaseRecalibrator', 'ApplyBQSR')
            
            # Construct the ApplyBQSR command by modifying the original BaseRecalibrator command string
            apply_bqsr_cmd_str = ' '.join([
                base_recal_cmd_str
                .replace('BaseRecalibrator', 'ApplyBQSR')
                .replace(racalibration_table_path, recalibrated_outpath)
                .replace(base_recal_logpath, apply_bqsr_logpath)
                .replace('--known-sites', '')
                .replace(self.configurator.config['annotation-database'], ''),
                '--bqsr-recal-file', racalibration_table_path])

            self.logger.info("Executing ApplyBQSR command")
            self.logger.debug(f"Command: {apply_bqsr_cmd_str}")

            execute(executor, apply_bqsr_cmd_str)
            os.rename(sample.bam_filepath, recalibrated_outpath)

            self.logger.info(
                f"ApplyBQSR completed successfully. See the log at '{apply_bqsr_logpath}'")

            return recalibrated_outpath
        except Exception as e:
            self.logger.critical(
                f"Error '{e.__repr__()}' occured at "
                f"line '{e.__traceback__.tb_frame.f_lineno}' during BQSR")

            exit(os.EX_SOFTWARE)
