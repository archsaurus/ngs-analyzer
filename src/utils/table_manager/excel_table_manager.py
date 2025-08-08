from src.core.base import *
from src.utils.table_manager import *

from src.utils.table_manager.sample_sheet_container import (
    SampleSheetContainer,
    Section)

from src.utils.table_manager.sample_sheet_builder import SampleSheetBuilder

import datetime

class ExcelTableManager(LoggerMixin, ITableManager):
    def __init__(self, logger: logging.Logger=None):
        super().__init__()
        self.set_logger(logger)

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
                pandas.DataFrame: \
                    The merged DataFrame, or None if errors occur. \
                Prints informative error messages if a logger is not provided.
        """

        # TODO: Must to refactor hardcode by adding mapping file
        try:
            adapters_book = pandas.read_excel(adapters_filepath)
            indexes_book = pandas.read_excel(indexes_filepath)
            samples_book = pandas.read_excel(samples_filepath)
        except Exception as e:
            self.logger.critical(
                f"A fatal error '{e.__repr__()}' occured at "
                f"'{e.__traceback__.tb_frame}'")

            return None

        table = pandas.DataFrame({
            'sample_id': [],
            'lib_type':  [], 'index_type':[],
            'i7_mark':   [], 'i5_mark':   [],
            'p7':        [], 'p5':        [],
            'i7':        [], 'i7_compl':  [],
            'i5':        [], 'i5_compl':  []
            }, dtype=str)

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

            mask7 = (table['index_type'].astype(str) == index_type) & \
                    (table['i7_mark'].astype(str) == sid_str)
            mask5 = (table['index_type'].astype(str) == index_type) & \
                    (table['i5_mark'].astype(str) == sid_str)

            table.loc[mask7, 'i7'] = index_norm
            table.loc[mask7, 'i7_compl'] = index_compl

            table.loc[mask5, 'i5'] = index_norm
            table.loc[mask5, 'i5_compl'] = index_compl

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
                                        if 'SHORT' in str(''.join(idx_type[1][0])).upper():
                                            idx_type = 'TSIT_short'
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

    def save_dump(
        self,
        path: PathLike[AnyStr],
        data: pandas.DataFrame
    ) -> bool:
        """
            Saves data from a Pandas DataFrame to a CSV file.

            Args:
                path: The path to the output CSV file.
                data: The Pandas DataFrame containing the data to save.

            Returns:
                True if the data was successfully saved, False otherwise. \
                    Raises an exception if the file cannot be created or written to.

            Raises:
                TypeError: If input data is not a Pandas DataFrame.
        """
        if not isinstance(data, pandas.DataFrame):
            raise TypeError("Input data must be a Pandas DataFrame.")

        try:
            with open(path, 'x') as sample_sheet_fd:
                header = "sample_id;lib_type;index_type;i7_mark;i5_mark;p7;p5;i7;i7_compl;i5;i5_compl;"
                print(header, file=sample_sheet_fd)

                for i in data.itertuples():
                    print(';'.join((map(str,i[1:]))), file=sample_sheet_fd)

            return True

        except FileExistsError as e:
            self.logger.warning(f"File {path} already exists.")
            while True:
                response = input(f"Do you want to rewrite {path} [y/n]? ").lower()
                if response in ('y', 'n'): break
                
                print("Invalid input. Please enter 'y' or 'n'.")
            if response == 'y':
                with open(path, 'w') as sample_sheet_fd:
                    header = "sample_id;lib_type;index_type;i7_mark;i5_mark;p7;p5;i7;i7_compl;i5;i5_compl;"
                    print(header, file=sample_sheet_fd)
                    for i in data.itertuples():
                        print(';'.join((map(str,i[1:]))), file=sample_sheet_fd)

                return True

            else: return False

    def create_sample_sheet(self, path: PathLike[AnyStr], data: pandas.DataFrame) -> bool:
        sh, sh_builder = None, None
        try:
            sh = SampleSheetContainer()
            sh.add_section(Section("Header", {
                "Local Run Manager Analysis Id": 1,
                "Date": datetime.date.today(),
                "Experiment Name": "NSG216",
                "WorkFlow": "GenerateFastQWorkflow",
                "Description": "",
                "Chemistry": "Amplicon"}))
            sh.add_section(Section("Reads", ["151", "151"]))

            """ data:
                row[0]  - column index,  row[1] - sample identifier
                row[2]  - lib identifier,row[3] - index identifier
                row[4]  - p7 forward,    row[5] - p7 compl
                row[6]  - p5 forward,    row[7] - p5 compl
                row[8]  - i7 forward,    row[9] - i7 compl
                row[10] - i5 forward,    row[11] - i5 compl
            """

            # Writing [Data] Section with format:   Sample_ID   Sample_Name Index   I7_Index_ID index2  I5_Index_ID
            # This header is required for [Data] section.
            # For more details see documentation provided by Illumina
            # (https://support.illumina.com/content/dam/illumina-support/documents/documentation/software_documentation/bcl2fastq/bcl2fastq2-v2-20-software-guide-15051736-03.pdf)
            
            counter = 1

            sh_data_dict = {}
            sh_data_dict['Sample_ID'] = [
                'Sample_Name',
                'Index',
                'I7_Index_ID',
                'index2',
                'I5_Index_ID']

            for row in data.itertuples():
                if counter not in sh_data_dict:
                    sh_data_dict[counter] = [
                        f"{row[1]}",
                        f"{row[9]}",
                        f"{row[4]}",
                        f"{row[11]}",
                        f"{row[5]}"]

                else:
                    raise IndexError(
                        f"Not unique value '{counter}' passed as primary key")

                counter += 1

            sh.add_section(Section("Data", sh_data_dict))

            sh_builder = SampleSheetBuilder(sh, separator=',')
            sh_builder.build()
            sh_builder.save_to_csv(path)

            return True

        except Exception as e:
            raise e
