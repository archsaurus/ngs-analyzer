from src.core.base import *
import abc

from dataclasses import dataclass, fields
from itertools import zip_longest

from src.configurator import Configurator
from src.core.sample_data_container import SampleDataContainer
from src.core.analyzer.amplicon_coverage_computer import AmpliconCoverageDataPreparator

from .i_report_data_container import IReportDataContainer
from .annotation_data_container import AnnotationDataContainer
from .variant_data_container import VariantDataContainer, VariantDataLineContainer

genotype_format_aliases = {
    'GT': "Genotype",
    'GQ': "Genotype Quality",
    'AD': "Allele Depth",
    'DP': "Total Depth Used For Variant Calling",
    'VF': "Variant Frequency",
    'NL': "Applied BaseCall Noise Level",
    'SB': "StrandBias Score"
}
