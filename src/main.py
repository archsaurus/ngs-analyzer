from src.core.base import *

from src.core.sample_data_container import SampleDataContainer

from src.dependency_handler import DependencyHandler
from src.configurator import Configurator
from src.demultiplexor_adapter import DemultiplexorAdapterFactory
from src.analyzer import Analyzer

from src.core.sample_data_factory import SampleDataFactory

def main():
    configurator = Configurator(config_path=os.path.abspath(os.path.join(os.path.curdir, 'src', 'conf', 'config.ini')))
    
    main_logger = configurator.logger
    
    dependency_handler = DependencyHandler()
    dependency_handler.set_logger(main_logger)
    

    tm_config = configurator.parse_configuration(target_section='TableManager')
    reads_list = os.listdir(path=configurator.config['reads-dir'])
    
    is_demultiplexing_needed = False
    if is_demultiplexing_needed:
        demultiplexor_adapter = DemultiplexorAdapterFactory.create_adapter(
            config=configurator.parse_configuration(target_section='DemultiplexorAdapter'),
            logger=main_logger,
            caller=os.system
        )

        demultiplexor_adapter.demultiplex()

    sample_factory = SampleDataFactory(logger=main_logger)
    
    
    brca1_analyzer = Analyzer(configurator=configurator, cmd_caller=os.system)

    
    if 'sample-sheet' in tm_config:
        with open(tm_config['sample-sheet'], 'r') as sample_sheet:
            for sample_string in sample_sheet.readlines():
                sample_id = sample_string.split(';')[0]

                sample = sample_factory.parse_sample_data(
                    path=configurator.config['reads-dir'],
                    sample_id=sample_id
                )
                if sample is None:
                    main_logger.warning(f"Skip '{sample_id}' sample")
                    continue
                
                sample_base_outpath = os.path.abspath(os.path.join(configurator.output_dir, sample_id))
                
                sample.processing_logpath = os.path.join(sample_base_outpath, "log")
                sample.processing_path = sample_base_outpath
                sample.report_path =  os.path.join(sample_base_outpath, "report")


                brca1_analyzer.context.update(brca1_analyzer.prepareData(sample))
                input('end')

    brca1_analyzer.analyze()

if __name__ == '__main__': main()
