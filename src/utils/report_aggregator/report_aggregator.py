"""This module processes genetic variant data and \
generates a comprehensive report.

Overview:
    The script reads annotation and
    coverage data for a given biological sample,
    consolidates variant information with annotations,
    and outputs a summarized report in Excel format.

Main functionalities:
    - Parses configuration to determine target genomic regions.
    - Performs coverage analysis on specified regions.
    - Reads variant annotation data from a text file.
    - Extracts relevant variant and annotation details.
    - Calculates coverage metrics for each variant.
    - Compiles the data into a structured report using a data container.
    - Exports the report as an Excel file for further analysis.

Usage:
    This script is intended to be run as
        a standalone module, with the `main()`
    function invoked with a `SampleDataContainer`
        object representing the sample.

Dependencies:
    - pandas:
        for data manipulation and Excel output.
    - os:
        for filesystem operations.
    - Other project-specific modules imported with `from . import *`.

Note:
    Ensure that all required input files
    (e.g., annotation text files) are available, and that configuration
    settings are properly set up before running.
"""

# region Imports
import os

from statistics import mean

import pandas

from src.core.analyzer.amplicon_coverage_computer import \
    AmpliconCoverageDataPreparator
from src.core.sample_data_container import SampleDataContainer
from src.configurator import Configurator

from src.utils.report_aggregator.i_report_data_container import \
    IReportDataContainer
from src.utils.report_aggregator.variant_data_container import \
    VariantDataContainer

from src.utils.report_aggregator.variant_coverage_dto import VariantCoverageDTO
from src.utils.report_aggregator.gene_details_dto import GeneDetailsDTO
from src.utils.report_aggregator.report_dto import ReportDTO

from src.utils.report_aggregator.variant_data_container import \
    ClinvarVariantAnnotationContainer
from src.utils.report_aggregator.annotation_data_container import \
    AnnotationDataContainer
# endregion


def parse_variant_section(row: str) -> IReportDataContainer:
    r"""Parse a variant section string into a VariantDataContainer object.

    Args:
        row (str):
            A tab-separated string containing variant information.

    Returns:
        IReportDataContainer:
            An instance of VariantDataContainer
            populated with parsed data.

    Example:
        row = "chr1\t12345\t12345\tA\tT\tmissense_variant\
            \tGENE1\tGeneName1\tmissense\tp.Val600Glu\t12345\
            \tDiseaseX\tDatabaseY\treviewed\tpathogenic\
            \tDiseaseY\tDatabaseZ\treviewed\toncogenic\
            \tHigh\tLow\tModerate\tYes\t..."

        variant = parse_variant_section(row)
    """
    var_fields = row.split('\t')

    variant = VariantDataContainer(
        chromosome=var_fields[0],
        start=var_fields[28],  # var_fields[1],
        end=var_fields[2],
        reference=var_fields[3],
        alternate=var_fields[4],
        gene_function=var_fields[5],
        gene_name=var_fields[6],
        gene_detail=var_fields[7],
        exonic_function=var_fields[8],
        aminoacid_change=var_fields[9],
        clinvar=ClinvarVariantAnnotationContainer(
            allele_id=var_fields[10],
            disease_name=var_fields[11],
            disease_database=var_fields[12],
            review_status=var_fields[13],
            clinical_sign=var_fields[14],

            onco_disease_name=var_fields[15],
            onco_disease_database=var_fields[16],
            onco_review_status=var_fields[17],
            oncogenicity_factor=var_fields[18],

            somatic_clinical_impact_disease_name=var_fields[19],
            somatic_clinical_impact_disease_database=var_fields[20],
            somatic_clinical_impact_review_status=var_fields[21],
            somatic_clinical_impact=var_fields[22]),

        one_thousand_genomics=var_fields[23],
        other_info=var_fields[24:])

    return variant


class FirstAnnotation(AnnotationDataContainer):
    """Represents a detailed annotation of a genetic mutation
    with specific gene and transcript information.

    This class encapsulates annotation data including gene name,
    mutation identifier, transcript biotype, exon information,
    and HGVS nomenclature for both cDNA and protein changes.

    It provides a method to convert the annotation data into a dictionary
    format for further processing or output.

    Note:
        This class was developed to meet the specific data representation
        needs of a laboratory.
    """

    def to_dict(self):
        return {
            "Gene name": self.gene_name,
            "Annotation": self.annotation,
            "Mutation ID": self.mutation_id,
            "Transcript type": self.transcript_biotype,
            "Exon": self.exon,
            "HGVS.c": self.hgvs_cds,
            "HGVS.p": self.hgvs_protein}


