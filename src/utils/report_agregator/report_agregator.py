from src.core.base import *

from dataclasses import dataclass, fields
from itertools import zip_longest
import csv

from src.configurator import Configurator
from src.core.sample_data_container import SampleDataContainer
from src.core.analyzer.amplicon_coverage_computer import AmpliconCoverageDataPreparator

genotype_format_aliases = {
    'GT': "Genotype",
    'GQ': "Genotype Quality",
    'AD': "Allele Depth",
    'DP': "Total Depth Used For Variant Calling",
    'VF': "Variant Frequency",
    'NL': "Applied BaseCall Noise Level",
    'SB': "StrandBias Score"
}

import abc  
class IReportDataContainer(abc.ABC):
    @classmethod
    def to_dict(cls, self): return {attr: getattr(self, attr) for attr in vars(self)}

    @classmethod
    def from_list(cls, data_list):
        values = []
        for i in range(len(fields(cls))):
            if i < len(data_list): values.append(data_list[i])
            else: values.append('')
        return cls(*values)

    def __str__(self): return ';\n'.join([f"{key}: {value}" for key, value in vars(self).items()])

@dataclass
class VariantDataContainer(IReportDataContainer):
    chromosome: str
    start: str
    end: str
    reference: str
    alternate: str
    gene_function: str
    gene_name: str
    gene_detail: str
    exonic_function: str
    aminoacid_change: str

    """
        SCI	Aggregate somatic clinical impact for this single variant
        SCIDN	ClinVar’s preferred disease name for the concept specified by disease identifiers in SCIDISDB
        SCIDISDB	Tag-value pairs of disease database name and identifier submitted for somatic clinical impact classifications, e.g. MedGen: NNNNNN
        SCIREVSTAT	ClinVar review status of somatic clinical impact for the Variation ID
        ONC	Aggregate oncogenicity classification for the variant
        ONCDN	ClinVar’s preferred disease name for the concept specified by disease identifiers in ONCDISDB
        ONCDISDB	Tag-value pairs of disease database name and identifier submitted for oncogenicity classifications, e.g. MedGen: NNNNNN
        ONCREVSTAT	ClinVar review status of oncogenicity classification for the Variation ID
        ONCCONF	Conflicting oncogenicity classifications for the variant
    """

    clinvar_allele_id: str
    clinvar_disease_name: str
    clinvar_disease_database: str
    clinvar_review_status: str
    clinvar_clinical_sign: str
    clinvar_onco_disease_name: str
    clinvar_onco_disease_database: str
    clinvar_onco_review_status: str
    clinvar_oncogenicity_factor: str

    clinvar_somatic_clinical_impact_disease_name: str
    clinvar_somatic_clinical_impact_disease_database: str
    clinvar_somatic_clinical_impact_review_status: str
    clinvar_somatic_clinical_impact: str

    _1K_Genomics: str
    other_info: str

@dataclass
class AnnotationDataContainer(IReportDataContainer):
    """annotation section (ANN) has a bit of annotations divided by 15 fields such as
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
    HGVS_CDS: str
    HGVS_protein: str
    cDNA: str
    CDS: str
    aminoacid: str
    distance: str
    info: str

class VariantDataLineContainer:
    def __init__(
        self,
        variant1: VariantDataContainer,
        variant2: Optional[VariantDataContainer],
        annotations: list[AnnotationDataContainer]
    ):
        self.variants = {'v1': variant1, 'v2': variant2}
        self.annotations = annotations

    def __str__(self):
        hr_str = ''
        if self.variants['v1']: hr_str += f"Variant 1:\n{self.variants['v1'].__str__()}\n\n"
        if self.variants['v2']: hr_str += f"Variant 2:\n{self.variants['v2'].__str__()}\n\n"
        if self.annotations:
            for annotation in self.annotations: hr_str += f"Annotation:\n{annotation.__str__()}\n"
        return hr_str+'\n'

def main():
    logger = Configurator().logger
    report_conf = Configurator().parse_configuration(target_section='Report')
    avinput_path, csv_path, txt_path = report_conf['avinput_path'], report_conf['csv_path'], report_conf['txt_path']

    from statistics import mean, median
    preparator = AmpliconCoverageDataPreparator(Configurator(), filter_func=mean)
    preparator.perform(sample, os.system)

    with open(txt_path, 'r') as fd: 
        for line in fd.readlines()[1:]:
            if ";ANN=" in line:
                variants_section, annotations_section = line.split(";ANN=")
                var_fields = variants_section.split('\t')

                variant = VariantDataContainer(
                    chromosome=var_fields[0],
                    start=var_fields[1],
                    end=var_fields[2],
                    reference=var_fields[3],
                    alternate=var_fields[4],
                    gene_function=var_fields[5],
                    gene_name=var_fields[6],
                    gene_detail=var_fields[7],
                    exonic_function=var_fields[8],
                    aminoacid_change=var_fields[9],

                    clinvar_allele_id=var_fields[10],
                    clinvar_disease_name=var_fields[11],
                    clinvar_disease_database=var_fields[12],
                    clinvar_review_status=var_fields[13],
                    clinvar_clinical_sign=var_fields[14],

                    clinvar_onco_disease_name=var_fields[15],
                    clinvar_onco_disease_database=var_fields[16],
                    clinvar_onco_review_status=var_fields[17],
                    clinvar_oncogenicity_factor=var_fields[18],

                    clinvar_somatic_clinical_impact_disease_name=var_fields[19], 
                    clinvar_somatic_clinical_impact_disease_database=var_fields[20], 
                    clinvar_somatic_clinical_impact_review_status=var_fields[21], 
                    clinvar_somatic_clinical_impact=var_fields[22],

                    _1K_Genomics=var_fields[23],
                    other_info=var_fields[24:],
                )
                ann_fields = annotations_section.split(";LOF=")[0].split('|')[:16]
                annotation = AnnotationDataContainer(
                    allele=ann_fields[0],
                    annotation=ann_fields[1],
                    annotation_impact=ann_fields[2],
                    gene_name=ann_fields[3],
                    gene_id=ann_fields[4],
                    mutation_type=ann_fields[5],
                    mutation_id=ann_fields[6],
                    transcript_biotype=ann_fields[7],
                    exon=ann_fields[8],
                    HGVS_CDS=ann_fields[9],
                    HGVS_protein=ann_fields[10],
                    cDNA=ann_fields[11],
                    CDS=ann_fields[12],
                    aminoacid=ann_fields[13],
                    distance=ann_fields[14],
                    info=ann_fields[15].split(',')[0]
                )
                print(variant.start, variant.reference, variant.alternate, preparator.count_variant_coverage(variant.chromosome, variant.start, variant.reference, variant.alternate))

if __name__ == '__main__': main()

"""Predicted loss of function (LOF) effects for this variant section has fields
    Gene_Name
    Gene_ID
    Number_of_transcripts_in_gene
    Percent_of_transcripts_affected
"""
"""Predicted nonsense mediated decay (NMD) effects for this variant has fields
    Gene_Name
    Gene_ID
    Number_of_transcripts_in_gene
    Percent_of_transcripts_affected
"""
