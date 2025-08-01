from . import *

def main():
    configurator = Configurator(config_path=os.path.abspath(os.path.join(os.path.curdir, 'src', 'conf', 'config.ini')))
    main_logger = configurator.logger

    dependency_handler = DependencyHandler(logger=main_logger)

    import subprocess
    brca1_analyzer = Analyzer(configurator=configurator, cmd_caller=subprocess.run)

    if True:
        from src import table_manager
        table_manager.main()

    is_demultiplexing_needed = False
    if is_demultiplexing_needed:
        from src.demultiplexor_adapter import main
        demultiplexor_adapter.main()

    sample_factory = SampleDataFactory(logger=main_logger)
    tm_config = configurator.parse_configuration(target_section='TableManager')
    
    if 'dump-file' in tm_config:
        with open(tm_config['dump-file'], 'r') as dump_fd:
            for dump_string in dump_fd.readlines()[1:]:
                sample_id = dump_string.split(';')[0]
                sample = sample_factory.parse_sample_data(configurator.config['reads-dir'], sample_id)
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
