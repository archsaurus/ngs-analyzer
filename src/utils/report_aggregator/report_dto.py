"""This module defines the ReportDTO class,
which serves as a comprehensive data container for report entries.

The ReportDTO class inherits from IReportDataContainer and is implemented
as a dataclass. It aggregates various pieces of information,
including a unique sample ID, variant coverage details, gene details,
1000 Genomes project data, and ClinVar clinical significance.

The class provides a method to convert the entire report data
into a dictionary format, suitable for reporting, exporting,
or further processing.

Attributes:
    id (str):
        Unique identifier for the sample.
    variant_coverage (VariantCoverageDTO):
        Coverage information for a genetic variant.
    gene_details (GeneDetailsDTO):
        Detailed gene annotation information.
    one_thousand_genomics (str):
        Data from the 1000 Genomes project.
    clinvar_clinical_sign (str):
        Clinical significance annotation from ClinVar.
"""

from dataclasses import dataclass

from src.utils.report_aggregator.i_report_data_container import \
    IReportDataContainer

from src.utils.report_aggregator.variant_coverage_dto import VariantCoverageDTO
from src.utils.report_aggregator.gene_details_dto import GeneDetailsDTO


@dataclass
class ReportDTO(IReportDataContainer):
    """Data container for report entries."""
    id: str
    variant_coverage: VariantCoverageDTO
    gene_details: GeneDetailsDTO
    one_thousand_genomics: str
    clinvar_clinical_sign: str

    def to_dict(self):
        result_dict = {"Sample ID": self.id}
        result_dict.update(self.variant_coverage.to_dict())
        result_dict.update(self.gene_details.to_dict())
        result_dict.update({"1000G": self.one_thousand_genomics})
        result_dict.update({"Clinical sign": self.clinvar_clinical_sign})

        return result_dict
