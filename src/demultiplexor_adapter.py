"""
    Module for demultiplexor adapter functionality.
"""

# region Imports
import os

from src.configurator import Configurator
from src.utils.demultiplexor_adapter.demultiplexor_adapter_factory import (
    DemultiplexorAdapterFactory)
# endregion

def main():
    """
        Main function responsible for creating and executing \
        the demultiplexor adapter as an autonomous component \
            outside the pipeline.
    """
    demultiplexor_adapter = DemultiplexorAdapterFactory.create_adapter(
        adapter_type_name="BclToFastqAdapter",
        config=Configurator().parse_configuration(
            target_section='DemultiplexorAdapter'),
        logger=Configurator().logger,
        caller=os.system)

    demultiplexor_adapter.demultiplex()

if __name__ == '__main__':
    main()
