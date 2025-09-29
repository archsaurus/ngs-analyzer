
from dataclasses import dataclass

from src.utils.report_agregator.i_report_data_container import IReportDataContainer

from src.utils.report_agregator.annotation_data_container import AnnotationDataContainer
from src.utils.report_agregator.variant_coverage_dto import VariantCoverageDTO
from src.utils.report_agregator.gene_details_dto import GeneDetailsDTO

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
