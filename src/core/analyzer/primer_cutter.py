from . import *

class CutPrimers(LoggerMixin, IDataPreparator):
    def __init__(self, configurator: Configurator):
        super().__init__(logger=configurator.logger)
        self.configurator = configurator

    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> (PathLike[AnyStr], PathLike[AnyStr]):
        """
            Executes the primer cutting process on the provided sample data.

            This method constructs a command to run an external \
                primer cutting script with the specified parameters, \
                manages logging setup, and runs the command using \
                the provided executor. \
                It generates trimmed and untrimmed file paths, \
                logs the execution details, and returns \
                the paths to the trimmed read files.

            Args:
                sample (SampleDataContainer): \
                    The sample data containing source file \
                        paths and processing directories.
                executor (Union[CommandExecutor, callable]): \
                    An executor object or function responsible for \
                        running the command.

            Returns:
                Tuple[PathLike[AnyStr], PathLike[AnyStr]]: \
                    Paths to the trimmed R1 and R2 files.
        """
        primer_cutter_logpath = os.path.join(
            sample.processing_logpath, 'cutPrimers.log')

        if not os.path.exists(os.path.dirname(primer_cutter_logpath)):
            os.makedirs(os.path.dirname(primer_cutter_logpath))
        if not os.path.exists(primer_cutter_logpath):
            with open(primer_cutter_logpath, 'a') as f: pass

        tr1 = os.path.join(
            sample.processing_path, os.path.basename(sample.R1_source))
        tr1  = insert_processing_infix(  '.trimmed', tr1 )

        tr2 = os.path.join(
            sample.processing_path, os.path.basename(sample.R2_source))
        tr2  = insert_processing_infix(  '.trimmed', tr2 )

        utr1= os.path.join(
            sample.processing_path, os.path.basename(sample.R1_source))
        utr1 = insert_processing_infix('.untrimmed', utr1)

        utr2= os.path.join(
            sample.processing_path, os.path.basename(sample.R2_source))
        utr2 = insert_processing_infix('.untrimmed', utr2)

        cmd = ' '.join([
            self.configurator.config['python'],
            self.configurator.config['cutprimers'],
            '-r1',   sample.R1_source,
            '-tr1',  tr1,
            '-utr1', utr1,
            '-r2',   sample.R2_source,
            '-tr2',  tr2,
            '-utr2', utr2, 
            '-pr15', self.configurator.config['primer15'],
            '-pr13', self.configurator.config['primer13'],
            '-pr25', self.configurator.config['primer25'],
            '-pr23', self.configurator.config['primer23'],
            '-stat', primer_cutter_logpath,
            '-t',    str(self.configurator.args.threads)])

        '''cmd_bam = ' '.join([
            self.configurator.config['python'],
            self.configurator.config['cutprimers'],
            '-bam', sample.bam_filepath,
            '--coordinates-file', sample.bam_filepath+'.coords',
            '-outbam', insert_processing_infix('.trimmed', sample.bam_filepath),
            '-outbam2', insert_processing_infix('.untrimmed', sample.bam_filepath),
            '-pr15', self.configurator.config['primer15'],
            '-pr13', self.configurator.config['primer13'],
            '-pr25', self.configurator.config['primer25'],
            '-pr23', self.configurator.config['primer23'],
            '-stat', primer_cutter_logpath,
            '-t', str(self.configurator.args.threads)])'''

        self.configurator.logger.info(f"Executing cutPrimers command")
        self.configurator.logger.debug(f"Command: {cmd}")

        execute(executor, cmd)

        self.configurator.logger.info(
            "cutPrimers completed successfully. "
            f"See the log at '{primer_cutter_logpath}'")

        return (tr1, tr2)

class PTrimmer(LoggerMixin, IDataPreparator):
    """
        Class responsible for trimming \
            primer sequences from paired-end reads.
        It runs an external trimming tool and logs progress.
    """
    def __init__(self, configurator: Configurator):
        super().__init__(logger=configurator.logger)
        self.configurator = configurator

    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> (PathLike[AnyStr], PathLike[AnyStr]):
        """
            Performs primer trimming on the sample's read files.

            Args:
                sample (SampleDataContainer): \
                    The sample data with source file paths.
                executor (CommandExecutor or callable): \
                    Executor for running commands.

            Returns:
                Tuple of paths to the trimmed R1 and R2 files.
        """
        primer_cutter_logpath = os.path.join(
            sample.processing_logpath, 'pTrimmer.log')

        if not os.path.exists(os.path.dirname(primer_cutter_logpath)):
            os.makedirs(os.path.abspath(
                os.path.dirname(primer_cutter_logpath)))

        if not os.path.exists(primer_cutter_logpath):
            with open(primer_cutter_logpath, 'a') as f: pass

        R1_trimmed = os.path.join(
            sample.processing_path, insert_processing_infix(
                '.trimmed', os.path.basename(sample.R1_source)))
        R2_trimmed = os.path.join(
            sample.processing_path, insert_processing_infix(
                '.trimmed', os.path.basename(sample.R2_source)))

        cmd = ' '.join([
            self.configurator.config['ptrimmer'],
            '--seqtype', 'pair',
            '--ampfile',self.configurator.config['ampfile'],
            '--read1', sample.R1_source,
            '--trim1', R1_trimmed,
            '--read2', sample.R2_source,
            '--trim2', R2_trimmed,
            '--summary', os.path.join(
                sample.processing_logpath, 'pTrimmer.summary'), 
            '--mismatch', str(1),
            '--kmer', str(4),
            '>', primer_cutter_logpath,
            '2>&1',
            '--gzip'])

        self.configurator.logger.info(f"Executing pTrimmer command")
        self.configurator.logger.debug(f"Command: {cmd}")

        execute(executor, cmd)

        self.configurator.logger.info(
            "pTrimmer completed successfully. "
            f"See the log at '{primer_cutter_logpath}'")

        return (R1_trimmed, R2_trimmed)

class PrimerCutter(LoggerMixin):
    """Factory class for creating primer-related data preparators."""
    def __init__(
        self,
        configurator: Configurator,
        logger: Optional[logging.Logger]=None
    ):
        super().__init__(logger=configurator.logger if logger is None else logger)
        self.configurator = configurator

    @staticmethod
    def create_primer_cutter(
        configurator: Configurator,
        cutter_name: Optional[str]='cutprimers'
    ) -> IDataPreparator:
        """
            Factory method to instantiate a primer cutter object \
                based on the cutter_name.

            Args:
                configurator (Configurator): \
                    Configuration object with parameters and logger.
                cutter_name (str): \
                    Name of the cutter type ('cutprimers' or 'ptrimmer').

            Returns:
                IDataPreparator instance corresponding to the cutter.
        """
        match cutter_name.lower():
            case 'cutprimers':
                return CutPrimers(configurator)
            case 'ptrimmer':
                return PTrimmer(configurator)
