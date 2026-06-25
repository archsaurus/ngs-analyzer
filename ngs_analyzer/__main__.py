#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Main module for the data analysis pipeline."""

# region Imports
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from ngs_analyzer.core.configuration.configurator import Configurator
from ngs_analyzer.core.data_processing.analyzer.analyzer import (Analyzer,
                                                                 BRCAAnalyzer)
from ngs_analyzer.core.data_processing.sample_input import sample_data_factory
from ngs_analyzer.core.demultiplexing import demultiplexor_adapter
from ngs_analyzer.core.report import report_aggregator
from ngs_analyzer.core.table_manager import table_manager

# endregion


def process_sample(
    sample_id: str,
    sample_factory: sample_data_factory.SampleDataFactory,
    analyzer: Analyzer,
    reads_dir: str,
    logger,
) -> dict:
    """Process a single sample (wrapper for concurrent executor).

    Args:
        sample_id: Sample identifier
        sample_factory: Factory for parsing sample data
        analyzer: Analyzer instance
        reads_dir: Path to reads directory
        logger: logging.Logger instance

    Returns:
        dict with sample_id, status, and error message (if any)
    """
    result = {
        'sample_id': sample_id,
        'status': 'success',
        'error': None,
    }

    try:
        sample = sample_factory.parse_sample_data(reads_dir, sample_id)

        if sample is None:
            logger.warning(f'Skip "{sample_id}" sample')
            result['status'] = 'skipped'
            return result

        analyzer.prepare_data(sample)
        analyzer.analyze(sample)
        report_aggregator.aggregate_report(sample=sample)

        logger.info(f'Successfully processed "{sample_id}"')

    except Exception as e:
        logger.critical(f'Failed to process "{sample_id}": {e}')
        result['status'] = 'failed'
        result['error'] = str(e)

    return result


def main():
    """Initiate and run the data analysis pipeline.

    Loads configuration, initializes logging, dependency handler,
    and the analyzer. Optionally runs additional modules
    (e.g., table management or demultiplexing).
    """
    configurator = Configurator()
    main_logger = configurator.logger

    analyzer = BRCAAnalyzer(
        configurator=configurator,
        cmd_caller=os.system,
    )

    if configurator.args.table_manager_flag:
        table_manager.main()

    if configurator.args.demultiplexor_flag:
        demultiplexor_adapter.main()

    sample_factory = sample_data_factory.SampleDataFactory(
        outpath=configurator.output_dir,
        logger=main_logger,
    )

    tm_config = configurator.parse_configuration(
        base_config_filepath=configurator.args.configFilepath,
        target_section='TableManager')

    if 'dump-file' not in tm_config:
        runtime_error_msg = (
            'The analyzer requires a sample list to function. '
            'Provide the sample list in the TableManager.dump-file field '
            'of the configuration file.'
        )

        main_logger.critical(runtime_error_msg)
        raise RuntimeError(runtime_error_msg)

    sample_ids = []
    with open(tm_config['dump-file'], 'r', encoding='utf-8') as dump_fd:
        for dump_string in dump_fd.readlines():
            sample_id = dump_string.split(';')[0].strip()
            sample_ids.append(sample_id)

    main_logger.info(f'Found {len(sample_ids)} samples to process')

    reads_dir = configurator.config['reads-dir']

    if configurator.args.workers == 1:
        main_logger.info('Processing samples sequentially...')

        failed_samples = []
        for sample_id in sample_ids:
            result = process_sample(
                sample_id=sample_id,
                sample_factory=sample_factory,
                analyzer=analyzer,
                reads_dir=reads_dir,
                logger=main_logger,
            )

            if result['status'] == 'failed':
                failed_samples.append(sample_id)

        if failed_samples:
            main_logger.warning(
                f'Failed to process {len(failed_samples)} '
                f'samples: {failed_samples}',
            )

    else:
        main_logger.info(
            f'Processing samples in parallel mode '
            f'with {configurator.args.workers} workers...',
        )

        results = []
        failed_samples = []

        with ThreadPoolExecutor(
            max_workers=configurator.args.workers,
            thread_name_prefix='sample_worker',
        ) as executor:
            futures = {
                executor.submit(
                    process_sample,
                    sample_id=sample_id,
                    sample_factory=sample_factory,
                    analyzer=analyzer,
                    reads_dir=reads_dir,
                    logger=main_logger,
                ): sample_id
                for sample_id in sample_ids
            }

            # Process results as they complete
            for future in as_completed(futures):
                sample_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)

                    if result['status'] == 'failed':
                        failed_samples.append(sample_id)

                except Exception as e:
                    main_logger.critical(f'Exception for "{sample_id}": {e}')
                    failed_samples.append(sample_id)
                    results.append({
                        'sample_id': sample_id,
                        'status': 'failed',
                        'error': str(e),
                    })

        # Summary
        success_count = len([r for r in results if r['status'] == 'success'])
        main_logger.info(
            f'Completed: {success_count} successful, '
            f'{len(failed_samples)} failed out of {len(sample_ids)} samples',
        )

        if failed_samples:
            main_logger.warning(f'Failed samples: {failed_samples}')

    main_logger.info('Pipeline completed')


if __name__ == '__main__':
    main()
