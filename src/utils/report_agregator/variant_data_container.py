"""
    This module defines the VariantDataContainer class, which encapsulates
    data related to a genomic variant.  It includes information about the
    variant's location, alleles, associated genes, and potentially
    functional consequences.  This class is designed for structured
    representation of variant data, facilitating analysis and reporting.

    The module also includes a dataclass for VariantDataContainer, inheriting
    from IReportDataContainer (defined in another module) and providing
    methods for accessing and manipulating variant data.

    The module `src.utils.report_agregator.annotation_data_container` is
    imported for potentially including annotation data.
"""

from dataclasses import dataclass

from src.utils.report_agregator.i_report_data_container import IReportDataContainer

@dataclass
class ClinvarVariantAnnotationContainer(IReportDataContainer):
    """
        Here is description of Clinvar database's headers: 
            SCI:
                Aggregate somatic clinical impact for this single variant
            SCIDN:
                ClinVar’s preferred disease name for the concept
                    specified by disease identifiers in SCIDISDB
            SCIDISDB:
                Tag-value pairs of disease database name and identifier
                submitted for somatic clinical impact classifications,
                    e.g. MedGen: NNNNNN
            SCIREVSTAT:
                ClinVar review status of somatic clinical impact
                    for the Variation ID
            ONC:
                Aggregate oncogenicity classification for the variant
            ONCDN:
                ClinVar’s preferred disease name for the concept
                    specified by disease identifiers in ONCDISDB
            ONCDISDB:
                Tag-value pairs of disease database name and identifier submitted
                    for oncogenicity classifications, e.g. MedGen: NNNNNN
            ONCREVSTAT:
                ClinVar review status of oncogenicity classification
                for the Variation ID
            ONCCONF:
                Conflicting oncogenicity classifications for the variant

    """
    allele_id: str
    disease_name: str
    disease_database: str
    review_status: str
    clinical_sign: str
    onco_disease_name: str
    onco_disease_database: str
    onco_review_status: str
    oncogenicity_factor: str

    somatic_clinical_impact_disease_name: str
    somatic_clinical_impact_disease_database: str
    somatic_clinical_impact_review_status: str
    somatic_clinical_impact: str

    def __str__(self):
        self_str = ''
        for key, value in vars(self).items():
            self_str += f"{key}: {value}, "
        return self_str

@dataclass
class VariantDataContainer(IReportDataContainer):
    """
        Represents a container for variant data,
        inheriting from IReportDataContainer.

        This class encapsulates the necessary information about a variant,
        including its genomic location, reference and alternate alleles,
        associated gene information, and functional effects.
        It's designed to be used within a reporting system and
        can likely hold additional attributes.

        Attributes:
            chromosome (str):
                The chromosome the variant is located on.
            start (str):
                The start position of the variant.
            end (str):
                The end position of the variant.
            reference (str):
                The reference allele.
            alternate (str):
                The alternate allele.
            gene_function (str):
                Functional impact on the gene.
            gene_name (str):
                The name of the gene affected.
            gene_detail (str):
                Additional details about the gene.
            exonic_function (str):
                Impact on the exonic region.
            aminoacid_change (str):
                Description of any amino acid changes.
            clinvar (ClinvarVariantAnnotationContainer):
                dataclass for clinvar annotation fields.
            one_thousand_genomics (str):
                Annotation with 1K_Genomics.
            other_info (str):
                Field for the part of the annotation file
                row, that's not a part of
                a first annotation section.
    """
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
    clinvar: ClinvarVariantAnnotationContainer
    one_thousand_genomics: str
    other_info: str

    def __str__(self):
        self_str = ''
        for key, value in vars(self).items():
            if key == 'clinvar':
                self_str += f"{key}: [{str(self.clinvar)}]\n"
            else:
                self_str += f"{key}: {value}\n"
        return self_str
