"""
    This module defines the IDemultiplexorAdapter protocol, \
    which specifies the interface for demultiplexing adapters. \

    It's intended to be used for various demultiplexing methods, \
        ensuring a consistent API.
"""

from os import PathLike
from typing import Protocol, Optional, AnyStr

class IDemultiplexorAdapter(Protocol):
    """
        Protocol for demultiplexing adapters.
        This defines the methods that any demultiplexing adapter \
            must implement.
    """
    def demultiplex(self):
        """
            Performs the demultiplexing operation.
            This should handle all aspects of the demultiplexing process, \
            including configuration, command execution, and error handling.
        """

    def extract_barcodes(
        self,
        r1_path: PathLike[AnyStr],
        r2_path: Optional[PathLike[AnyStr]]=None
    ) -> PathLike[AnyStr]:
        """
            Extract barcode subsequences from input sequence file(s).

            Processes the provided FASTA, FASTQ, or compressed (gzipped) \
            input file(s) to identify and extract barcode sequences \
                or subsequences.

            Supports single-end (R1 only) or paired-end (R1 and R2) data.

            Args:
                r1_path (PathLike[AnyStr]): \
                    Path to the input file containing forward read sequences.
                r2_path (Optional[PathLike[AnyStr]]): \
                    Optional path to the input file containing reversed \
                        read sequences (paired-end data). Defaults to None.

            Returns:
                PathLike[AnyStr]: \
                    Path to the output file containing the extracted \
                        barcode subsequences.

            Raises:
                Various exceptions depending on file processing errors \
                    (not explicitly documented here).
        """
