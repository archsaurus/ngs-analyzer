"""
    This module processes genetic variant data and
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
from dataclasses import dataclass

from statistics import mean

import pandas

from src.core.analyzer.amplicon_coverage_computer import AmpliconCoverageDataPreparator
from src.core.sample_data_container import SampleDataContainer
from src.configurator import Configurator

from src.utils.report_agregator.i_report_data_container import IReportDataContainer
from src.utils.report_agregator.variant_data_container import VariantDataContainer
from src.utils.report_agregator.variant_data_container import ClinvarVariantAnnotationContainer
from src.utils.report_agregator.annotation_data_container import AnnotationDataContainer

from src.utils.util import reg_tuple_generator
# endregion

@dataclass
class VariantCoverageDTO(IReportDataContainer):
    """
        Represents the coverage information for a variant.

        Attributes:
            chromosome (str):
                The chromosome the variant is located on.
            start (str):
                The starting position of the variant on the chromosome.
            reference (str):
                The reference allele.
            alternate (str):
                The alternate allele.
            ref_count (str):
                The count of the reference allele.
                Should ideally be a numeric type.
            alt_count (str):
                The count of the alternate allele.
                Should ideally be a numeric type.
            alt_coverage (str):
                The coverage of the alternate allele.
                Should ideally be a numeric type.
    """
    chromosome: str
    start: str
    reference: str
    alternate: str
    ref_count: str
    alt_count: str
    alt_coverage: str

    def to_dict(self):
        return {
            "Chromosome": self.chromosome,
            "Start": self.start,
            "Reference": self.reference,
            "Alternate": self.alternate,
            "Reference count": self.ref_count,
            "Alternate  count": self.alt_count,
            "Alternate coverage": self.alt_coverage}

@dataclass
class GeneDetailsDTO(IReportDataContainer):
    """
        Represents detailed information about a gene, including its
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
    gene_name: str
    gene_detail: str # transcript id
    exon: str
    hgvs_cds: str
    hgvs_protein: str

    def to_dict(self):
        return {
            "Gene name": self.gene_name,
            "Gene detail": self.gene_detail,
            "Exon": self.exon,
            "HGVS_CDS": self.hgvs_cds,
            "HGVS_Protein": self.hgvs_protein}

@dataclass
class ReportDTO(IReportDataContainer):
    """Data container for report entries."""
    id: str
    variant_coverage: VariantCoverageDTO
    annotation: str
    gene_details: GeneDetailsDTO
    one_thousand_genomics: str
    clinvar_clinical_sign: str

    def to_dict(self):
        result_dict = {"Sample ID": self.id}
        result_dict.update(self.variant_coverage.to_dict())
        result_dict.update({"Annotation": self.annotation})
        result_dict.update(self.gene_details.to_dict())
        result_dict.update({"Clinical sign": self.clinvar_clinical_sign})

        return result_dict

def parse_variant_section(row: str) -> IReportDataContainer:
    """
        Parses a variant section string into a VariantDataContainer object.

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
        start=var_fields[1],
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

def parse_annotation_section(row: str) -> IReportDataContainer:
    """
        Parses an annotation section string
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
    ann_fields = row.split(";LOF=")[0].split('|')[:16]

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
        hgvs_cds=ann_fields[9],
        hgvs_protein=ann_fields[10],
        c_dna=ann_fields[11],
        cds=ann_fields[12],
        aminoacid=ann_fields[13],
        distance=ann_fields[14],
        info=ann_fields[15].split(',')[0])

    return annotation

def agregate_report(
    target_regions: (str, str),
    sample: SampleDataContainer=None
    ):
    """
        Main processing function.

        Reads annotation data,
        performs coverage analysis,
        and generates a report.
    """
    logger = Configurator().logger
    report_conf = Configurator().parse_configuration(
        target_section='Report')

    txt_path = os.path.abspath(os.path.join(
        sample.processing_path, sample.sid+".ann.hg19_multianno.txt"))

    if not os.path.exists(sample.report_path):
        os.makedirs(sample.report_path)

    logger.info(
        f"Starting to perform report agregation for sample {sample.sid}")
    logger.debug(
        "Report agregator configuration:\n"
        "Target regions:\n\t(Region, mpileup filepath): "
        f"""{'\n\t(Region, mpileup filepath): '.join(
            [f"({region}, {path})" for (region, path) in target_regions]
            )}\n"""
        f"{'\n\t'.join(
            [str(key)+': '+str(value) for (key, value) in report_conf.items()]
            )}")

    preparator = AmpliconCoverageDataPreparator(
        Configurator(), filter_func=mean)
    preparator.perform(sample, target_regions, os.system)

    report_list = []

    with open(txt_path, 'r', encoding='utf-8') as fd:
        for line in fd.readlines()[1:]:
            if ";ANN=" in line:
                variant, annotation = map(
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
                    # barcode7, barcode5,
                    VariantCoverageDTO(
                        variant.chromosome,
                        variant.start,
                        variant.reference,
                        variant.alternate,
                        depth - alt_count if depth != -1 else -1, # ref_count
                        alt_count,
                        alt_coverage),
                    annotation.annotation,
                    GeneDetailsDTO(
                        variant.gene_name,
                        variant.gene_detail, # transcript id
                        annotation.exon,
                        annotation.hgvs_cds,
                        annotation.hgvs_protein),
                    variant.one_thousand_genomics,
                    variant.clinvar.clinical_sign))

    report_dataframe = pandas.DataFrame([report_column for report_column in [
        report.to_dict() for report in report_list]])

    report_dataframe.to_excel(excel_writer=f"{
            os.path.join(sample.report_path, sample.sid+'.report.xlsx')}",
        sheet_name="main")

if __name__ == '__main__':
    cfg = Configurator()
