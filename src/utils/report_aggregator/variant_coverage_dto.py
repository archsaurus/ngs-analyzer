"""This module defines the VariantCoverageDTO class, which represents
    coverage information for a genetic variant.

    The VariantCoverageDTO class inherits from IReportDataContainer
    and is implemented as a dataclass. It encapsulates details
    such as chromosome, start position, reference and alternate alleles,
    as well as their respective counts and coverage metrics.

    This class provides a method to convert its data into a dictionary format
    suitable for reporting or further processing.

    Note:
        The attributes ref_count, alt_count, and alt_coverage
        are represented as strings but should ideally be numeric types
        for calculations and analysis.
"""

from dataclasses import dataclass

from src.utils.report_aggregator.i_report_data_container import \
    IReportDataContainer


@dataclass(slots=True)
class VariantCoverageDTO(IReportDataContainer):
    """Represents the coverage information for a variant.

        Attributes:
            chromosome (str): The chromosome the variant is located on.
            start (str):
                The starting position of the variant on the chromosome.
            reference (str): The reference allele.
            alternate (str): The alternate allele.
            ref_count (str):
                The count of the reference allele.
                Should ideally be a numeric type.
            alt_count (str):
                The count of the alternate allele.
                Should ideally be a numeric type.
            alt_coverage (str):
                The coverage of the alternate allele.
                Should ideally be a numeric type.
    """

    chromosome: str
    start: str
    reference: str
    alternate: str
    ref_count: str
    alt_count: str
    alt_coverage: str

    def to_dict(self):
        return {
            "Chromosome": self.chromosome,
            "Start": self.start,
            "Reference": self.reference,
            "Alternate": self.alternate,
            "Reference count": self.ref_count,
            "Alternate  count": self.alt_count,
            "Alternate coverage": self.alt_coverage
        }
