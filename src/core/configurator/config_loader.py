"""
    This module provides functionality to load
    configuration settings from a file.

    It defines:
        - `IConfigLoader`:
            An interface (via Protocol) that specifies a `load()`
            method for loading configuration data.
        - `ConfigLoader`:
            Implements `IConfigLoader` and `LoggerMixin` to load
            configuration from an INI file.

    Main features:
        - Loads configuration from a specified file path,
        defaulting to 'src/conf/config.ini'.
        - Reads a specific section (default 'Pathes')
        from the configuration file.
        - Returns a dictionary containing configuration key-value pairs.
        - Raises `FileNotFoundError` if the configuration file does not exist.
        - Raises `ConfigurationError` if the section is missing or invalid.

    Usage:
        Instantiate `ConfigLoader`, optionally passing a logger,
        and call `load()` with the desired file path and section.
"""

# region Imports
import os
import logging
import configparser

from os import PathLike
from typing import Protocol, Optional, AnyStr

from src.core.base import LoggerMixin
from src.core.configurator.configuration_error import ConfigurationError
# endregion

class IConfigLoader(Protocol):
    """
        Interface for configuration loader classes.
        Defines a load() method to load configuration data.
    """
    def load(self) -> dict:
        """
            Loads configuration from a file.

            Args:
                base_config_filepath:
                    Path to the configuration file.
                    Defaults to 'src/conf/config.ini'.
                target_section:
                    Section in the config file to load.
                    Defaults to 'Pathes'.

            Returns:
                A dictionary containing the loaded configuration.
                Returns an empty dictionary if the file doesn't exist
                or is invalid.

            Raises:
                FileNotFoundError: if loading fails.
        """

class ConfigLoader(LoggerMixin, IConfigLoader):
    """Loads configuration data from an INI file, with logging support."""
    def __init__(self, logger: Optional[logging.Logger]=None):
        super().__init__(logger)

    def load(
        self,
        base_config_filepath: PathLike[AnyStr]=os.path.join(
            os.path.curdir, 'src', 'conf', 'config.ini'),
        target_section: AnyStr='Pathes'
    ) -> dict:
        """
            Loads configuration from the specified INI file and section.

            Args:
                base_config_filepath (PathLike):
                    Path to the configuration file.
                target_section (str):
                    Section in the configuration file to load.

            Returns:
                dict:
                    Dictionary with configuration entries from the section.

            Raises:
                FileNotFoundError:
                    if the configuration file does not exist.
                ConfigurationError:
                    if the section is missing or cannot be parsed.
        """
        if os.path.exists(base_config_filepath) and os.path.isfile(base_config_filepath):
            conf = configparser.ConfigParser(
                inline_comment_prefixes=[';', '#'], comment_prefixes=[';', '#'])
            conf.read(os.path.join(base_config_filepath))

            config_dict = {'target_section': target_section}
            if target_section in conf:
                for path_value in conf[target_section]:
                    config_dict[path_value] = conf[target_section][path_value]
            else:
                raise ConfigurationError(
                    f"Can't parse configuration file under path '{base_config_filepath}'. "
                    "See the project config documentation")

            return config_dict
        self.logger.critical(
            "Can't find configuration file under path '%s'",
            base_config_filepath)

        raise FileNotFoundError()