class NextAnnotation(AnnotationDataContainer):
    """Represent a simplified annotation of a genetic mutation \
    focusing on core transcript information.

    This class includes essential annotation details such as gene name,
    mutation identifier, transcript biotype, exon information,
    and HGVS nomenclature for cDNA and protein changes.

    It provides a method to convert the data
    into a dictionary format suitable for downstream applications.

    Note:
        This class was developed to meet the specific data representation
        needs of a particular laboratory.
    """

    def to_dict(self):
        return {
            "Gene name": self.gene_name,
            "Mutation ID": self.mutation_id,
            "Transcript type": self.transcript_biotype,
            "Exon": self.exon,
            "HGVS.c": self.hgvs_cds,
            "HGVS.p": self.hgvs_protein}


def parse_annotation_section(row: str) -> list[IReportDataContainer]:
    """Parses an annotation section string
    into an AnnotationDataContainer object.

    Args:
        row (str):
            A string containing annotation information,
            with fields separated by '|'.
            The string may contain additional data separated by ';LOF=',
                which is ignored here.

    Returns:
        IReportDataContainer:
            An instance of AnnotationDataContainer
                populated with parsed data.

    Example:
        row = "A|missense_variant|MODERATE|GeneX|ID123|missense|rs123\
            |protein_coding|exon2|c.123A>T|p.Lys41Asn|cDNA info|CDS info\
            |Ala|100bp|info,more"

        annotation = parse_annotation_section(row)
    """
    annotations = []
    sub_annotations = row.split(";LOF=")[0].split('|,')

    for ann_fields in sub_annotations:
        annotations_count = 0

        ann_fields = ann_fields.split('|')
        fields_count = len(ann_fields)
        if fields_count < 16:
            for _ in range(fields_count, 16):
                ann_fields.append('')

        if annotations_count > 0:
            Annotation = NextAnnotation
        else:
            Annotation = FirstAnnotation

        annotations.append(Annotation(
            allele=ann_fields[0],
            annotation=ann_fields[1],
            annotation_impact=ann_fields[2],
            gene_name=ann_fields[3],
            gene_id=ann_fields[4],
            mutation_type=ann_fields[5],
            mutation_id=ann_fields[6],
            transcript_biotype=ann_fields[7],
            exon=ann_fields[8],
            hgvs_cds=ann_fields[9],
            hgvs_protein=ann_fields[10],
            c_dna=ann_fields[11],
            cds=ann_fields[12],
            aminoacid=ann_fields[13],
            distance=ann_fields[14],
            info=ann_fields[15]))

    return annotations


def aggregate_report(sample: SampleDataContainer = None):
    """Main processing function.

    Reads annotation data,
    performs coverage analysis,
    and generates a report.
    """
    logger = Configurator().logger

    txt_path = os.path.abspath(os.path.join(
        sample.processing_path, sample.sid+".ann.hg19_multianno.txt"))

    if not os.path.exists(sample.report_path):
        os.makedirs(sample.report_path)

    logger.info(
        f"Starting to perform report aggregation for sample {sample.sid}")
    logger.debug(
        "Report aggregator configuration:\n"
        "Target regions:\n\t(Region, mpileup filepath): "
        f"""{'\n\t(Region, mpileup filepath): '.join(
            [f"({region}, {path})" for (region, path) in sample.target_regions]
            )}\n""")

    preparator = AmpliconCoverageDataPreparator(
        Configurator(), filter_func=mean)
    preparator.perform(sample, os.system)

    report_list = []

    with open(file=txt_path, mode='r', encoding='utf-8') as fd:
        for line in fd.readlines()[1:]:
            if ";ANN=" in line:
                depth, alt_count, alt_coverage = 0, 0, 0

                variant, annotations = map(
                    lambda s, parser: parser(s),
                    line.split(";ANN="),
                    [parse_variant_section, parse_annotation_section])

                data = preparator.count_variant_coverage(
                    variant.chromosome.replace('chr', '').strip(),
                    variant.start,
                    variant.reference,
                    variant.alternate)
                if data:
                    depth, alt_count, alt_coverage = data

                    if alt_count < 1:
                        continue

                report_list.append(ReportDTO(
                    sample.sid,
                    VariantCoverageDTO(
                        variant.chromosome,
                        variant.start,
                        variant.reference,
                        variant.alternate,
                        depth - alt_count if depth != -1 else -1,
                        alt_count,
                        alt_coverage),
                    GeneDetailsDTO(annotations),
                    variant.one_thousand_genomics,
                    variant.clinvar.clinical_sign))

    report_dataframe = pandas.DataFrame([report_column for report_column in [
        report.to_dict() for report in report_list]])

    report_dataframe.to_excel(excel_writer=f"{
            os.path.join(sample.report_path, sample.sid+'.report.xlsx')}",
        sheet_name="main", index=False)


if __name__ == '__main__':
    cfg = Configurator()
