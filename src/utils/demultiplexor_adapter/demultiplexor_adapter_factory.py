from src.core.base import *

from .i_demultiplexor_adapter import IDemultiplexorAdapter
from .bcl2fastq_adapter import BclToFastqAdapter

class DemultiplexorAdapterFactory:
    @staticmethod
    def create_adapter(config: dict[str, str], logger: logging.Logger=None, caller: callable=os.system) -> IDemultiplexorAdapter:
        return BclToFastqAdapter(config=config, logger=logger, cmd_caller=caller)
