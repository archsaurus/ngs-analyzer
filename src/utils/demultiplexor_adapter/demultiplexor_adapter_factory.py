"""
    This module provides a factory for creating different types of \
        demultiplexor adapters.
    It handles the creation and selection logic, \
        abstracting away the specific implementation details.
"""
from typing import Union, TypeVar, Generic
import logging
import os

from src.utils.demultiplexor_adapter.i_demultiplexor_adapter import IDemultiplexorAdapter
from src.utils.demultiplexor_adapter.bcl2fastq_adapter import BclToFastqAdapter
from src.core.base import CommandExecutor
from src.core.base import LoggerMixin

T = TypeVar("T", bound=IDemultiplexorAdapter)

class DemultiplexorAdapterFactory(LoggerMixin, Generic[T]):
    """
        Factory class for creating demultiplexor adapters.
        This class manages the creation process, \
            enabling different demultiplexing implementations.
    """
    def __init__(
        self,
        adapter_types: list[type[T]],
        logger: logging.Logger=None
    ):
        """
            Initializes the factory with a list of supported adapter types.

            Args:
                adapter_types: \
                    A list of adapter classes that the factory can create.
        """
        super().__init__(logger=logger)

        self.adapter_types = adapter_types or [BclToFastqAdapter,]

    @staticmethod
    def create_adapter(
        adapter_type_name: str,
        config: dict[str, str],
        logger: logging.Logger=None,
        caller: Union[CommandExecutor, callable]=os.system
    ) -> IDemultiplexorAdapter:
        """
            Creates a demultiplexor adapter based on the provided type name.

            Args:
                adapter_type_name (str): \
                    The name of the adapter type to create.
                config (dict[str, str]): \
                    A dict of implementation-based agruments.
                logger (logging.Logger): \
                    A logger instance to handle adapter output.
                caller (Union[CommandExecutor, callable]): \
                    Callable entity to execute system commands.

            Returns:
                A demultiplexor adapter object of the specified type.

            Raises:
                ValueError: \
                    If no adapter of the requested type is found.
        """
        factory = DemultiplexorAdapterFactory([BclToFastqAdapter,])
        return factory.get_adapter(
            adapter_type_name, config, logger, caller)

    def get_adapter(
        self,
        adapter_type_name: str,
        config: dict[str, str],
        logger: logging.Logger=None,
        caller: Union[CommandExecutor, callable]=os.system
    ) -> IDemultiplexorAdapter:
        """
            Retrieve an instance of a demultiplexor adapter \
                matching the specified type name.

            Searches through the available adapter types managed \
                by this factory and attempts to instantiate one that \
                    matches the provided `adapter_type_name`.
            If successful, returns the adapter instance; \
                otherwise, logs an error and returns None.

            Args:
                adapter_type_name (str): \
                    The name of the adapter type to instantiate.
                config (dict[str, str]): \
                    Configuration parameters for the adapter.
                logger (logging.Logger, optional): \
                    Logger for logging messages. \
                    Defaults to None.
                caller (Union[CommandExecutor, callable], optional): \
                    Callable used by the adapter for execution purposes. \
                    Defaults to `os.system`.

            Returns:
                IDemultiplexorAdapter: \
                    An instance of the adapter if found and created successfully.
                None: \
                    If no matching adapter type is found or creation fails.

            Raises:
                None explicitly; \
                    errors during adapter instantiation are caught and logged.
        """
        for adapter_type in self.adapter_types:
            if adapter_type.__name__ == adapter_type_name:
                try:
                    adapter = adapter_type(config, caller, logger)
                    return adapter
                except (TypeError, ValueError)  as e:
                    self.logger.error(
                        "Failed to create adapter of type %s: %s",
                        adapter_type.__name__, e)

        self.logger.critical(
            "No suitable demultiplexor adapter found.")
        return None
