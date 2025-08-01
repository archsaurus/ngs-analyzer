from . import *

class SampleDataContainer:
    def __init__(
        self,
        R1_source: PathLike[AnyStr],
        R2_source: PathLike[AnyStr]=None,
        id: str='1',
        processing_path: PathLike[AnyStr]=None,
        processing_logpath: PathLike[AnyStr]=None,
        bam_filepath: Optional[PathLike[AnyStr]]=None,
        vcf_filepath: Optional[PathLike[AnyStr]]=None,
        report_path: PathLike[AnyStr]=None
    ):
        # TODO: Validate current patient data
        self.R1_source = R1_source
        self.R2_source = R2_source

        self.id = id

        self.processing_path = os.path.abspath(os.path.join(os.path.curdir, 'logs', f"patient_{self.id}")) if processing_path is None else processing_logpath
        self.processing_logpath = os.path.abspath(os.path.join(os.path.curdir, f"patient_{self.id}")) if processing_logpath is None else processing_logpath
        self.report_path = os.path.abspath(os.path.join(os.path.curdir, f"patient_{self.id}", "report")) if report_path is None else report_path

        self.bam_filepath = bam_filepath
        self.vcf_filepath = vcf_filepath

    def __str__(self): return "{"+f"id: '{self.id}', r1: '{self.R1_source}', r2: '{self.R2_source}'"+"}"

    def __repr__(self):
        return f"{self.__class__}({self.R1_source}, {self.R2_source}, {self.id}, {self.processing_path}, {self.processing_logpath}, {self.report_path})"
