import logging
from collections.abc import Sequence
from typing import Any, Optional

from ngs_analyzer.core.report.coverage_collector import constants
from ngs_analyzer.core.report.coverage_collector.converters import (
    allele_depth_converter, genotype_converter)
from ngs_analyzer.core.report.coverage_collector.dto import (
    FieldSpec, GenotypeAdditionalInfo)

GENOTYPE_FIELD_SPECS = (
    FieldSpec('GT', 0, genotype_converter, constants.DEFAULT_GENOTYPE_DATA),
    FieldSpec('GQ', 1, int, constants.DEFAULT_GENOTYPE_QUALITY),
    FieldSpec('AD', 2, allele_depth_converter, constants.DEFAULT_ALLELE_DEPTH),
    FieldSpec('DP', 3, int, constants.DEFAULT_TOTAL_DEPTH),
    FieldSpec('VF', 4, float, constants.DEFAULT_VARIANT_FREQUENCY),
    FieldSpec('NL', 5, float, constants.DEFAULT_NOISE_LEVEL),
    FieldSpec('SB', 6, float, constants.DEFAULT_STRAND_BIAS_SCORE),
)
"""Genotype field specifications for VCF format parsing.

Each entry defines:
    - field name (e.g. 'GT', 'GQ'),
    - index in the sample field (0-based),
    - converter function to parse the raw string value,
    - default value to use when parsing fails.
"""


def _warn_about_validation_error(
    field_name: str,
    exc: Exception,
    default_field_value: Any,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Log a warning about a validation error for a genotype field.

    Args:
        field_name (str): Name of the genotype field (e.g. 'GT', 'GQ', 'AD').
        exc (Exception): Exception that occurred during validation.
        default_field_value (Any): Default value to use for the field
            when validation fails.
        logger (logging.Logger | None): Logger instance to use.
            If None, the module logger is used.
    """
    logger = logger or logging.getLogger(__name__)
    logger.warning(
        'Caught exception "%s" while validating field "%s", set default "%s"',
        exc,
        field_name,
        default_field_value,
    )


def _empty_genotype(
    logger: Optional[logging.Logger] = None,
) -> GenotypeAdditionalInfo:
    """Return a GenotypeAdditionalInfo DTO with all default values.

    This function is used when the input line cannot be parsed as a valid VCF
        genotype line. It also logs a warning to indicate that parsing failed.

    Args:
        logger (logging.Logger | None): Logger instance to use. If None,
            the module logger is used.

    Returns:
        GenotypeAdditionalInfo instance populated with default values
            for all genotype fields.
    """
    logger = logger or logging.getLogger(__name__)
    logger.warning(
        'Unable to parse FORMAT string from the line, return an empty DTO',
    )

    return GenotypeAdditionalInfo(
        gt=constants.DEFAULT_GENOTYPE_DATA,
        gq=constants.DEFAULT_GENOTYPE_QUALITY,
        ad=constants.DEFAULT_ALLELE_DEPTH,
        dp=constants.DEFAULT_TOTAL_DEPTH,
        vf=constants.DEFAULT_VARIANT_FREQUENCY,
        nl=constants.DEFAULT_NOISE_LEVEL,
        sb=constants.DEFAULT_STRAND_BIAS_SCORE,
    )


def _validate_genotype_fields(
    fields: Sequence[Any],
) -> GenotypeAdditionalInfo:
    """Convert a sequence of raw genotype field values to a typed \
        GenotypeAdditionalInfo DTO.

    This function iterates over GENOTYPE_FIELD_SPECS,
        applies the configured converter for each field,
        and falls back to the default value when conversion fails.
    Conversion errors are logged as warnings via _warn_about_validation_error.

    Args:
        fields (Sequence): Sequence of raw genotype field values (strings)
            in the order defined by the VCF FORMAT field
            (e.g. ['0/1', '45', '1,20', '30', '0.67', '0.01', '0.02']).

    Returns:
        GenotypeAdditionalInfo instance with all fields converted
            to their correct types. If a field cannot be parsed,
            its default value is used.
    """
    values: dict[str, Any] = {}

    for spec in GENOTYPE_FIELD_SPECS:
        try:
            raw_value = fields[spec.index]
            values[spec.name] = spec.converter(raw_value)

        except (IndexError, ValueError, TypeError) as exc:
            _warn_about_validation_error(spec.name, exc, spec.default)
            values[spec.name] = spec.default

    return GenotypeAdditionalInfo(
        gt=values.get('GT'),
        gq=values.get('GQ'),
        ad=values.get('AD'),
        dp=values.get('DP'),
        vf=values.get('VF'),
        nl=values.get('NL'),
        sb=values.get('SB'),
    )


def parse_genotype_fields(line: str) -> GenotypeAdditionalInfo:
    """Parse genotype fields from a VCF-like line and \
        return a GenotypeAdditionalInfo DTO.

    Args:
        line (str): A single line from a VCF-like file (e.g. multianno file),
            including the FORMAT field and sample genotype data.

    Returns:
        GenotypeAdditionalInfo instance with parsed genotype fields.
        If the line cannot be parsed, a DTO with
            default values is returned instead of raising an exception.
    """
    stripped = line.strip()

    if not stripped or stripped.startswith('#'):
        return _empty_genotype()

    if constants.DEFAULT_GENOTYPE_FIELDS_PATTERN not in stripped:
        return GenotypeAdditionalInfo(
            gt=constants.DEFAULT_GENOTYPE_DATA,
            gq=constants.DEFAULT_GENOTYPE_QUALITY,
            ad=constants.DEFAULT_ALLELE_DEPTH,
            dp=constants.DEFAULT_TOTAL_DEPTH,
            vf=constants.DEFAULT_VARIANT_FREQUENCY,
            nl=constants.DEFAULT_NOISE_LEVEL,
            sb=constants.DEFAULT_STRAND_BIAS_SCORE,
        )

    _, meta_tags = stripped.split(constants.DEFAULT_GENOTYPE_FIELDS_PATTERN)
    return _validate_genotype_fields(fields=meta_tags.split(':'))
