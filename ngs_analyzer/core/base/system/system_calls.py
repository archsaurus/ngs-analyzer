import os
from typing import AnyStr


def touch(path: AnyStr) -> None:
    """Creates an empty file or updates the timestamp if it exists.

        Args:
            path (PathLike[AnyStr]):
                Path to the file.
    """
    with open(path, 'a', encoding='utf-8'):
        os.utime(path, None)


def execute(executor, command) -> None:
    """Executes a command using the provided executor.

        Args:
            executor (Union[ICommandExecutor, callable]):
                Executor object or callable.
            command (Union[list[str], str, dict[str, str]]):
                Command to execute.
    """
    if hasattr(executor, 'run'):
        executor.run(command)
    elif callable(executor):
        executor(command)
    else:
        raise TypeError(f"Unsupported executor type: {type(executor)}")
