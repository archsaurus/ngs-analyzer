from src.settings import *

from src.core.patient_data_container import PatientDataContainer

class Analyzer():
    def __init__(self, cmd_caller: FunctionType=None):
        # TODO: cmd_caller must be a wrapper, returning call's output

        # I don't get it, but with calling subprocess.run(cmd) it can't walk the pathes,
        # but with os.system(' '.join(cmd)) it works. So on, using second way of calling
        self.cmd_caller = os.system if cmd_caller is None else cmd_caller

    def analyze(self):        
        patient = PatientDataContainer(
            id=0,
            R1_source=configurator.args.readsFiles1,
            R2_source=configurator.args.readsFiles2
        )

        self.trimAdapters(patient, configurator.args.outputDir)
        aligned_reads_path = self.alignReadsToReference(patient, configurator.config['reference'], os.path.abspath(os.path.join(configurator.args.outputDir, f"patient_{patient.id}")))
        bam_index_path, bam_filepath = self.groupReads(patient, aligned_reads_path)

    def trimAdapters(
        self,
        patient: PatientDataContainer,
        output_dir: PathLike[AnyStr]
    ) -> None:
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
                os.path.basename(os.path.splitext(configurator.config['trimmomatic'])[0]))+'.log')

            trim_outpath = os.path.abspath(os.path.join(output_dir, f"patient_{patient.id}", 'trimmed_reads'))

            os.makedirs(trim_outpath, exist_ok=True)

            trimmer_args = configurator.parse_configuration(target_section='Trimmomatic')

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

            if self.cmd_caller(' '.join([
                configurator.config['java'], '-jar',
                configurator.config['trimmomatic'], trimmer_args['mode'],
                '-threads', str(configurator.args.threads),
                '-'+trimmer_args['phred'],
                '-trimlog', "'"+trim_logpath+"'",
                '-summary', "'"+os.path.abspath(os.path.join(
                    patient.processing_logpath,
                    os.path.basename(os.path.splitext(configurator.config['trimmomatic'])[0]))+'.summary')+"'",
                ' ', ' '.join(trimmer_args['basein']),
                ' ', ' '.join(trimmer_args['baseout']),
                f"ILLUMINACLIP:'{os.path.abspath(trimmer_args['adapters'])}':{trimmer_args['illuminaclip']}",
                f"LEADING:{trimmer_args['leading']}" if 'leading' in trimmer_args else '',
                f"TRAILING:{trimmer_args['trailing']}" if 'trailing' in trimmer_args else '',
                f"SLIDINGWINDOW:{trimmer_args['slightwindow']}" if 'slightwindow' in trimmer_args else '',
                f"MINLEN:{trimmer_args['minlen']}" if 'minlen' in trimmer_args else '',
                f"CROP:{trimmer_args['crop']}" if 'crop' in trimmer_args else '',
                f"HEADCROP:{trimmer_args['headcrop']}" if 'headcrop' in trimmer_args else ''
            ])) != 0: exit(os.EX_SOFTWARE)

            del trimmer_args
            return

        configurator.logger.error(msg)
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
            os.path.basename(os.path.splitext(configurator.config['bwa-mem2'])[0]))+'_mem'+'.log'
        )

        try:
            configurator.logger.info(f"Starting to map patient '{patient.id}' reads to reference '{configurator.config['reference']}'")

            aligning_outpath = os.path.abspath(os.path.join(patient.processing_path, f"patient_{patient.id}.sam"))

            self.cmd_caller(' '.join([
                configurator.config['bwa-mem2'], 'mem', configurator.config['reference'],
                "'"+patient.R1_source+"'",
                "'"+patient.R2_source+"'" if not isinstance(patient.R2_source, type(None)) else '',
                '-o', "'"+aligning_outpath+"'",
                '-t', str(configurator.args.threads),
                '2>', aligning_logpath
            ]))

            configurator.logger.info(f"Alignment completed successfully. See it's log on '{aligning_logpath}'")

            return aligning_outpath
        except Exception as e:
            print(f"A fatal error '{e.__repr__()}' occured at '{e.__traceback__.tb_frame}'", file=sys.stdout)
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
            configurator.log_path,
            f"{os.path.basename(configurator.config['picard'])}_AddOrReplaceReadGroups.log")
        )

        picard_grouping_outpath = os.path.abspath(os.path.join(
            patient.processing_path,
            f"patient_{patient.id}.sorted.read_groups")
        )

        configurator.logger.info(f"Start grouping aligned reads from '{input_path}' to '{picard_grouping_outpath}'")

        self.cmd_caller(' '.join([
            configurator.config['java'], '-jar', configurator.config['picard'],
            'AddOrReplaceReadGroups',
            '-INPUT', input_path,
            '-OUTPUT', picard_grouping_outpath+".bam",
            '-SORT_ORDER', 'coordinate',
            '-CREATE_INDEX', 'TRUE',
            '2>', picard_grouping_logpath,
            # region TODO: Must add [Meta] section to config.ini for simplify stamping
            '-RGLB', 'MiSeq',
            '-RGPL', 'Illumina',
            '-RGPU', 'barcode',
            '-RGSM', f"patient_{patient.id}"
            # endregion
        ]))

        configurator.logger.info(f"picard Grouping Output has successfully done (The SAM-file has successfully converted to BAM). See it's log at '{picard_grouping_logpath}'")
        return (picard_grouping_outpath + ext for ext in [".bai", ".bam"])

    def printReads(
        input_path: PathLike[AnyStr],
        output_path: PathLike[AnyStr],
        patient: PatientDataContainer
    ) -> None:
        print_reads_logpath = os.path.abspath(os.path.join(
            configurator.log_path,
            f"{os.path.basename(configurator.config['gatk'])}_PrintReads.log")
        )

        touch(gatkPrintReadsLogPath)
