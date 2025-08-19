"""
    Module containing protocols for variant calling and data preparation.

    This module defines protocols for `IDataPreparator` and `IVariantCaller`
    classes, enforcing a specific method signature for type hinting.
    This improves code maintainability and readability by ensuring
    all implementing classes adhere to a consistent interface.
"""

# region Imports
from typing import Protocol
from typing import Union, Any

from src.core.base import CommandExecutor
from src.core.sample_data_container import SampleDataContainer
# endregion

class IVariantCaller(Protocol):
    """
        Protocol interface for variant caller classes.
        Defines the 'call_variant' method that all implementing classes
        must override, responsible for performing variant calling
        on a given sample.
    """
    def call_variant(
        self,
        sample: SampleDataContainer,
        executor: Union[CommandExecutor, callable],
    ) -> Any:
        """
            Executes variant calling on the provided sample.

            Args:
                sample (SampleDataContainer):
                    The sample data container containing input data.
                executor (Union[CommandExecutor, callable]):
                    Function or object to execute system commands.

            Returns:
                None:
                    This method performs its task without returning a value.
        """
        raise NotImplementedError
