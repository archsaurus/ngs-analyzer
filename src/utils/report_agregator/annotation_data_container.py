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

            Distance to feature:
                All items in this field are options,
                so the field could be empty.
                * Up/Downstream:
                    Distance to first / last codon
                * Intergenic:
                    Distance to closest gene
                * Distance to closest Intron boundary
                in exon (+/- up/downstream).
                If same, use positive number.
                * Distance to closest exon boundary
                in Intron (+/- up/downstream)
                * Distance to first base in MOTIF
                * Distance to first base in miRNA
                * Distance to exon-intron boundary
                in splice_site or splice _region
                * ChipSeq peak:
                    Distance to summit (or peak center)
                * Histone mark / Histone state:
                    Distance to summit (or peak center)    
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

    def to_dict(self):
        return {
            #"Allele": self.allele,
            "Annotation": self.annotation,
            "Impact": self.annotation_impact,
            #"Gene name": self.gene_name,
            #"Gene ID": self.gene_id,
            "Mutation type": self.mutation_type,
            "Mutation ID": self.mutation_id,
            "Transcript type": self.transcript_biotype,
            #"Exon": self.exon,
            #"HGVS.c": self.hgvs_cds,
            #"HGVS.p": self.hgvs_protein,
            "C_DNA": self.c_dna,
            "CDS": self.cds,
            "Aminoacid": self.aminoacid,
            "Distance": self.distance,
            "Info": self.info}

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
