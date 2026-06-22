import logging
import os
from typing import Optional, Protocol, Union

from ngs_analyzer.core.base.mixins.logger_mixin import LoggerMixin


class ICommandExecutor(Protocol):
    """Protocol for command executor classes.

    Defines the interface for executing system commands.
    """

    def run(
        self,
        command: Union[list[str], str, dict[str, str]]
    ) -> bool:
        """Executes a command.

        Args:
            command (Union[list[str], str, dict[str, str]]):
                Command to execute.
        """


class CommandExecutor(LoggerMixin, ICommandExecutor):
    """Executes system commands using a provided callable.

        Attributes:
            caller (callable):
                Function that executes commands, defaults to os.system.
            logger (logging.Logger):
                Logger instance for logging.
    """

    def __init__(
        self,
        caller: callable = os.system,
        logger: Optional[logging.Logger] = None
    ):
        """Initializes the CommandExecutor.

            Args:
                caller (callable):
                    Callable that executes commands.
                logger (Optional[logging.Logger]):
                    Logger instance.
        """
        super().__init__(logger)

        if callable(caller):
            self.caller = caller
        else:
            raise TypeError(
                "Command caller must be callable, "
                f"'{type(caller)}' given")

    def run(
        self,
        command: Union[list[str], str, dict[str, str]]
    ) -> bool:
        """Executes the given command.

            Args:
                command (Union[list[str], str, dict[str, str]]):
                    Command to run.

            Returns:
                bool:
                    True if command executed successfully, False otherwise.
        """
        if isinstance(command, list):
            self.caller(' '.join(command))
        elif isinstance(command, str):
            self.caller(command)
        elif isinstance(command, dict):
            self.caller(' '.join(
                [f"{key} {value}" for (key, value) in command.items()])
            )

        else:
            raise TypeError(f"Unsupported command type: {type(command)}")

        self.logger.debug(
            "'%s' got '%s' command as type '%s'",
            self.__class__.__name__,
            str(command), type(command))

        try:
            self.caller(command)
            return True

        except (OSError, SystemError, PermissionError, IOError) as e:
            self.logger.critical(e)
            return False
