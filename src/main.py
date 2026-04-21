#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main module for the data analysis pipeline."""

# region Imports
import os

from src.configurator import Configurator
from src.analyzer import BRCAAnalyzer
from src.core.sample_data_factory import SampleDataFactory

from src.utils.report_aggregator import report_aggregator

from src import demultiplexor_adapter
from src import table_manager
# endregion


def main():
    """Main function to initiate and run the data analysis pipeline.

        Loads configuration, initializes logging, dependency handler,
        and the BRCA1 analyzer. Optionally runs additional modules
        (e.g., table management or demultiplexing).
    """
    configurator = Configurator()
    main_logger = configurator.logger

    brca1_analyzer = BRCAAnalyzer(
        configurator=configurator,
        cmd_caller=os.system
    )

    if configurator.args.table_manager_flag:
        table_manager.main()

    if configurator.args.demultiplexor_flag:
        demultiplexor_adapter.main()

    sample_factory = SampleDataFactory(
        outpath=configurator.output_dir,
        logger=main_logger
    )

    tm_config = configurator.parse_configuration(
        base_config_filepath=configurator.args.configFilepath,
        target_section='TableManager')

    if 'dump-file' in tm_config:
        with open(tm_config['dump-file'], 'r', encoding='utf-8') as dump_fd:
            for dump_string in dump_fd.readlines():
                sample_id = dump_string.split(';')[0].strip()

                sample = sample_factory.parse_sample_data(
                    configurator.config['reads-dir'], sample_id)

                if sample is None:
                    main_logger.warning(
                        f"Skip '{sample_id.strip()}' sample")
                    continue

                try:
                    brca1_analyzer.prepare_data(sample)

                except Exception as e:
                    main_logger.critical(e)
                    raise e

                brca1_analyzer.analyze(sample)

                report_aggregator.aggregate_report(sample=sample)

    else:
        runtime_error_msg = (
            'The analyzer requires a sample list to function. '
            'Provide the sample list in the TableManager.dump-file field '
            'of the configuration file.'
        )

        main_logger.critical(runtime_error_msg)
        raise RuntimeError(runtime_error_msg)


if __name__ == '__main__':
    main()
