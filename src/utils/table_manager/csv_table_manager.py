from src.core.base import *
from . import *

class CsvTableManager(LoggerMixin, ITableManager):
    def __init__(self, delimeter: str=',', logger: logging.Logger=None):
        super().__init__()
        self.set_logger(logger)
        self.delimeter = delimeter

    def set_delimeter(self, delimeter: str) -> None:
        if len(delimeter) == 1:
            if self.delimeter != delimeter: self.delimeter = delimeter
        else: raise Exception(f"Passed non one-character delimeter '{delimeter}'")

    def aggregate_data() -> pandas.DataFrame: pass

    def save_data(self, path: PathLike[AnyStr], data: pandas.DataFrame) -> bool: pass
