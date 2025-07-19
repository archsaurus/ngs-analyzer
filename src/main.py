from src.core.base import *

from src.core.patient_data_container import PatientDataContainer
from src.core.analyzer import Analyzer

from src.settings import dependency_handler, configurator

def main():
    brca1_analyzer = Analyzer()

    tm_config = configurator.parse_configuration(target_section='ExcelTableManager')
    reads_list = os.listdir(path=configurator.config['reads-dir'])
    
    if 'sample_sheet' in tm_config:
        with open(tm_config['sample_sheet'], 'r') as sample_sheet:

            for sample_string in sample_sheet.readlines():
                sample_id = sample_string.split(';')[0]
                
                regexp_filter = re.compile(rf"^.*{sample_id}.*")
                patient_reads_source_pathes = filter(regexp_filter.match, reads_list)

                sample_r1_path, sample_r2_path = None, None

                for read in patient_reads_source_pathes:
                    if 'R1' in read:
                        sample_r1_path = read
                        continue
                    if 'R2' in read:
                        sample_r2_path = read
                        continue
                if all((sample_r1_path is not None, sample_r2_path is not None)):
                    patient = PatientDataContainer(
                        id=sample_id,
                        R1_source=os.path.join(configurator.config['reads-dir'], sample_r1_path),
                        R2_source=os.path.join(configurator.config['reads-dir'], sample_r2_path)
                    )
                    
                    brca1_analyzer.context.update(brca1_analyzer.prepareData(patient))
                else:
                    configurator.logger.critical(f"Can't find {'R1' if sample_r1_path is None else 'R2'} for sample '{sample_id}'")
                    continue


        brca1_analyzer.analyze()

if __name__ == '__main__':
    if configurator.args is None:
        configurator.args = configurator.parse_argvars()
        configurator.output_dir = configurator.set_output_directory(configurator.args.outputDir)
    
    main()
