from src.core.base import *

from src.configurator import Configurator
from src.core.patient_data_container import PatientDataContainer

class Analyzer(metaclass=SingletonMeta):
    def __init__(
        self,
        configurator: Configurator,
        cmd_caller: FunctionType=None
    ):
        self.configurator = configurator
        # TODO: cmd_caller must be a wrapper, returning call's output

        # I don't get it, but with calling subprocess.run(cmd) it can't walk the pathes,
        # but with os.system(' '.join(cmd)) it works. So on, using second way of calling
        self.cmd_caller = os.system if cmd_caller is None else cmd_caller
        self.context = {}

    def prepareData(self, patient: PatientDataContainer) -> dict[str, dict[str, PathLike[AnyStr]]]:
        """
            Performs data preparation for a comprehensive analysis pipeline of patient sequencing data.

            The method executes the following steps:
            1. Initializes a PatientDataContainer with source read files.
            2. Trims adapter sequences from the raw reads.
            3. Selects paired-end reads after trimming, if available.
            4. Aligns the processed reads to a reference genome.
            5. Groups aligned reads into a BAM file and creates an index.
            6. Performs Base Quality Score Recalibration (BQSR) on the BAM file.

            This process prepares the patient's sequencing data for downstream analysis such as variant calling.

            Args:
                patient (PatientDataContainer): The container holding patient-specific sequencing data, \
                including source read file paths and patient identifiers.
            Returns:
                dict[str, dict[str, PathLike[AnyStr]]]: A dictionary containing a patient id \
                and a dictionary of file paths needed for downstream analysis steps, \
                such as aligned and recalibrated BAM files.
        """
        trimmed_reads_pathes = self.trimAdapters(patient, self.configurator.args.outputDir)
        paired_trimmed_reads = []
        for path in trimmed_reads_pathes:
            if '.paired' in path: paired_trimmed_reads.append(path)
        if len(paired_trimmed_reads) == 2:
            patient.R1_source = paired_trimmed_reads[0]
            patient.R2_source = paired_trimmed_reads[1]
        
        aligned_reads_path = self.alignReadsToReference(
            patient,
            self.configurator.config['reference'],
            os.path.abspath(os.path.join(self.configurator.args.outputDir,f"patient_{patient.id}"))
        )
        
        bam_index_path, bam_filepath = self.groupReads(patient, aligned_reads_path)
        recalibrated_bam_filepath = self.performBQSR(patient, bam_filepath)

        return {patient.id: {
            'bam_filepath': bam_filepath,
            'recalibrated_bam_filepath': recalibrated_bam_filepath
        }}

    def trimAdapters(
        self,
        patient: PatientDataContainer,
        output_dir: PathLike[AnyStr]
    ) -> list[PathLike[AnyStr]]:
        """
            Removal of adapter sequences from reads using the Trimmomatic program.
            This step is necessary to ensure that primer sequences in the reads are positioned as close as possible to the ends of the reads.
            In this way, their identification is more accurate.
            Args:
                patient (PatientDataContainer): The container holding patient's sequencing data, including raw reads path.
                output_dir (PathLike[AnyStr]): Directory where the trimmed reads and output files will be saved.
            Returns:
                None
        """
        if not os.path.exists(patient.R1_source): msg = f"R1 reads file '{patient.R1_source}' not found. Abort"
        else:
            trim_logpath = os.path.abspath(os.path.join(
                patient.processing_logpath,
                os.path.basename(os.path.splitext(self.configurator.config['trimmomatic'])[0]))+'.log')

            trim_outpath = os.path.abspath(os.path.join(output_dir, f"patient_{patient.id}", 'trimmed_reads'))

            os.makedirs(trim_outpath, exist_ok=True)

            trimmer_args = self.configurator.parse_configuration(target_section='Trimmomatic')

            if patient.R2_source is None: # SE
                trimmer_args.update({
                    'mode': 'SE',
                    'basein': "'"+os.path.abspath(patient.R1_source)+"'",
                    'baseout': tuple(
                        "'"+t+"'" for t in [insert_processing_infix(
                            infix, os.path.abspath(
                                os.path.join(
                                    trim_outpath,
                                    os.path.basename(patient.R1_source)
                                )
                            )
                        ) for infix in ['.paired', '.unpaired']]
                    )
                })
            else: # PE
                trimmer_args.update({
                    'mode': 'PE',
                    'basein': (
                        "'"+os.path.abspath(patient.R1_source)+"'",
                        "'"+os.path.abspath(patient.R2_source)+"'"
                    ),
                    'baseout': tuple(
                        "'"+t+"'" for t in [insert_processing_infix(
                            infix, os.path.abspath(
                                os.path.join(
                                    trim_outpath,
                                    os.path.basename(patient.R1_source)
                                )
                            )
                        ) for infix in ['.paired_1', '.unpaired_1', '.paired_2', '.unpaired_2']]
                    )
                })

            os.makedirs(os.path.dirname(trim_logpath), exist_ok=True)

            trimmer_summary_path = os.path.abspath(os.path.join(
                patient.processing_logpath,
                os.path.basename(os.path.splitext(self.configurator.config['trimmomatic'])[0]))+'.summary'
            )

            trimmer_cmd = ' '.join([
                self.configurator.config['java'], '-jar',
                self.configurator.config['trimmomatic'], trimmer_args['mode'],
                '-threads', str(self.configurator.args.threads),
                '-'+trimmer_args['phred'],
                # '-trimlog', "'"+trim_logpath+"'", # Not human-readable output
                '-summary', "'"+trimmer_summary_path+"'",
                ' ', ' '.join(trimmer_args['basein']),
                ' ', ' '.join(trimmer_args['baseout']),
                f"ILLUMINACLIP:'{os.path.abspath(trimmer_args['adapters'])}':{trimmer_args['illuminaclip']}",
                f"LEADING:{trimmer_args['leading']}" if 'leading' in trimmer_args else '',
                f"TRAILING:{trimmer_args['trailing']}" if 'trailing' in trimmer_args else '',
                f"SLIDINGWINDOW:{trimmer_args['slightwindow']}" if 'slightwindow' in trimmer_args else '',
                f"MINLEN:{trimmer_args['minlen']}" if 'minlen' in trimmer_args else '',
                f"CROP:{trimmer_args['crop']}" if 'crop' in trimmer_args else '',
                f"HEADCROP:{trimmer_args['headcrop']}" if 'headcrop' in trimmer_args else ''
            ])

            self.configurator.logger.info(f"Executing Trimmomatic command")
            self.configurator.logger.debug(f"Command: {trimmer_cmd}")

            self.cmd_caller(trimmer_cmd)

            self.configurator.logger.info(f"Trimming completed successfully. See the log at '{trimmer_summary_path}'")

            return trimmer_args['baseout']

        self.configurator.logger.error(msg)
        raise FileNotFoundError(msg)

    # TODO: Have to cover the case of no index
    def alignReadsToReference(
        self,
        patient: PatientDataContainer,
        reference_source: PathLike[AnyStr],
        output_path: PathLike[AnyStr]
    ) -> PathLike[AnyStr]:
        """
            Mapping reads to the reference human genome.

            This is the stage at which, for each read, it is determined
            where a similar sequence is located in the reference genome,
            and their alignment is performed relative to each other.

            Args:
                patient (PatientDataContainer): The container holding patient's sequencing data, including raw reads path.
                reference_source (PathLike[AnyStr]): Path to the reference genome file to which reads will be aligned.
                output_path (PathLike[AnyStr]): Path where the alignment results, including CIGAR strings, will be saved.
            Returns:
                None
        """
        aligning_logpath = os.path.abspath(os.path.join(
            patient.processing_logpath,
            os.path.basename(os.path.splitext(self.configurator.config['bwa-mem2'])[0]))+'-mem'+'.log'
        )

        try:
            aligning_outpath = os.path.abspath(os.path.join(patient.processing_path, f"patient_{patient.id}.sam"))
            
            reads_mapping_cmd = ' '.join([
                self.configurator.config['bwa-mem2'], 'mem', self.configurator.config['reference'],
                "'"+patient.R1_source+"'",
                "'"+patient.R2_source+"'" if not isinstance(patient.R2_source, type(None)) else '',
                '-o', "'"+aligning_outpath+"'",
                '-t', str(self.configurator.args.threads),
                '2>', aligning_logpath
            ])

            self.configurator.logger.info(f"Starting to map patient '{patient.id}' reads to reference '{self.configurator.config['reference']}'")
            self.configurator.logger.debug(f"Command: {reads_mapping_cmd}")

            self.cmd_caller(reads_mapping_cmd)

            self.configurator.logger.info(f"Alignment completed successfully. See the log at '{aligning_logpath}'")

            return aligning_outpath
        except Exception as e:
            self.configurator.logger.critical(f"A fatal error '{e.__repr__()}' occured at '{e.__traceback__.tb_frame}'")
            exit(os.EX_SOFTWARE)

    def groupReads(
        self,
        patient: PatientDataContainer,
        input_path: PathLike[AnyStr]
    ) -> (PathLike[AnyStr], PathLike[AnyStr]):
        """
            Conversion of the read mapping output on the reference (SAM file) to a BAM file,
            sorting of reads, addition of read group information, and indexing of the BAM file using Picard.

            BAM files occupy less disk space, and due to indexing and their binary format,
            interaction speed with these files is significantly higher.
            Args:
                patient (PatientDataContainer): The container with patient's data, may be used for naming or metadata.
                input_path (PathLike[AnyStr]): Path to the input SAM file generated from mapping.

            Returns:
                tuple: A pair of paths -
                    (index_path, bam_path)
                    where index_path is the path to the BAM index file (.bai),
                    and bam_path is the path to the sorted BAM file.
        """
        picard_grouping_logpath = os.path.abspath(os.path.join(
            patient.processing_logpath,
            f"{os.path.splitext(os.path.basename(self.configurator.config['picard']))[0]}-AddOrReplaceReadGroups.log")
        )

        picard_grouping_outpath = os.path.abspath(os.path.join(
            patient.processing_path,
            f"patient_{patient.id}.sorted.read_groups")
        )

        group_reads_cmd = ' '.join([
            self.configurator.config['java'], '-jar', self.configurator.config['picard'],
            'AddOrReplaceReadGroups',
            '-INPUT', input_path,
            '-OUTPUT', picard_grouping_outpath+'.bam',
            '-SORT_ORDER', 'coordinate',
            '-CREATE_INDEX', 'TRUE',
            '2>', picard_grouping_logpath,
            # region TODO: Must add [Meta] section to config.ini for simplify stamping
            '-RGLB', 'MiSeq',
            '-RGPL', 'Illumina',
            '-RGPU', 'barcode',
            '-RGSM', f"patient_{patient.id}"
            # endregion
        ])

        self.configurator.logger.info("Start grouping aligned reads")
        self.configurator.logger.debug(f"Command: {group_reads_cmd}")

        self.cmd_caller(group_reads_cmd)

        self.configurator.logger.info(f"Grouping reads has successfully done. See the log at '{picard_grouping_logpath}'")
        return (picard_grouping_outpath + ext for ext in [".bai", ".bam"])

    def performBQSR(
        self,
        patient: PatientDataContainer,
        input_path: PathLike[AnyStr]
    ) -> PathLike[AnyStr]:
        """
            Performs Base Quality Score Recalibration (BQSR) using GATK's BaseRecalibrator and ApplyBQSR tools.

            This method executes two sequential GATK commands:
            1. BaseRecalibrator to generate a recalibration table.
            2. ApplyBQSR to produce a recalibrated BAM file.

            Args:
                patient (PatientDataContainer): The patient data container with processing info.
                input_path (PathLike[AnyStr]): Path to the input BAM file to be recalibrated.

            Returns:
                PathLike[AnyStr]: Path to the recalibrated BAM file.

            Raises:
                Exception: Propagates any exceptions raised during command execution.
        """
        base_recal_logpath = os.path.abspath(os.path.join(
            patient.processing_logpath,
            f"{os.path.basename(self.configurator.config['gatk'])}-BaseRecalibrator.log")
        )

        racalibration_table_path = os.path.abspath(os.path.join(
            patient.processing_path, f"patient_{patient.id}.table"
        ))

        base_recal_cmd_str = ' '.join([
            self.configurator.config['gatk'], 'BaseRecalibrator',
            '--input', input_path,
            '--output', racalibration_table_path,
            '--reference', self.configurator.config['reference'],
            # TODO: Have to make it works with a list of sites
            '--known-sites', self.configurator.config['annotation-database'],
            '--intervals', self.configurator.config['chr13-interval'],
            '--intervals', self.configurator.config['chr17-interval'],
            '2>', base_recal_logpath
        ])

        try:
            self.configurator.logger.info("Executing BaseRecalibrator command")
            self.configurator.logger.debug(f"Command: {base_recal_cmd_str}")

            self.cmd_caller(base_recal_cmd_str)

            self.configurator.logger.info(f"BaseRecalibrator completed successfully. See the log at '{base_recal_logpath}'")

            recalibrated_outpath = insert_processing_infix('.recalibrated', input_path)
            apply_bqsr_logpath = base_recal_logpath.replace('BaseRecalibrator', 'ApplyBQSR')
            
            # Construct the ApplyBQSR command by modifying the original BaseRecalibrator command string
            apply_bqsr_cmd_str = ' '.join([
                base_recal_cmd_str.replace(
                    'BaseRecalibrator', 'ApplyBQSR'
                ).replace(
                    racalibration_table_path, recalibrated_outpath
                ).replace(
                    base_recal_logpath, apply_bqsr_logpath
                ).replace(
                    '--known-sites', ''
                ).replace(
                    self.configurator.config['annotation-database'], ''
                ),
                '--bqsr-recal-file', racalibration_table_path
            ])
            
            self.configurator.logger.info("Executing ApplyBQSR command")
            self.configurator.logger.debug(f"Command: {apply_bqsr_cmd_str}")
            
            self.cmd_caller(apply_bqsr_cmd_str)

            self.configurator.logger.info(f"ApplyBQSR completed successfully. See the log at '{apply_bqsr_logpath}'")

            return recalibrated_outpath
        except Exception as e:
            self.configurator.logger.critical(
                f"Error '{e.__repr__()}' occured at line '{e.__traceback__.tb_frame.f_lineno}' during BQSR"
            )

            exit(os.EX_SOFTWARE)

    def analyze(self): pass

    def __repr__(self): return f"{self.__class__}(configurator={self.configurator}, cmd_caller={self.cmd_caller}, context={self.context})"

    def __str__(self): return f"{self.context}"
