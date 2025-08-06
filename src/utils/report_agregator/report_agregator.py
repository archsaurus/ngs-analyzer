from . import *

@dataclass
class ReportDTO(IReportDataContainer):
    id: str
    # barcode7,
    # barcode5,
    chromosome: str
    start: str
    reference: str
    alternate: str
    ref_count: str
    alt_count: str
    alt_coverage: str
    annotation: str
    gene_name: str
    gene_detail: str # transcript id
    exon: str
    HGVS_CDS: str
    HGVS_protein: str
    _1K_Genomics: str
    clinvar_clinical_sign: str

def main():
    logger = Configurator().logger
    report_conf = Configurator().parse_configuration(target_section='Report')
    avinput_path, csv_path, txt_path = report_conf['avinput_path'], report_conf['csv_path'], report_conf['txt_path']

    from statistics import mean, median
    preparator = AmpliconCoverageDataPreparator(Configurator(), filter_func=mean)
    preparator.perform(sample, os.system)

    report_list = []

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

                depth, alt_count, alt_coverage = preparator.count_variant_coverage(variant.chromosome.replace('chr', ''), variant.start, variant.reference, variant.alternate)
                ref_count = depth - alt_count

                report_list.append(ReportDTO(
                    sample.id,
                    # barcode7,
                    # barcode5,
                    variant.chromosome,
                    variant.start,
                    variant.reference,
                    variant.alternate,
                    ref_count,
                    alt_count,
                    alt_coverage,
                    annotation.annotation,
                    variant.gene_name,
                    variant.gene_detail, # transcript id
                    annotation.exon,
                    annotation.HGVS_CDS,
                    annotation.HGVS_protein,
                    variant._1K_Genomics,
                    variant.clinvar_clinical_sign
                    ))
    import pandas
    report = pandas.DataFrame(report_list)
    report.to_excel(
        excel_writer=f"{os.path.join(sample.processing_path, sample.id+'.report.xlsx')}",
        sheet_name="main",
        )

if __name__ == '__main__': main()
