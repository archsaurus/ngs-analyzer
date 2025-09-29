
from dataclasses import dataclass

from src.utils.report_agregator.i_report_data_container import IReportDataContainer

@dataclass
class VariantCoverageDTO(IReportDataContainer):
    """
        Represents the coverage information for a variant.

        Attributes:
            chromosome (str):
                The chromosome the variant is located on.
            start (str):
                The starting position of the variant on the chromosome.
            reference (str):
                The reference allele.
            alternate (str):
                The alternate allele.
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
            "Alternate coverage": self.alt_coverage}
