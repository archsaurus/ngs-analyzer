from collections.abc import Sequence
import os
from typing import Optional

from ngs_analyzer.core.report.coverage_collector.dto import (
    AlleleCoverage, GenotypeAdditionalInfo)
from ngs_analyzer.core.report.coverage_collector.parsers import \
    parse_genotype_fields


def parse_allele_coverage(line: str) -> AlleleCoverage:
    """Parse a VCF‑style line and return an allele coverage object.

    The function extracts the genotype‑related fields (depth, allele depth and
    variant frequency) from a raw annotation line using parse_genotype_fields,
    then converts those values into a compact representation that summarises
    the coverage of the reference and alternate alleles.

    Args:
        line (str): A single line from a Multianno/VCF‑style file containing
            the genotype information. The line is expected to be in the same
            format accepted by parse_genotype_fields.

    Returns:
        An AlleleCoverage instance with three attributes:
            * reference_count – the absolute difference between the total
                read depth (DP) and the alternate‑allele depth (AD);
                this gives the number of reads supporting the reference allele.
            * alternate_count – the raw alternate‑allele depth (AD).
            * alternate_frequency – the variant frequency (VF) as a float.

    Raises:
        ValueError: If parse_genotype_fields cannot parse the input line
            (i.e. it returns None or a malformed object). The function
            assumes that a valid GenotypeAdditionalInfo instance is returned;
            otherwise a ValueError is raised to make the failure explicit.
    """
    genotype_fields: GenotypeAdditionalInfo = parse_genotype_fields(line)

    return AlleleCoverage(
        reference_count=abs(genotype_fields.dp - genotype_fields.ad),
        alternate_count=genotype_fields.ad,
        alternate_frequency=genotype_fields.vf,
    )


def parse_multianno(
    annotation_filepath: Optional[str] = None
) -> Sequence[tuple[int, AlleleCoverage]]:
    """Parse a Multianno‑style annotation file and return a summary table.

    The function expects a tab‑delimited file where the first line is a header.
    For each subsequent line it extracts genotype‑related fields
        (depth, allele depth, variant‑frequency, ...) using
        parse_genotype_fields and returned values is a DTO consisting of:
            a record counter, the absolute difference between
            total depth (DP) and allele depth (AD),
            the allele depth (AD) itself,
            the variant frequency (VF).

    Args:
        annotation_filepath: Path to the Multianno file to be processed.
            If 'None' (the default) the function will raise a ValueError.

    Returns:
        Sequence[tuple[int, AlleleCoverage]]:
            a Sequence object, containig set of tuples like (index, coverage)

    Raises:
        ValueError: If annotation_filepath is Non` or an empty string.
        FileNotFoundError: If the supplied path does not point to an existing
            regular file.
        OSError: Propagated from the underlying open call if the file cannot
            be opened for reading (e.g., permission errors).

    Note:
        The function prints directly to the console; it is intended for quick
        inspection or for use in a pipeline where the printed table
        is captured downstream.
    """
    if not annotation_filepath:
        raise ValueError('annotation_filepath must be a non‑empty string.')

    if not os.path.isfile(annotation_filepath):
        raise FileNotFoundError(f'File not found: {annotation_filepath}')

    coverage_seq: list[tuple[int, AlleleCoverage]] = []
    with open(annotation_filepath, mode='r', encoding='utf-8') as multianno_fd:
        cnt: int = 1
        for line in multianno_fd.readlines()[1:]:
            coverage_seq.append((cnt, parse_allele_coverage(line)))
            cnt += 1
    return coverage_seq


if __name__ == '__main__':
    print(
            parse_multianno(
            '/home/archsaurus/Documents/code/ngs-analyzer-refactoring'
            '/output_20260522_202744'
            '/BRCA_65222/BRCA_65222.ann.hg19_multianno.txt'
        )
    )
