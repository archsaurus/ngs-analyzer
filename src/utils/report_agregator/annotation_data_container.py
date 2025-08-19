"""
    Module containing the AnnotationDataContainer class. This class
    encapsulates data for a single annotation entry from an annotation section
    (ANN), crucial for analyzing variant impact and location. It inherits
    from IReportDataContainer.
"""

from dataclasses import dataclass

from src.utils.report_agregator.i_report_data_container import IReportDataContainer

@dataclass
class AnnotationDataContainer(IReportDataContainer):
    """
        annotation section (ANN) has a bit of annotations
        divided by 15 fields such as attributes listed bellow

        Attributes:
            Allele
            Annotation
            Annotation_Impact
            Gene_Name
            Gene_ID
            Feature_Type
            Feature_ID
            Transcript_BioType
            Rank
            HGVS.c
            HGVS.p
            cDNA.pos / cDNA.length
            CDS.pos / CDS.length
            AA.pos / AA.length
            Distance
            ERRORS / WARNINGS / INFO'
    """
    allele: str
    annotation: str
    annotation_impact: str
    gene_name: str
    gene_id: str
    mutation_type: str
    mutation_id: str
    transcript_biotype: str
    exon: str
    hgvs_cds: str
    hgvs_protein: str
    c_dna: str
    cds: str
    aminoacid: str
    distance: str
    info: str

# Predicted loss of function (LOF) effects for this variant section has fields
#    Gene_Name
#    Gene_ID
#    Number_of_transcripts_in_gene
#    Percent_of_transcripts_affected
# Predicted nonsense mediated decay (NMD) effects for this variant has fields
#    Gene_Name
#    Gene_ID
#    Number_of_transcripts_in_gene
#    Percent_of_transcripts_affected
