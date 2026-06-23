"""This module provides functionality to load config settings from a file.

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
import configparser
import logging
import os
from typing import AnyStr, Optional, Protocol

from ngs_analyzer.core.base.mixins.logger_mixin import LoggerMixin
from ngs_analyzer.core.configuration.configuration_error import \
    ConfigurationError

# endregion


class IConfigLoader(Protocol):
    """Interface for configuration loader classes.

    Defines a load() method to load configuration data.
    """

    def load(self) -> dict:
        """Load configuration from a file.

            Returns:
                A dictionary containing the loaded configuration.
                Returns an empty dictionary if the file doesn't exist
                or is invalid.

            Raises:
                FileNotFoundError: if loading fails.
        """
        raise NotImplementedError


class ConfigLoader(LoggerMixin, IConfigLoader):
    """Load configuration data from an INI file, with logging support."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)

    def load(
        self,
        base_config_filepath: Optional[os.PathLike[AnyStr]] = os.path.abspath(
            os.path.join('src', 'conf', 'config.ini'),
        ),
        target_section: AnyStr = 'Pathes',
    ) -> dict:
        """Load configuration from the specified INI file and section.

            Args:
                base_config_filepath (os.PathLike):
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
        if (
            os.path.exists(
                base_config_filepath) and os.path.isfile(base_config_filepath)
        ):
            conf = configparser.ConfigParser(
                inline_comment_prefixes=[';', '#'],
                comment_prefixes=[';', '#'])

            conf.read(os.path.join(base_config_filepath))

            config_dict = {'target_section': target_section}

            if target_section in conf:
                for path_value in conf[target_section]:
                    config_dict[path_value] = conf[target_section][path_value]
            else:
                raise ConfigurationError(
                    'Can\'t parse configuration file '
                    f'under path "{base_config_filepath}". '
                    'See the project config documentation',
                )

            return config_dict

        else:

            file_not_found_msg = \
                f'Can\'t find config file under path "{base_config_filepath}"'

            self.logger.critical(file_not_found_msg)
            raise FileNotFoundError(file_not_found_msg)
