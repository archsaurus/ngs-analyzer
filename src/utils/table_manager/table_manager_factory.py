"""
    This module contains the implementation of the TableManagerFactory class,
    which provides a static method for creating instances of table managers
    based on specified format types.
    The factory supports creating managers for XML, Excel, CSV, and TSV formats.

    Classes:
        - TableManagerFactory:
            Factory class with a static method to instantiate appropriate
            table manager objects based on format type.
"""

from src.utils.table_manager.i_table_manager import ITableManager
from src.utils.table_manager.excel_table_manager import ExcelTableManager
from src.utils.table_manager.csv_table_manager import CsvTableManager
from src.utils.table_manager.xml_table_manager import XmlTableManager

class TableManagerFactory:
    """
        Factory class for creating instances of table managers
        based on the specified format type.

        Methods:
            - create_manager:
                Creates and returns an appropriate ITableManager
                implementation based on the provided format type string.

        Usage:
            manager = TableManagerFactory.create_manager(
                'csv', logger=my_logger)
    """
    @staticmethod
    def create_manager(format_type: str, logger=None) -> ITableManager:
        """
            Creates and returns an instance of a table manager
            based on the format type.

            Args:
                format_type (str):
                    The format of the table data. Supported values include:
                        - 'xml'
                        - 'xls' or 'xlsx'
                        - 'csv' or 'tsv'
                logger (logging.Logger, optional):
                    Logger instance for the manager. Defaults to None.

            Returns:
                ITableManager:
                    An instance of the corresponding table manager.

            Raises:
                ValueError:
                    If the provided format_type is not supported.
        """
        match format_type:
            case 'xml': return XmlTableManager(logger=logger)
            case 'xls' | 'xlsx': return ExcelTableManager(logger=logger)
            case 'csv' | 'tsv': return CsvTableManager(logger=logger)
            case _: raise ValueError(f"Unknown format type: {format_type}")
