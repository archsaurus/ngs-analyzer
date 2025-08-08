from src.core.base import *
from . import *

class PositionNotFoundError(Exception): pass

class AmpliconCoverageDataPreparator(LoggerMixin, IDataPreparator):
    def __init__(
        self,
        configurator: Configurator,
        filter_func: callable
    ):
        super().__init__(logger=configurator.logger)

        self.configurator = configurator
        self.config = self.configurator.parse_configuration(target_section='samtools')

        # a file with lines in format "chrom_number, region_start, region_end, depth"
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
        mp_files = []

        for region, out_name in regions:
            out_path = os.path.join(
                sample.processing_path, f"{sample.id}.{out_name}")

            cmd = ' '.join([
                self.configurator.config['samtools'], "mpileup",
                sample.bam_filepath,
                # skip bases with baseQ/BAQ smaller than value was given
                # '--min-BQ', self.config['min-bq'],
                '--no-BAQ' if 'no-BAQ' in self.config else '',
                '--max-depth', self.config['max-depth'],
                '--region', "chr"+region,
                '--count-orphans', # do not discard anomalous read pairs
                '--output', out_path])

            execute(executor, cmd)
            mp_files.append(out_path)

        return mp_files

    def count_region_coverage(
        self,
        mpileup: PathLike[AnyStr],
        chromosome: Union[int, str],
        start: Union[int, str],
        end: Union[int, str]
    ) -> float:
        try:
            start, end = int(start), int(end)
            if start > end: start, end = end, start

            chromosome = str(chromosome).upper()
            try:
                with open(mpileup, 'r') as fd:
                    coverages = []
                    last_position = start - 1

                    for line in fd:
                        chrom, position, _, depth = line.strip().split('\t')[:4]

                        position, depth = int(position), int(depth)

                        chrom = chrom.upper().replace('CHR', '')
                        if chromosome != chrom or start > position or 'X' in chrom: continue
                        elif end > 0 and position > end: break

                        if position > last_position + 1:
                            coverages.extend([0] * (position - last_position - 1))

                        coverages.append(depth)
                        last_position = position
                    if coverages:
                        if len(coverages) < end - start + 1:
                            coverages.extend([0] * (end - start + 1 - len(coverages)))

                        return self.filter_func(coverages)
                    return 0.0
            except FileNotFoundError as e:
                self.logger.warning(
                    f"There is no mpileup-file for chromosome {chromosome}")

                return 0.0

        except Exception as e:
            self.logger.critical(
                f"An error {str(e)} occured in "
                f"'{self.__class__.__name__}"
                f".{self.perform.__func__.__name__}'. Abort")
            raise e

    def count_variant_coverage(
        self,
        chromosome: Union[int, str],
        position: Union[int, str],
        ref: str,
        alt: str
    ) -> (int, int, float):
        chromosome = str(chromosome).replace('chr', '').strip()
        position = str(position)

        if chromosome in self.mpileup_files:
            try:
                with open(self.mpileup_files[chromosome], 'r') as fd:
                    for line in fd:
                        if position in line:
                            columns = line.split('\t')[3:5]
                            depth = int(columns[0])
                            alt_count = depth - columns[1].upper().count(ref)
                            return (depth, alt_count, round(alt_count/depth, 3))
                        else: continue

                        self.logger.warning(
                            f"Can't find position '{position}' in mpileup data "
                            f"'{os.path.basename(self.mpileup_files[chromosome])}'")

                        raise PositionNotFoundError(
                            f"There is no '{position}' position in "
                            f"'{self.mpileup_files[chromosome]}' file")
            except FileNotFoundError as e:
                return (-1, -1, -1)

        else:
            msg = f"The mpileup file for chromosome {chromosome} doesn't exist"

            self.logger.critical(
                f"{msg} You have to execute "
                f"{self.__class__.__name__}."
                f"{self.perform.__func__.__name__} at first")

            return (-1, -1, -1)
            #raise FileNotFoundError(msg)

    def perform(
        self,
        sample: SampleDataContainer,
        target_regions: list[tuple[str, str]],
        executor: Union[CommandExecutor, callable]
    ) -> list:
        mpileup_data_list = self.generate_mpileup(
            sample=sample,
            regions=target_regions,
            executor=os.system)

        for file_path in mpileup_data_list:
            chromosome = file_path[-2:]
            self.mpileup_files[chromosome] = file_path

        if False: #not os.path.exists(self.coords) or sample.id not in self.coords:
            self.coords = os.path.join(sample.processing_path, sample.id+".coords")
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
                            '>', self.coords
                            ])

                    case 'windows':
                        cmd = ' '.join([
                            self.configurator.config['bedtools'], 'bamtobed',
                            '-i', sample.bam_filepath,
                            '|', 'powershell', '-Command',
                            "\"ForEach-Object { $fields = $_ -split '`t';",
                            '"$($fields[0])`t$($fields[1])`t$($fields[2])`t$($fields[4])" }',
                            f'| Set-Content {self.coords}"'
                            ])

                    case _:
                        self.logger.warning(
                            f"There is no any native way to build a comand for "
                            f"'{self.configurator.config['bedtools']}'."
                            f"Please edit '{self.__module__}' script to execute it properly")

                        exit(os.EX_USAGE)

                execute(executor, cmd)

            except Exception as e:
                self.logger.critical("An error '{e}' occured while performing "
                f"'{self.__class__.__name__}"
                f".{self.perform.__func__.__name__}'")
                raise e

        with open(self.coords, 'r') as fd:
            for data in map(str.strip, fd.readlines()):
                chrom, start, end, depth = data.split('\t')
                chrom = chrom.replace('chr', '')
                if chrom in self.mpileup_files:
                    mpileup = self.mpileup_files[chrom]
                    cov_value = round(
                        self.count_region_coverage(
                            mpileup, chrom, start, end
                            ), 3)

                    self.results.append(cov_value)
                else: continue
        return self.results
