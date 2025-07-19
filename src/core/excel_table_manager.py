from src.core.base import *

import pandas

class ExcelTableManager(metaclass=SingletonMeta):
    def __init__(self, logger: logging.Logger=None):
        if logger is None:
            self.logger = logging.Logger(__name__)
            self.logger.setLevel(logging.INFO)
            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setFormatter(logging.Formatter(r'%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(stdout_handler)
        else: self.logger = logger

    # TODO: Must to refactor hardcode by adding mapping file
    def aggregate_data(
        self,
        adapters_filepath: PathLike[AnyStr], 
        indexes_filepath: PathLike[AnyStr], 
        samples_filepath: PathLike[AnyStr]
    ) -> pandas.DataFrame:
        """
            Merges data from three Excel files into a single DataFrame.

            Args:
                adapters_filepath: Path to the adapters Excel file.
                indexes_filepath: Path to the indexes Excel file.
                samples_filepath: Path to the samples Excel file.

            Returns:
                pandas.DataFrame: The merged DataFrame, or None if errors occur. \
                Prints informative error messages if a logger is not provided.
        """
        try:
            adapters_book = pandas.read_excel(adapters_filepath)
            indexes_book = pandas.read_excel(indexes_filepath)
            samples_book = pandas.read_excel(samples_filepath)
        except Exception as e:
            self.logger.critical(f"A fatal error '{e.__repr__()}' occured at '{e.__traceback__.tb_frame}'")
            return None

        table = pandas.DataFrame({
                'sample_id': [],
                'lib_type':  [], 'index_type':[],
                'i7_mark':   [], 'i5_mark':   [],
                'p7':        [], 'p5':        [],
                'i7':        [], 'i7_compl':  [],
                'i5':        [], 'i5_compl':  []
            }, dtype=str
        )

        table['i7_mark'] = table['i7_mark'].astype(int)
        table['i5_mark'] = table['i5_mark'].astype(int)

        for sample_row in samples_book.itertuples(): # Init table with reference Sample List
            index_type, lib_type, sample_id = sample_row[4:7]
            i7_mark, i5_mark = sample_row[14:16]
            table = pandas.concat([
                table, pandas.DataFrame({
                    'sample_id': [str(sample_id).strip().replace(' ', '')],
                    'lib_type': [lib_type],
                    'index_type': [index_type],
                    'i7_mark': [i7_mark],
                    'i5_mark': [i5_mark]
            })], ignore_index=True)

        for index_row in indexes_book.itertuples(): # Add i7, i7_compl, i5 and i5_compl to table
            index_type = 'BridgeV1' if 'Bridge' in str(index_row[1]) else index_row[1]
            
            sid, index_norm, index_compl = index_row[2:5]

            sid_str = str(sid)[-3:]

            mask7 = (table['index_type'].astype(str) == index_type) & (table['i7_mark'].astype(str) == sid_str)
            mask5 = (table['index_type'].astype(str) == index_type) & (table['i5_mark'].astype(str) == sid_str)
            table.loc[mask7, 'i7'] = index_norm; table.loc[mask7, 'i7_compl'] = index_compl
            table.loc[mask5, 'i5'] = index_norm; table.loc[mask5, 'i5_compl'] = index_compl

        for adapter_row in adapters_book.itertuples():
            if pandas.notna(adapter_row[2]):
                sid, adapter_seq = adapter_row[1:3]
                
                idx_marks = re.findall(r"[0-9]{3}", sid)
                idx_type = re.findall(r"([a-zA-Z]{2,})|(D[0-9]{3})", sid)
                
                # region Name mapping
                if not idx_type: idx_type = 'Unknown'
                else:
                    try:
                        for t in idx_type[0]:
                            if len(t) > 0 :
                                t = str(t).upper()
                                if 'BRIDGE' in t: idx_type = 'BridgeV1'
                                elif 'TSIT' in t:
                                    if len(idx_type) > 1:
                                        if 'SHORT' in str(''.join(idx_type[1][0])).upper(): idx_type = 'TSIT_short'
                                        else: idx_type = 'TSIT'
                                    else: idx_type = 'TSIT'
                                elif 'D5' in t or 'D7' in t: idx_type = 'TruSeq'
                                else: idx_type = 'Unknown'
                    except Exception as e:
                        print(f"Raise '{e}' with data '{e.__traceback__.tb_frame.f_trace}'")
                # endregion
                if idx_marks:
                    mask_idx_type = (table['index_type'].astype(str) == str(idx_type))

                    mask7 = (table['i7_mark'].astype(str) == str(idx_marks[0])) & mask_idx_type
                    mask5 = (table['i5_mark'].astype(str) == str(idx_marks[0])) & mask_idx_type

                    table.loc[mask7, 'p7'] = str(adapter_seq).upper()
                    table.loc[mask5, 'p5'] = str(adapter_seq).upper()
        return table

    # TODO: Write FormatHandler for more flexible API
    def save_data(self, path: PathLike[AnyStr], data: pandas.DataFrame) -> bool:
        """
            Saves data from a Pandas DataFrame to a CSV file.

            Args:
                path: The path to the output CSV file.
                data: The Pandas DataFrame containing the data to save.

            Returns:
                True if the data was successfully saved, False otherwise.  Raises an exception if the file cannot be created or written to.

            Raises:
                TypeError: If input data is not a Pandas DataFrame.
        """
        if not isinstance(data, pandas.DataFrame): raise TypeError("Input data must be a Pandas DataFrame.")
        try:
            with open(path, 'x') as dump_fd:
                header = "sample_id;lib_type;index_type;i7_mark;i5_mark;p7;p5;i7;i7_compl;i5;i5_compl;"
                print(header, file=dump_fd)
                for i in data.itertuples(): print(';'.join((map(str,i[1:]))), file=dump_fd)
            return True
        except FileExistsError as e:
            self.logger.warning(f"File {path} already exists.")
            while True:
                response = input(f"Do you want to rewrite {path} [y/n]? ").lower()
                if response in ('y', 'n'): break
                
                print("Invalid input. Please enter 'y' or 'n'.")
            if response == 'y':
                with open(path, 'w') as dump_fd:
                    header = "sample_id;lib_type;index_type;i7_mark;i5_mark;p7;p5;i7;i7_compl;i5;i5_compl;"
                    print(header, file=dump_fd)
                    for i in data.itertuples(): print(';'.join((map(str,i[1:]))), file=dump_fd)
                return True
            else: return False

def main():
    from src.settings import dependency_handler, configurator

    tm = ExcelTableManager()
    tm_config = configurator.parse_configuration(target_section='ExcelTableManager')

    demultiplexing_table = tm.aggregate_data(
        adapters_filepath=tm_config['adapter-list'],
        indexes_filepath=tm_config['index-list'],
        samples_filepath=tm_config['sample-list']
    )

    if tm.save_data(path=tm_config['dump'], data=demultiplexing_table):
        barcodes_path = os.path.join(tm_config['base_outpath'], 'barcodes.tsv') 

        try:
            with open(barcodes_path, 'w') as barcodes_fd:
                [print(f"{row[1]}", f"{row[8]}", f"{row[10]}", sep='\t', file=barcodes_fd) for row in demultiplexing_table.itertuples()]

        except:
            pass

        output_dir_path = os.path.join(tm_config['base_outpath'], 'demultiplexed3')
        os.makedirs(output_dir_path, exist_ok=True)

        cmd = ' '.join([
            tm_config['demultiplexor'], 'match',
            '-p', output_dir_path,
            '-m', '3',
            '-d',
            barcodes_path,
            tm_config['r1_undetermined_path'],
            tm_config['r2_undetermined_path'],
        ])

        os.system(cmd)

    else: exit(os.EX_SOFTWARE)

if __name__ == '__main__':
    main()
