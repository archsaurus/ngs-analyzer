from src.core.base import *
from src.core.configurator import Configurator
from src.core.dependency_handler import DependencyHandler

global configurator, dependency_handler

configurator = Configurator()
dependency_handler = DependencyHandler()
dependency_handler.set_logger(configurator.logger)

class PatientDataContainer:
        def __init__(
            self,
            R1_source: PathLike[AnyStr],
            R2_source: PathLike[AnyStr]=None,
            id: int=0,
            processing_logpath: PathLike[AnyStr]=None,
            report_path: PathLike[AnyStr]=None
        ):
            # TODO: Validate current patient data
            self.R1_source = R1_source
            self.R2_source = R2_source
            
            self.id = id
            
            self.processing_logpath = os.path.abspath(os.path.join(configurator.log_path, f"patient_{self.id}")) if processing_logpath is None else processing_logpath
            self.report_path = os.path.abspath(os.path.join(configurator.args.outputDir, f"patient_{self.id}", "report")) if report_path is None else report_path

class Analyzer:
    def __init__(self): pass

    def analyze(self):        
        patient = PatientDataContainer(
            id=0,
            R1_source=configurator.args.readsFiles1,
            R2_source=configurator.args.readsFiles2
        )

        self.trimAdapters(patient, configurator.config['adapters'], configurator.args.outputDir)

    def trimAdapters(
        self,
        patient: PatientDataContainer,
        adapter_source: PathLike[AnyStr],
        output_dir: PathLike[AnyStr]
    ) -> None:
        """
            Удаление последовательностей адаптеров из прочтений программой Trimmomatic.

            Этап необходим для того, чтобы последовательности праймеров в прочтениях
            располагались максимально близко к концам прочтения.
            
            В этом случае их идентификация имеет более высокую точность.
        """
        """
            The current trimming steps by trimmomatic are:
                ILLUMINACLIP: Cut adapter and other illumina-specific sequences from the read.
                SLIDINGWINDOW: Perform a sliding window trimming, cutting once the average quality within the window falls below a threshold.
                LEADING: Cut bases off the start of a read, if below a threshold quality
                TRAILING: Cut bases off the end of a read, if below a threshold quality
                CROP: Cut the read to a specified length
                HEADCROP: Cut the specified number of bases from the start of the read
                MINLEN: Drop the read if it is below a specified length
                TOPHRED33: Convert quality scores to Phred-33
                TOPHRED64: Convert quality scores to Phred-64
        """
        if not os.path.exists(adapter_source.split(':')[0]): msg = f"Adapter sequence file '{adapter_source}' not found. Abort"
        elif not os.path.exists(patient.R1_source): msg = f"R1 reads file '{patient.R1_source}' not found. Abort"
        else:
            trim_logpath = os.path.abspath(os.path.join(
                patient.processing_logpath,
                os.path.basename(os.path.splitext(configurator.config['trimmomatic'])[0]))+'.log')

            trim_outpath = os.path.abspath(os.path.join(output_dir, f"patient_{patient.id}", 'trimmed_reads'))


            os.makedirs(trim_outpath, exist_ok=True)

            trimmer_args = {}

            if patient.R2_source is None: # SE
                trimmer_args = {
                    'mode': 'SE',
                    'basein': os.path.abspath(patient.R1_source),
                    'baseout': tuple(
                        insert_processing_infix(
                            infix, os.path.abspath(
                                os.path.join(
                                    trim_outpath,
                                    os.path.basename(patient.R1_source)
                                )
                            )
                        ) for infix in ['.paired', '.unpaired']
                    )
                }
            else: # PE
                trimmer_args = {
                    'mode': 'PE',
                    'basein': (
                        os.path.abspath(patient.R1_source),
                        os.path.abspath(patient.R2_source)
                    ),
                    'baseout': tuple(
                        insert_processing_infix(
                            infix, os.path.abspath(
                                os.path.join(
                                    trim_outpath,
                                    os.path.basename(patient.R1_source)
                                )
                            )
                        ) for infix in ['.paired_1', '.unpaired_1', '.paired_2', '.unpaired_2']
                    )
                }

            os.makedirs(os.path.dirname(trim_logpath), exist_ok=True)
            
            subprocess.run([
                configurator.config['java'], '-jar',
                configurator.config['trimmomatic'], trimmer_args['mode'],
                '-threads', str(configurator.args.threads),
                '-trimlog', trim_logpath,
                '-summary', os.path.abspath(os.path.join(
                    patient.processing_logpath,
                    os.path.basename(os.path.splitext(configurator.config['trimmomatic'])[0]))+'.summary'),
                '-basein', ' '.join(trimmer_args['basein']),
                '-baseout', ' '.join(trimmer_args['baseout']),
                f"ILLUMINACLIP:{os.path.abspath(configurator.config['adapters'])}",
                f"LEADING:{3}",
                f"TRAILING:{3}",
                f"SLIDINGWINDOW:{4}:{15}"
            ])

            del trimmer_args
            return

        configurator.logger.error(msg)
        raise FileNotFoundError(msg)

class ReportHandler: pass

if __name__ == '__main__':
    brca1_analyzer = Analyzer()
    brca1_analyzer.analyze()
