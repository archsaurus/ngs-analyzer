#!/bin/python
"""Main module for the data analysis pipeline."""

# region Imports
import os

from src.configurator import Configurator
from src.analyzer import Analyzer
from src.core.sample_data_factory import SampleDataFactory

from src.utils.util import reg_tuple_generator
from src.utils.report_agregator import report_agregator

from src import demultiplexor_adapter
from src import table_manager
# endregion

def main():
    """
        Main function to initiate and run the data analysis pipeline.

        Loads configuration, initializes logging, dependency handler,  \
        and the BRCA1 analyzer.  Optionally runs additional modules \
        (e.g., table management or demultiplexing).
    """
    configurator = Configurator(
        config_path=os.path.abspath(os.path.join(
            os.path.curdir, 'src', 'conf', 'config.ini')
            ))

    main_logger = configurator.logger

    brca1_analyzer = Analyzer(
        configurator = configurator, cmd_caller = os.system)

    if configurator.args.table_manager_flag:
        table_manager.main()

    if configurator.args.demultiplexor_flag:
        demultiplexor_adapter.main()

    sample_factory = SampleDataFactory(logger=main_logger)
    tm_config = configurator.parse_configuration(
        target_section='TableManager')

    if 'dump-file' in tm_config:
        with open(tm_config['dump-file'], 'r', encoding='utf-8') as dump_fd:
            for dump_string in dump_fd.readlines()[1:]:
                sample_id = dump_string.split(';')[0].strip()

                sample = sample_factory.parse_sample_data(
                    configurator.config['reads-dir'], sample_id)

                if sample is None:
                    main_logger.warning(
                        f"Skip '{sample_id.strip()}' sample")
                    continue

                sample_base_outpath = os.path.abspath(os.path.join(
                    configurator.output_dir, sample_id))

                sample.processing_logpath = os.path.join(
                    sample_base_outpath, "log")
                sample.processing_path = sample_base_outpath
                sample.report_path =  os.path.join(
                    sample_base_outpath, "report")

                brca1_analyzer.prepare_data(sample)
                brca1_analyzer.analyze(sample)

                # Need to fetch chromosome's number from reads
                # before proceed to report generation.
                target_regions=[
                    reg_tuple_generator(configurator, 'chr03-interval'),
                    reg_tuple_generator(configurator, 'chr06-interval'),
                    reg_tuple_generator(configurator, 'chr10-interval'),
                    reg_tuple_generator(configurator, 'chr13-interval'),
                    reg_tuple_generator(configurator, 'chr14-interval'),
                    reg_tuple_generator(configurator, 'chr17-interval'),
                    reg_tuple_generator(configurator, 'chr19-interval')
                ]

                report_agregator.agregate_report(
                    target_regions=target_regions,
                    sample=sample)

if __name__ == '__main__':
    main()
