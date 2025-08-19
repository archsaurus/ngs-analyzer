"""
    Module containing the IDataPreparator protocol.

    This module defines a protocol for data preparator classes
.
    This allows type hinting to ensure that classes using an
    IDataPreparator will have a perform method with a specific
    signature.
"""

from typing import Protocol, Any

class IDataPreparator(Protocol):
    """
        Protocol interface for data preparator classes.

        Defines a method 'perform' that all implementing classes
        must override.  This allows type hinting to ensure that
        classes using an IDataPreparator will have a perform method
        with a specific signature.
    """
    def perform(self) -> Any:
        """
            Performs the data preparation steps.

            Raises:
                NotImplementedError:
                    If the method is not implemented in a concrete class.
        """
        raise NotImplementedError
