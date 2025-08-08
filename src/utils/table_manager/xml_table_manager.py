from src.core.base import *
from . import *

class XmlTableManager(LoggerMixin, ITableManager):
    def __init__(self, logger: logging.Logger=None):
        super().__init__(logger=logger)

    def aggregate_data() -> pandas.DataFrame: pass

    def save_dump(
        self,
        path: PathLike[AnyStr],
        data: pandas.DataFrame
    ) -> bool: pass
