"""This module defines the GeneDetailsDTO class,
which encapsulates detailed information about a gene,
including its name, transcript, exon, and HGVS annotations.

The GeneDetailsDTO class inherits from IReportDataContainer
and is implemented as a dataclass. It contains attributes
such as gene name, gene detail, exon, HGVS coding DNA and protein annotations,
and a list of associated annotation data containers.

The class provides a method to convert its data into a dictionary,
dynamically including a subset of annotations based on the number of
annotations available (with a modulo operation). This is useful
for generating summarized or formatted reports.

Note:
    The annotations attribute is a list of AnnotationDataContainer instances,
    allowing for flexible annotation management.
"""

from dataclasses import dataclass

from src.utils.report_aggregator.i_report_data_container import \
    IReportDataContainer
from src.utils.report_aggregator.annotation_data_container import \
    AnnotationDataContainer


@dataclass
class GeneDetailsDTO(IReportDataContainer):
    """Represents detailed information about a gene, including its
        name, transcript, exon, and HGVS annotations.

    Attributes:
        gene_name (str):
            The official name of the gene.
        gene_detail (str):
            Additional details about the gene, such as transcript ID.
        exon (str):
            The exon number or identifier within the gene.
        hgvs_cds (str):
            HGVS nomenclature for the coding DNA sequence (c. notation).
        hgvs_protein (str):
            HGVS nomenclature for the protein change (p. notation).
    """

    annotations: list[AnnotationDataContainer]

    def to_dict(self):
        annotations_count = len(self.annotations) % 5
        annotation_context = {}

        for i in range(annotations_count):
            annotation = self.annotations[i]

            for name, value in annotation.to_dict().items():
                if value is not None:
                    key = f"{i+1} {name.replace('_', ' ')}"
                    annotation_context[key] = value

        return annotation_context
