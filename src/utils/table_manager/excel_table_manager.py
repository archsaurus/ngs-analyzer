"""
    This module defines the ExcelTableManager class,
    which manages table data  imported from Excel files,
    processes and merges the data, and provides methods
    to save the processed data to CSV files or generate
    sample sheets.
    
    It extends the LoggerMixin for logging capabilities
    and implements the ITableManager interface.

    Functions include:
    - aggregate_data:
        Reads multiple Excel files, merges data,
        and returns a DataFrame.
    - save_dump:
        Saves the DataFrame to a CSV file with optional overwrite.
    - create_sample_sheet:
        Generates a sample sheet file based on the data.

    Note: Ensure all dependencies such as pandas,
    and project-specific modules are properly imported and available.
"""

# region Imports
import re
import logging
import datetime

from os import PathLike
from typing import Optional, AnyStr

import pandas
from pandas.errors import ParserError
from pandas.errors import EmptyDataError
from pandas.errors import DataError

from src.core.base import LoggerMixin

from src.utils.table_manager.i_table_manager import ITableManager
from src.utils.table_manager.sample_sheet_container import SampleSheetContainer
from src.utils.table_manager.sample_sheet_container import Section
from src.utils.table_manager.sample_sheet_builder import SampleSheetBuilder
# endregion

class ExcelTableManager(LoggerMixin, ITableManager):
    """
        Manages Excel table data for sample sheets,
        including merging data from multiple Excel files,
        saving data to CSV, and creating sample sheets.
    """
    def __init__(self, logger: logging.Logger=None):
        super().__init__()
        self.set_logger(logger)


    def determine_idx_type(self, idx_type_candidates: list) -> str:
        """Determines the index type based on given candidates."""
        if not idx_type_candidates:
            return 'Unknown'

        for t in idx_type_candidates[0]:
            if not t:
                continue
            t_upper = str(t).upper()

            if 'BRIDGE' in t_upper:
                return 'BridgeV1'
            if 'TSIT' in t_upper:
                if len(idx_type_candidates) > 1:
                    t_part = ''.join(idx_type_candidates[1][0])
                    if 'SHORT' in t_part.upper():
                        return 'TSIT_short'
                return 'TSIT'
            if 'D5' in t_upper or 'D7' in t_upper:
                return 'TruSeq'
        return 'Unknown'

    def aggregate_data(
        self,
        adapters_filepath: PathLike[AnyStr],
        indexes_filepath: PathLike[AnyStr],
        samples_filepath: PathLike[AnyStr]
        ) -> Optional[pandas.DataFrame]:
        """
            Merges data from three Excel files into a single DataFrame.

            Args:
                adapters_filepath (PathLike[AnyStr]):
                    Path to the adapters Excel file.
                indexes_filepath (PathLike[AnyStr]):
                    Path to the indexes Excel file.
                samples_filepath (PathLike[AnyStr]):
                    Path to the samples Excel file.

            Returns:
                pandas.DataFrame:
                    The merged DataFrame, or None if errors occur.
                Prints informative error messages if a logger is not provided.
        """
        try:
            adapters_book = pandas.read_excel(adapters_filepath)
            indexes_book = pandas.read_excel(indexes_filepath)
            samples_book = pandas.read_excel(samples_filepath)

        except (ParserError, EmptyDataError, DataError) as e:
            self.logger.critical(
                "A fatal error '%s' occured at '%s'",
                repr(e), e.__traceback__.tb_frame)

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

        # Init table with reference Sample List
        for sample_row in samples_book.itertuples():
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

         # Add i7, i7_compl, i5 and i5_compl to table
        for index_row in indexes_book.itertuples():
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
                adapter_sid, adapter_seq = adapter_row[1:3]

                idx_marks = re.findall(
                    r"[\d]{3}", adapter_sid)

                # region Name mapping
                try:
                    idx_type_candidates = re.findall(
                        r"([a-zA-Z]{2,})|(D[\d]{3})", adapter_sid)
                    idx_type = self.determine_idx_type(idx_type_candidates)

                except re.PatternError as e:
                    print(f"Raise '{e}' with data "
                    f"'{e.__traceback__.tb_frame.f_trace}'")
                    return None
                # endregion

                if idx_marks:
                    mask_idx_type = (
                        table['index_type'].astype(str) == str(idx_type))

                    mask7 = (
                        table['i7_mark'].astype(str) == str(idx_marks[0])) & \
                            mask_idx_type
                    mask5 = (
                        table['i5_mark'].astype(str) == str(idx_marks[0])) & \
                            mask_idx_type

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
                path:
                    The path to the output CSV file.
                data:
                    The Pandas DataFrame containing the data to save.

            Returns:
                True if the data was successfully saved, False otherwise.
                Raises an exception if the file cannot be created or written to.

            Raises:
                TypeError:
                    If input data is not a Pandas DataFrame.
        """
        if not isinstance(data, pandas.DataFrame):
            raise TypeError("Input data must be a Pandas DataFrame.")

        try:
            with open(path, 'x', encoding='utf-8') as sample_sheet_fd:
                header = "sample_id;lib_type;index_type;"\
                    "i7_mark;i5_mark;p7;p5;i7;i7_compl;i5;i5_compl;"
                print(header, file=sample_sheet_fd)

                for i in data.itertuples():
                    print(';'.join((map(str,i[1:]))), file=sample_sheet_fd)

            return True

        except FileExistsError as _:
            self.logger.warning("File '%s' already exists.", path)
            while True:
                response = input(
                    f"Do you want to rewrite {path} [y/n]? ").lower()
                if response in ('y', 'n'):
                    break

                print("Invalid input. Please enter 'y' or 'n'.")
            if response == 'y':
                with open(path, 'w', encoding='utf-8') as sample_sheet_fd:
                    header = "sample_id;lib_type;index_type;"\
                        "i7_mark;i5_mark;p7;p5;i7;i7_compl;i5;i5_compl;"
                    print(header, file=sample_sheet_fd)
                    for i in data.itertuples():
                        print(';'.join(
                            (map(str,i[1:]))), file=sample_sheet_fd)

                return True
            return False

    def create_sample_sheet(
        self,
        path: PathLike[AnyStr],
        data: pandas.DataFrame) -> bool:
        """
            Creates a sample sheet CSV file based on provided data.

            Args:
                path (PathLike[AnyStr]):
                    Path to save the sample sheet.
                data (pandas.DataFrame):
                    DataFrame with sample data.

            Returns:
                bool:
                    True if the sample sheet was successfully created,
                    raises exceptions otherwise.
        """
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

            # data:
            #    row[0]  - column index,  row[1] - sample identifier
            #    row[2]  - lib identifier,row[3] - index identifier
            #    row[4]  - p7 forward,    row[5] - p7 compl
            #    row[6]  - p5 forward,    row[7] - p5 compl
            #    row[8]  - i7 forward,    row[9] - i7 compl
            #    row[10] - i5 forward,    row[11] - i5 compl

            # Writing [Data] Section with format:
            #       Sample_ID   Sample_Name Index   I7_Index_ID index2  I5_Index_ID
            # This header is required for [Data] section.
            # For more details see documentation provided by Illumina

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
            self.logger.critical(
                "An error '%s' occured at '%s'",
                repr(e), e.__traceback__.tb_frame.f_trace)
            raise e
