"""
    Module responsible for loading and aggregating data from
    various input files specified in a configuration file.
    It utilizes the TableManagerFactory to create and interact
    with a suitable TableManager instance, processing and saving
    the aggregated data.
"""

# region Imports
import os

from src.configurator import Configurator
from src.utils.table_manager.table_manager_factory import TableManagerFactory
# endregion

def main():
    """
        Loads configuration, creates a TableManager instance,
        aggregates data from specified files (adapters, indexes, samples),
        and saves the aggregated data to a file.

        Raises:
            Exception:
            If any error occurs during configuration parsing,
            TableManager creation, data aggregation, or saving.

        Returns:
            None. Prints success message or error message to console.
    """
    configurator = Configurator()

    tm_config = configurator.parse_configuration(
        target_section='TableManager')

    _, table_ext = os.path.splitext(tm_config['adapter-list'])

    excel_tm = TableManagerFactory.create_manager(
        table_ext[1:], logger=configurator.logger)

    demultiplexing_table = excel_tm.aggregate_data(
        adapters_filepath=tm_config['adapter-list'],
        indexes_filepath=tm_config['index-list'],
        samples_filepath=tm_config['sample-list'])

    excel_tm.save_dump(
        tm_config['dump-file'], data=demultiplexing_table)

    excel_tm.create_sample_sheet(
        tm_config['sample-sheet'], data=demultiplexing_table)

if __name__ == '__main__':
    main()
