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

        self.trimAdapters(patient, configurator.args.outputDir)

    def trimAdapters(
        self,
        patient: PatientDataContainer,
        output_dir: PathLike[AnyStr]
    ) -> None:
        """
            Удаление последовательностей адаптеров из прочтений программой Trimmomatic.

            Этап необходим для того, чтобы последовательности праймеров в прочтениях
            располагались максимально близко к концам прочтения.
            
            В этом случае их идентификация имеет более высокую точность.
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

            # I don't get it, but with calling subprocess.run(cmd) it can't walk the pathes,
            # but with os.system(' '.join(cmd)) it works. So on, using second way of calling
            if os.system(' '.join([
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

class ReportHandler: pass

if __name__ == '__main__':
    brca1_analyzer = Analyzer()
    brca1_analyzer.analyze()
