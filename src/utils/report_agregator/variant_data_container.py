from . import *

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
