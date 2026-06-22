from collections.abc import Sequence


def allele_depth_converter(allele_raw_data: str) -> int:
    """Convert a raw AD (Allele Depth) field string to an integer.

    The VCF AD field typically contains a comma‑separated list of read depths,
    e.g. "10,5" where the first value is the depth for the reference allele
    and the second value is the depth for the alternate allele. This helper
    extracts the depth of the alternate allele (the second value)
        and returns it as an int.

    Args:
        allele_raw_data (str): A string that contains
            one or more comma‑separated numeric values
            (the raw AD field from a VCF record).

    Returns:
        The integer depth of the alternate allele
            (the value after the first comma).

    Raises:
        ValueError: If the input does not contain a comma, the second element
            cannot be converted to an integer, or the string is otherwise
            malformed.
    """
    try:
        return int(allele_raw_data.split(',')[1])
    except (IndexError, ValueError) as exc:
        raise ValueError('Invalid AD field') from exc


def genotype_converter(genotype_raw_data: str) -> Sequence[str]:
    """Parse a raw genotype string into its individual allele components.

    VCF genotype fields can be represented with either "/" (unphased) or
    "|" (phased) separators, e.g. "0/1", "1|0", or a single allele
    such as "." for missing data. This function normalises the representation
    by splitting on the appropriate separator and stripping whitespace from
    each allele.

    Args:
        genotype_raw_data (str): The raw genotype string from a VCF record.

    Returns:
        A tuple of allele strings. If the input contains a separator ("/" or
        "|"), the tuple will contain each allele in order; otherwise a
        single‑element tuple is returned containing the trimmed raw string.

    Raises:
        None. The function never raises; malformed strings are returned as‑is
        (after stripping).
    """
    if '/' in genotype_raw_data:
        separator = '/'
    elif '|' in genotype_raw_data:
        separator = '|'
    else:
        return (genotype_raw_data.strip(),)

    return tuple(part.strip() for part in genotype_raw_data.split(separator))
