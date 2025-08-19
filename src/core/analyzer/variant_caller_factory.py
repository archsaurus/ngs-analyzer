"""
    This module defines a factory class for creating variant caller instances.
    It provides a way to select a specific variant calling tool (e.g., Pisces,
    GATK UnifiedGenotyper, FreeBayes) based on configuration settings.
    The factory ensures that the correct variant caller is instantiated
    and initialized with the appropriate configuration parameters.
"""

# region Imports
import logging

from typing import Optional

from src.core.base import LoggerMixin

from src.configurator import Configurator

from src.core.analyzer.i_variant_caller import IVariantCaller

from src.core.analyzer.variant_caller import PiscesVariantCaller
from src.core.analyzer.variant_caller import UnifiedGenotyperVariantCaller
from src.core.analyzer.variant_caller import FreebayesVariantCaller
# endregion

class VariantCallerFactory(LoggerMixin):
    """
        Factory class for creating variant caller instances
        based on configuration.

        Supports multiple variant calling tools such as
            Pisces,
            GATK UnifiedGenotyper,
            and FreeBayes.

        The factory uses the provided configuration to determine
        which variant caller to instantiate.

        This promotes code modularity and allows
        for easy addition or removal of variant calling tools without
        affecting other parts of the application.
    """
    def __init__(self, logger: Optional[logging.Logger]=None):
        """
            Initializes the factory with an optional logger.

            Args:
                logger (Optional[logging.Logger]):
                    Logger instance for logging messages.
        """
        super().__init__(logger=logger)

    @staticmethod
    def create_caller(
        caller_config: dict[str, str],
        configurator: Configurator
     ) -> IVariantCaller:
        """
            Creates an instance of a variant caller
                based on the provided configuration.

            Args:
                caller_config (Dict[str, str]):
                    Dictionary containing at least the 'name' key
                    specifying the caller type.
                configurator (Configurator):
                    Configuration object containing parameters and logger.

            Returns:
                IVariantCaller:
                    An instance of the selected variant caller class.

            Raises:
                ConfigurationError:
                    If the caller type is not recognized.
        """
        match caller_config['name']:
            case 'pisces':
                return PiscesVariantCaller(
                    configurator=configurator,
                    logger=configurator.logger)

            case 'unifiedgenotyper':
                return UnifiedGenotyperVariantCaller(
                    configurator=configurator,
                    logger=configurator.logger)

            case 'freebayes':
                return FreebayesVariantCaller(
                    configurator=configurator,
                    logger=configurator.logger)

            case _:
                logger = logging.getLogger(__name__)
                logger.critical(
                    "Unknown caller type '%s'", caller_config['name'])
                raise SyntaxError(
                    "There is an error in your configuration file"
                    "Check the project documentation")
