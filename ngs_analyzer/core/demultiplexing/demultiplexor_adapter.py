"""Module for demultiplexor adapter functionality."""

# region Imports
import os

from ngs_analyzer.core.configuration.configurator import Configurator
from ngs_analyzer.core.demultiplexing.demultiplexor_adapter_factory import \
    DemultiplexorAdapterFactory

# endregion


def main():
    """Create and execute the demultiplexor adapter as an autonomous \
        component outside the pipeline."""
    configurator = Configurator()

    demultiplexor_adapter = DemultiplexorAdapterFactory.create_adapter(
        adapter_type_name='BclToFastqAdapter',
        config=configurator.parse_configuration(
            base_config_filepath=configurator.args.configFilepath,
            target_section='DemultiplexorAdapter',
        ),
        logger=configurator.logger,
        caller=os.system,
    )

    demultiplexor_adapter.demultiplex()


if __name__ == '__main__':
    main()
