from . import *

class AdapterTrimmer(LoggerMixin, IDataPreparator):
    def __init__(self, configurator):
        super().__init__(logger=configurator.logger)
        self.configurator = configurator
    
    def perform(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable]
    ) -> list[PathLike[AnyStr]]:
        """
            Removal of adapter sequences from reads using the Trimmomatic program.
            This step is necessary to ensure that primer sequences in the reads are positioned as close as possible to the ends of the reads.
            In this way, their identification is more accurate.
            Args:
                sample (SampleDataContainer): The container holding sample's sequencing data, including raw reads path.
                output_dir (PathLike[AnyStr]): Directory where the trimmed reads and output files will be saved.
            Returns:
                None
        """
        
        if not os.path.exists(sample.R1_source):
            msg = f"R1 reads file '{sample.R1_source}' not found. Abort"
            self.configurator.logger.critical(msg)
            raise FileNotFoundError(msg)

        trim_outpath = os.path.abspath(os.path.join(sample.processing_path, 'trimmed_reads'))
        os.makedirs(trim_outpath, exist_ok=True)
        os.makedirs(sample.processing_logpath, exist_ok=True)

        trimmer_args = self.configurator.parse_configuration(target_section='Trimmomatic')


        outpathes = [t for t in [insert_processing_infix(
            infix, os.path.abspath(
                os.path.join(
                    trim_outpath,
                    os.path.basename(sample.R1_source)
                )
            )
        ) for infix in ['.paired', '.unpaired']]]
        if sample.R2_source is None: # SE
            trimmer_args.update({
                'mode': 'SE',
                'basein': sample.R1_source,
                'baseout': tuple(outpathes)
            })
        else: # PE
            if not os.path.exists(sample.R2_source):
                msg = f"R2 reads file '{sample.R2_source}' not found. Abort"
                
                self.configurator.logger.critical(msg)
                raise FileNotFoundError(msg)

            outpathes.extend(
                [t for t in [insert_processing_infix(
                    infix, os.path.abspath(
                        os.path.join(
                            trim_outpath,
                            os.path.basename(sample.R2_source)
                        )
                    )
                ) for infix in ['.paired', '.unpaired']]])

            trimmer_args.update({
                'mode': 'PE',
                'basein': (sample.R1_source, sample.R2_source),
                'baseout': tuple(outpathes)
            })

        os.makedirs(os.path.dirname(sample.processing_logpath), exist_ok=True)

        trimmer_summary_path = os.path.abspath(os.path.join(
            sample.processing_logpath,
            os.path.basename(os.path.splitext(self.configurator.config['trimmomatic'])[0]))+'.summary'
        )

        trimmer_cmd = ' '.join([
            self.configurator.config['java'], '-jar',
            self.configurator.config['trimmomatic'], trimmer_args['mode'],
            '-threads', str(self.configurator.args.threads),
            f"-{trimmer_args['phred']}",
            '-summary', trimmer_summary_path,
            '', ' '.join(trimmer_args['basein']),
            '', ' '.join(trimmer_args['baseout']),
            f"ILLUMINACLIP:{os.path.abspath(trimmer_args['adapters'])}:{trimmer_args['illuminaclip']}",
            f"LEADING:{trimmer_args['leading']}" if 'leading' in trimmer_args else '',
            f"TRAILING:{trimmer_args['trailing']}" if 'trailing' in trimmer_args else '',
            f"SLIDINGWINDOW:{trimmer_args['slightwindow']}" if 'slightwindow' in trimmer_args else '',
            f"MINLEN:{trimmer_args['minlen']}" if 'minlen' in trimmer_args else '',
            f"CROP:{trimmer_args['crop']}" if 'crop' in trimmer_args else '',
            f"HEADCROP:{trimmer_args['headcrop']}" if 'headcrop' in trimmer_args else '',
            '>> ', trimmer_summary_path
        ])

        self.configurator.logger.debug(f"Executing Trimmomatic with command: {trimmer_cmd}")

        execute(executor, trimmer_cmd)

        self.configurator.logger.info(f"Trimming completed successfully. See the log at '{trimmer_summary_path}'")
        
        paired_trimmed_reads = []
        for path in trimmer_args['baseout']:
            if '.paired' in path: paired_trimmed_reads.append(path)
        return paired_trimmed_reads
