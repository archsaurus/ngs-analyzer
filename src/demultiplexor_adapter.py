from src.core.base import *
from src.configurator import Configurator
from src.utils.demultiplexor_adapter.demultiplexor_adapter_factory import DemultiplexorAdapterFactory

def main():
    demultiplexor_adapter = DemultiplexorAdapterFactory.create_adapter(
        config=Configurator().parse_configuration(
            target_section='DemultiplexorAdapter'),
        logger=Configurator().logger,
        caller=os.system
    )

    demultiplexor_adapter.demultiplex()

if __name__ == '__main__': main()
