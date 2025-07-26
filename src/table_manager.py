from src.core.base import *
from src.configurator import Configurator
from src.utils.table_manager import *

# TODO: Code CSV- and XML- TableManager

def main():
    configurator = Configurator()
    tm_config = configurator.parse_configuration(target_section='TableManager')
    
    _, table_ext = os.path.splitext(tm_config['adapter-list'])

    excel_tm = TableManagerFactory.create_manager(table_ext[1:], logger=configurator.logger)
    
    demultiplexing_table = excel_tm.aggregate_data(
        adapters_filepath=tm_config['adapter-list'],
        indexes_filepath=tm_config['index-list'],
        samples_filepath=tm_config['sample-list']
    )
    
    if excel_tm.save_data(path=tm_config['sample_sheet'], data=demultiplexing_table):
        excel_tm.create_sample_sheet(
            path=os.path.abspath(os.path.join(tm_config['base_outpath'], 'sample_sheet.csv')),
            data=demultiplexing_table
        )
    else: exit(os.EX_SOFTWARE)

if __name__ == '__main__': main()
