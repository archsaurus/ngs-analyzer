from . import *

class ISampleDataFactory(Protocol):
    def parse_sample_data(
        self,
        path: PathLike[AnyStr],
        sample_id: AnyStr
    ) -> SampleDataContainer: ...

class SampleDataFactory(LoggerMixin, ISampleDataFactory):
    def __init__(self, logger: logging.Logger=None):
        super().__init__()

    def parse_sample_data(
        self, path:
        PathLike[AnyStr],
        sample_id: AnyStr
    ) -> SampleDataContainer:
        regexp_filter = re.compile(rf"^.*{sample_id}.*")
        sample_reads_source_pathes = filter(
            regexp_filter.match, os.listdir(path))

        sample_r1_path, sample_r2_path = None, None
        for read in sample_reads_source_pathes:
            if 'R1' in read: sample_r1_path = read; continue
            if 'R2' in read: sample_r2_path = read; continue

        if all((
            sample_r1_path is not None,
            sample_r2_path is not None)):
            sample_data = SampleDataContainer(
                id=sample_id,
                R1_source=os.path.join(path, sample_r1_path),
                R2_source=os.path.join(path, sample_r2_path))

            return sample_data

        else:
            self.logger.critical(
                f"Can't find {'R1' if sample_r1_path is None else 'R2'} "
                f"file for sample '{sample_id.strip()}'")

            return None
