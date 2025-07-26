from src.core.base import *
from . import *

class TableManagerFactory:
    @staticmethod
    def create_manager(format_type: str, logger=None) -> ITableManager:
        match format_type:
            case 'xml': return XmlTableManager(logger=logger)
            case 'xls' | 'xlsx': return ExcelTableManager(logger=logger)
            case 'csv' | 'tsv': return CsvTableManager(logger=logger)
            case _: raise ValueError(f"Unknown format type: {format_type}")
