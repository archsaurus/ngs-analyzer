"""
    This module defines the AmpliconCoverageDataPreparator class
    and associated components for analyzing sequencing data coverage
    within specified genomic regions.

    Modules and Classes:
    - PositionNotFoundError:
        Custom exception raised when a specific genomic
        position cannot be found in a mpileup file.

    - AmpliconCoverageDataPreparator:
        A class responsible for generating mpileup files
        for given sample regions, calculating coverage metrics,
        and analyzing variant coverage at specific positions.
        It inherits from LoggerMixin for logging capabilities
        and IDataPreparator to adhere to a data preparation interface.

    Key functionalities:
        - Generating mpileup files for sample regions using samtools.
        - Counting coverage over regions based on mpileup data.
        - Counting variant coverage at specific genomic positions.
        - Performing the entire process of mpileup generation and coverage calculation.
        - Managing configuration and executing system commands for data processing.

    Usage:
        Instantiate the class with a configuration object and a filter function,
        then call `perform()` with a sample data container, target regions,
        and an executor to process coverage analysis for sequencing samples.

    Note:
        Ensure that the configuration file contains correct paths
        and parameters, especially for 'samtools' and 'bedtools'.
        The class also relies on the presence of mpileup files
        and the ability to generate them via command-line tools.

"""

# region Imports
import os
import sys
import re

import mmap

from os import PathLike
from typing import Union, AnyStr

from src.configurator import Configurator

from src.core.base import LoggerMixin
from src.core.base import CommandExecutor

from src.core.base import execute
from src.core.base import touch
from src.core.base import get_platform

from src.core.sample_data_container import SampleDataContainer

from src.core.analyzer.i_data_preparator import IDataPreparator

from src.utils.util import depth_filter
# endregion

class PositionNotFoundError(Exception):
    """Base exception for handling source file positions management process"""

