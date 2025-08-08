from src.core.base import *
from . import *

class ITableManager(Protocol):
    def aggregate_data(
    ) -> pandas.DataFrame: ...
    
    def save_dump(
        self,
        path: PathLike[AnyStr],
        data: pandas.DataFrame
    ) -> bool: ...
    
    def set_logger(
        self,
        logger: logging.Logger
    ) -> None: ...
