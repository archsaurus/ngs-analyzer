from src.core.base import *
from src.core.configuration_error import ConfigurationError

from .i_demultiplexor_adapter import IDemultiplexorAdapter

class BclToFastqAdapter(LoggerMixin, IDemultiplexorAdapter):
    """
        Adapter class to convert BCL files to FASTQ format by Illumina bcl2fastq tool.

        This class manages the construction and execution of a demultiplexing command
        based on provided configuration parameters. It validates the configuration,
        constructs command-line arguments accordingly, and executes the demultiplexing
        process via a specified command caller.

        Attributes:
            config (dict[str, str]): Configuration parameters used for demultiplexing.
            cmd_caller (callable): Function used to execute system commands.
            logger (logging.Logger): Logger instance for logging messages (inherited from LoggerMixin).
    """
    def __init__(self, config: dict[str, str], cmd_caller: Optional[callable]=os.system, logger: logging.Logger=None):
        super().__init__()

        if not callable(cmd_caller): raise TypeError(f"'cmd_caller' should be callable, got {type(cmd_caller)}")
        else: self.cmd_caller = cmd_caller

        is_config_valid, msg = self._check_config(config)
        if not is_config_valid:
            self.logger.critical(msg)
            raise ConfigurationError(msg)
        else: self.config = config

    def _check_config(self, config: dict[str, str],) -> (bool, str):
        """
            Validates the provided configuration dictionary.

            Args:
                config (dict[str, str]): The configuration dictionary to validate.
            Returns: tuple[bool, str] contains
                flag (bool): True if the configuration is valid, False otherwise.
                message (str): A message indicating the validation result or describing missing keys.
        """
        if not isinstance(config, dict): return (False, f"Expected 'config' to be a dict, got {type(config)}")
        
        required_keys = ['demultiplexor', 'input-dir', 'output-dir', 'sample-sheet', 'runfolder-dir']
        missing_keys = [k for k in required_keys if k not in config]
        if missing_keys: return (False, f"Missing required configuration keys: {missing_keys}")

        return (True, "OK")

    def _add_param(self, arguments: list, arg_name: str, config_key=None, value=None, is_flag=False):
        """
            Adds a command-line argument to the list based on configuration and parameters.
            
            Args:
                arguments (list): The list of command-line arguments to which new arguments will be appended.
                arg_name (str): The argument name, e.g., '--min-log-level'.
                config_key (str, optional): The key to look up in the configuration dictionary. \
                    Defaults to None, in which case the argument name without '--' is used.
                value (any, optional): The value to be added as an argument if present. Defaults to None.
                is_flag (bool, optional): If True, adds only the flag (without a value) if \
                    the corresponding config is True. Defaults to False.
            Note:
                If 'is_flag' is True and the configuration value for the key is True, \
                    appends 'arg_name' to the arguments list.
                Otherwise, if a value exists in the configuration for the key, \
                    appends both 'arg_name' and the string representation of the value to the list.
        """
        key = config_key or arg_name.lstrip('-')
        if is_flag:
            if self.config[key] == "True" : arguments.append(arg_name)
        else:
            val = self.config.get(key)
            if val is not None: arguments.extend([arg_name, str(val)])

    def demultiplex(self) -> None:
        """
            Constructs and executes the demultiplexing command based on the current configuration.

            Note:
                Relies on the '_add_param' method to append arguments based on configuration values.
                Assumes 'self.config' contains all necessary configuration entries.
                Uses 'self.cmd_caller' to execute the command with the constructed arguments.
        """

        cmd_args = [self.config['demultiplexor']]

        required = [
            'runfolder-dir',
            'input-dir',
            'output-dir',
            'sample-sheet',
            'tiles',
            'use-bases-mask'
        ]

        [self._add_param(cmd_args, arg_name=f"--{arg}", config_key=arg) for arg in required]

        defaults = {
            'min-log-level': 'INFO',
            'loading-threads': 4,
            'processing-threads': 4,
            'writing-threads': 4,
            'minimum-trimmed-read-length': 35,
            'mask-short-adapter-reads': 22,
            'adapter-stringency': 0.9,
            'fastq-compression-level': 4,
            'barcode-mismatches': 1
        }

        for key, default in defaults.items(): 
            if key in self.config: self._add_param(cmd_args, arg_name=f"--{key}", config_key=key)
            else: self._add_param(cmd_args, arg_name=f"--{key}", value=default)

        for flag in [
            'ignore-missing-bcls',
            'ignore-missing-filter',
            'ignore-missing-positions',
            'ignore-missing-controls',
            'write-fastq-reverse-complement',
            'with-failed-reads',
            'create-fastq-for-index-reads',
            'find-adapters-with-sliding-window',
            'no-bgzf-compression',
            'no-lane-splitting'
        ]: self._add_param(cmd_args, arg_name=f"--{flag}", config_key=flag, is_flag=True)

        for other_optional in [
            'intensities-dir',
            'stats-dir',
            'interop-dir',
            'reports-dir'
        ]: self._add_param(cmd_args, arg_name=f"--{other_optional}", config_key=other_optional)

        [print(arg) for arg in cmd_args]
        self.cmd_caller(' '.join(cmd_args))
