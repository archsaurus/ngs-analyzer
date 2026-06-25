from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GenotypeAdditionalInfo:
    """DTO for genotype fields in VCF format.

    This data class represents additional genotype information extracted
        from a VCF sample field, including genotype, quality, depths,
        variant frequency, noise level, and strand bias score.

    Attributes:
        gt: Genotype, encoded as allele values separated by '/' or '|'.
            Allele values are 0 for the reference allele (REF field),
            1 for the first alternate allele (ALT),
            2 for the second, and so on.
        gq: Genotype quality score.
        ad: Allele depth for the alternate allele.
        dp: Total depth used for variant calling at this position.
        vf: Variant frequency at this position.
        nl: Applied BaseCall noise level.
        sb: Strand bias score at this position.

    Notes:
        - Genotype is encoded as allele values separated by either '/' or '|'.
        - If any field is missing, it is replaced with a default value.
          For example, if FORMAT is GT:GQ:DP:HQ and the sample field is
          ``0|0:.:23:23,34``, then GQ is missing and will be replaced by
            its default.
        - Trailing fields can be dropped, except GT (which must be present
            if specified in the FORMAT field).
    """

    gt: str
    gq: int
    ad: int
    dp: int
    vf: float
    nl: float
    sb: float


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """Specification for a single genotype field in VCF format parsing.

    This data class defines how to parse and validate a single field
        from the sample genotype data, including its name, position,
        converter function, and default value.

    Attributes:
        name: Field name (e.g. 'GT', 'GQ', 'AD').
        index: Zero-based index of the field in the sample field sequence.
        converter: Function that converts a raw string value
            to the target type. Must accept a single argument and
            return a converted value or raise an exception.
        default: Default value to use when parsing fails
            or the field is missing.
    """

    name: str
    index: int
    converter: Callable[[Any], Any]
    default: Any


@dataclass(frozen=True, slots=True)
class AlleleCoverage:
    reference_count: int
    alternate_count: int
    alternate_frequency: float