class AmpliconCoverageDataPreparator(LoggerMixin, IDataPreparator):
    """
        The AmpliconCoverageDataPreparator class is designed to
        generate mpileup files for specified regions of a sequenced sample
        and calculate coverage metrics within those regions.
        It also provides methods to count coverage over regions and analyze
        variant coverage at specific positions.
        
        Inherits from LoggerMixin and IDataPreparator,
        ensuring logging capabilities and adherence to
        data preparation interface.
    """
    def __init__(
        self,
        configurator: Configurator,
        filter_func: callable
        ):
        """
            Initializes the AmpliconCoverageDataPreparator
            with configuration and filter function.
            
            Args:
                configurator (Configurator):
                    The configuration object containing settings and paths.
                filter_func (callable):
                    A function to filter coverage data, e.g.,
                    calculating average or median.
        """
        super().__init__(logger=configurator.logger)

        self.configurator = configurator
        self.config = self.configurator.parse_configuration(
            target_section='samtools')

        # a file with lines in format
        # "chrom_number, region_start, region_end, depth"
        self.coords = self.config['coords-file']

        self.filter_func = filter_func

        self.mpileup_files = {}
        self.results = []

    def generate_mpileup(
        self,
        sample: SampleDataContainer,
        regions: list[tuple[str, str]],
        executor: Union[CommandExecutor, callable]
        ) -> list[PathLike[AnyStr]]:
        """
            Generates mpileup files for specified regions of the sample.

            Args:
                sample (SampleDataContainer):
                    The sample containing sequencing data.
                regions (list of tuples):
                    List of regions specified as (region_name, out_name).
                executor (callable):
                    The command executor or function to run system commands.

            Returns:
                list of PathLike: Paths to the generated mpileup files.
        """
        mp_files = []

        for region, out_name in regions:
            out_path = os.path.join(
                sample.processing_path, f"{sample.sid}.{out_name}")

            cmd = ' '.join([
                self.configurator.config['samtools'], "mpileup",
                sample.bam_filepath,
                # skip bases with baseQ/BAQ smaller than value was given
                # '--min-BQ', self.config['min-bq'],
                '--no-BAQ' if 'no-BAQ' in self.config else '',
                '--max-depth', self.config['max-depth'],
                '--region', "chr"+region,
                '--reference', self.configurator.config['reference'],
                '--count-orphans', # do not discard anomalous read pairs
                '--output', out_path])

            execute(executor, cmd)

            depth_filter(
                filepath=out_path,
                depth=15,
                logger=self.logger)            

            mp_files.append(out_path)

        return mp_files

    def count_region_coverage(
        self,
        mpileup: PathLike[AnyStr],
        chromosome: Union[int, str],
        start: Union[int, str],
        end: Union[int, str]
        ) -> float:
        """
            Counts the coverage within a specified region
                from a mpileup file.
            
            Args:
                mpileup (PathLike):
                    Path to the mpileup file.
                chromosome (int or str):
                    Chromosome identifier.
                start (int or str):
                    Start position of the region.
                end (int or str):
                    End position of the region.
            
            Returns:
                float:
                    The filtered average coverage within the region.
        """
        try:
            start, end = int(start), int(end)
            if start > end:
                start, end = end, start

            chromosome = str(chromosome).upper()
            try:
                with open(mpileup, 'r', encoding='utf-8') as fd:
                    coverages = []
                    last_position = start - 1

                    for line in fd:
                        chrom, position, _, depth = line.strip().split('\t')[:4]

                        position, depth = int(position), int(depth)

                        chrom = chrom.upper().replace('CHR', '')
                        if chromosome != chrom or start > position or 'X' in chrom:
                            continue
                        if position > end > 0:
                            break

                        if position > last_position + 1:
                            coverages.extend([0] * (position - last_position - 1))

                        coverages.append(depth)
                        last_position = position
                    if coverages:
                        if len(coverages) < end - start + 1:
                            coverages.extend(
                                [0] * (end - start + 1 - len(coverages)))

                        return self.filter_func(coverages)
                    return 0.0
            except FileNotFoundError:
                self.logger.warning(
                    "There is no mpileup-file for chromosome %s", chromosome)

                return 0.0

        except (SyntaxError, TypeError, OSError, IOError) as e:
            self.logger.critical(
                "An error '%s' occured in '%s.%s'. Abort",
                e, self.__class__.__name__,
                self.perform.__func__.__name__)
            raise e

    def count_indels(
        self,
        data: str
        ) -> (int, int, int, int):
        """
            Counts the number of insertions and deletions
            for two replicates (r1 and r2) based on
            the input data string.

            Args:
                data (str):
                    A string containing insertion and deletion patterns
                    in the form '+<number><bases>' or '-<number><bases>',
                    where <bases> is a sequence of [ACTGNactgn] characters.

            Returns:
                tuple (int, int, int, int): \\
                    r1_ins_count:
                        Number of insertions for replicate r1 \\
                    r1_del_count:
                        Number of deletions for replicate r1 \\
                    r2_ins_count:
                        Number of insertions for replicate r2 \\
                    r2_del_count:
                        Number of deletions for replicate r2
        """
        matches = re.findall(
            r'([+-])(\d+)([ACTGNactgn]+)', data)

        r1_ins_count = 0
        r1_del_count = 0
        r2_ins_count = 0
        r2_del_count = 0

        for sign, number, bases in matches:
            if sign == '+':
                if bases.islower():
                    r2_ins_count += 1
                elif bases.isupper():
                    r1_ins_count += 1
            elif sign == '-':
                if bases.islower():
                    r2_del_count += 1
                elif bases.isupper():
                    r1_del_count += 1

        return (
            r1_ins_count,
            r1_del_count,
            r2_ins_count,
            r2_del_count)

    def count_variant_coverage(
        self,
        chromosome: Union[int, str],
        position: Union[int, str],
        ref: str,
        alt: str
        ) -> (int, int, float):
        """
            Calculates coverage information and variant counts
            at a specific genomic position from mpileup data.

            Args:
                chromosome (int or str):
                    The chromosome identifier (number or string).
                position (int or str):
                    The genomic position to analyze.
                ref (str):
                    The reference allele at the position.
                alt (str):
                    The alternative allele at the position.

            Returns:
                tuple: \\
                    depth (int):
                        The total read depth at the position. \\
                    total_alt_count (int):
                        The total count of reads supporting
                        the alternative allele, including indels. \\
                    alt_ratio (float):
                        The ratio of reads supporting the alternative allele
                        to total depth, rounded to 3 decimal places.

            Note:
                - This method searches for the specified position
                in a chromosome-specific mpileup file.
                - It uses memory-mapped file access for efficiency.
                - It counts reference matches ('.' and ',')
                and mismatches (based on alt allele).
                - It also calls `count_indels()` to count insertions
                and deletions supporting the variant.
                - Returns (-1, -1, -1) if the position is not found
                or an error occurs.
                - Raises FileNotFoundError if the mpileup file
                for the chromosome does not exist.
        """
        self.logger.debug(
            "Starting to determine (%s:%s>%s, %s) variant coverage",
            chromosome, ref, alt, position)

        chromosome = str(chromosome)#.replace('chr', '').strip()
        position = str(position).strip()

        chromosome = '0'+chromosome if chromosome in [
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] else chromosome

        if chromosome in self.mpileup_files:
            self.logger.debug(
                "Chromosome %s found on %s",
                chromosome,
                os.path.abspath(self.mpileup_files[chromosome]))

            try:
                with open(self.mpileup_files[chromosome], 'r', encoding='utf-8') as fd:
                    self.logger.debug(
                        "File '%s' opened with 'r' flag",
                        os.path.abspath(self.mpileup_files[chromosome]))

                    with mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        b_position = mm.find(bytes(
                            position, encoding='utf-8'))

                        if b_position != 0:
                            line_number = mm.rfind(b'\n', 0, b_position) + 1
                            line_number = mm[:line_number].count(b'\n') + 1

                            self.logger.debug(
                                "Position '%s' found at line %s",
                                position, line_number)

                            # region Rules:
                            #   Forward Reverse Meaning
                            #   . dot	, comma	Base matches the reference base
                            #   ACGTN	  acgtn	Base is a mismatch to the reference base
                            #       >	      <	Reference skip (due to CIGAR “N”)
                            #       *	    */#	Deletion of the reference base (CIGAR “D”)
                            #
                            # Deleted bases are shown as “*” on both strands
                            # unless --reverse-del is used,
                            # in which case they are shown as “#” on the reverse strand.
                            #
                            # If there is an insertion after this read base,
                            # text matching “\+[0-9]+[ACGTNacgtn*#]+”:
                            #       a “+” character followed by an integer giving
                            #       the length of the insertion and then the inserted sequence.
                            # Pads are shown as “*” unless --reverse-del is used,
                            # in which case pads on the reverse strand will be shown as “#”.
                            #
                            # If there is a deletion after this read base,
                            # text matching “-[0-9]+[ACGTNacgtn]+”:
                            #       a “-” character followed by the deleted reference bases
                            # represented similarly.
                            # (Subsequent pileup lines will contain “*” for this read
                            # indicating the deleted bases.)
                            # 
                            # If this is the last position covered by the read,
                            # a “$” character.
                            # endregion

                            depth, pileup_data = fd.readlines()[line_number-1].split('\t')[3:5]
                            depth = int(depth)

                            r1_ref_count = pileup_data.count('.')
                            r2_ref_count = pileup_data.count(',')

                            r1_alt_count = pileup_data.count(alt.upper())
                            r2_alt_count = pileup_data.count(alt.lower())

                            (r1_ins_count,
                            r1_del_count,
                            r2_ins_count,
                            r2_del_count) = self.count_indels(pileup_data)

                            total_alt_count = (
                                r1_alt_count +
                                r2_alt_count +
                                r1_ins_count +
                                r1_del_count +
                                r2_ins_count +
                                r2_del_count)

                            return (
                                depth,
                                total_alt_count,
                                round((total_alt_count)/depth, 3))

                        self.logger.warning(
                            "Can't find position '%s' in mpileup data '%s'",
                            position, os.path.basename(self.mpileup_files[chromosome]))
                        return (-1, -1, -1)

            except (FileNotFoundError, ValueError):
                self.logger.critical(
                    "File '%s' not found or it is empty",
                    self.mpileup_files[chromosome])
                return (-1, -1, -1)

        else:
            msg = f"The mpileup file for chromosome {chromosome} doesn't exist."

            self.logger.critical(
                "%s You have to execute '%s.%s' at first",
                msg,
                self.__class__.__name__,
                self.perform.__func__.__name__)

            raise FileNotFoundError(msg)

    def perform(
        self,
        sample: SampleDataContainer,
        target_regions: list[tuple[str, str]],
        executor: Union[CommandExecutor, callable]
        ) -> list:
        """
            Executes the process of generating mpileup files for
                target regions and calculates coverage metrics.
            
            Args:
                sample (SampleDataContainer):
                    The sequencing data sample.
                target_regions (list of tuples):
                    List of regions as (region_name, out_name).
                executor (callable):
                    Function or command executor to run system commands.

            Returns:
                list:
                    Results containing coverage metrics for each region.
        """
        mpileup_data_list = self.generate_mpileup(
            sample=sample,
            regions=target_regions,
            executor=os.system)

        for file_path in mpileup_data_list:
            chromosome = file_path[-2:]
            self.mpileup_files[chromosome] = file_path

        if not os.path.exists(self.coords) or sample.sid not in self.coords:
            self.coords = os.path.join(sample.processing_path, sample.sid+".coords")
            touch(self.coords)

            try:
                cmd = ''

                match get_platform():
                    case 'linux' | 'freebsd' | 'macos':
                        cmd = ' '.join([
                            self.configurator.config['bedtools'], 'bamtobed',
                            '-i', sample.bam_filepath,
                            '|', os.path.join('/', 'bin', 'cut'), '-f1,2,3,5',
                            '|', 'uniq', '-u',
                            '>', self.coords])

                    case 'windows':
                        cmd = ' '.join([
                            self.configurator.config['bedtools'], 'bamtobed',
                            '-i', sample.bam_filepath,
                            '|', 'powershell', '-Command',
                            "\"ForEach-Object { $fields = $_ -split '`t';",
                            '"$($fields[0])`t$($fields[1])`t$($fields[2])`t$($fields[4])" }',
                            f'| Set-Content {self.coords}"'])

                    case _:
                        self.logger.warning(
                            "There is no any native way to build a comand for '%s'." \
                            "Please edit '%s' script to execute it properly",
                            self.configurator.config['bedtools'],
                            self.__module__)

                        sys.exit(os.EX_USAGE)

                execute(executor, cmd)

            except (
                SystemError,
                OSError,
                IOError,
                FileNotFoundError,
                PermissionError) as e:
                self.logger.critical(
                    "An error '%s' occured while performing '%s.%s'",
                    e,
                    self.__class__.__name__,
                    self.perform.__func__.__name__)
                raise e

        with open(self.coords, 'r', encoding='utf-8') as fd:
            for data in map(str.strip, fd.readlines()):
                if data.startswith('#') or data.startswith(';'):
                    continue
                chrom, start, end = data.split('\t')[:3]
                chrom = chrom.replace('chr', '')
                if chrom in self.mpileup_files:
                    mpileup = self.mpileup_files[chrom]
                    cov_value = round(
                        self.count_region_coverage(
                            mpileup, chrom, start, end
                            ), 3)

                    self.results.append(cov_value)
                else:
                    continue
        return self.results
