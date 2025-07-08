from src.settings import *

class PatientDataContainer:
    def __init__(
        self,
        R1_source: PathLike[AnyStr],
        R2_source: PathLike[AnyStr]=None,
        id: int=0,
        processing_path: PathLike[AnyStr]=None,
        processing_logpath: PathLike[AnyStr]=None,
        report_path: PathLike[AnyStr]=None
    ):
        # TODO: Validate current patient data
        self.R1_source = R1_source
        self.R2_source = R2_source
        
        self.id = id
        
        self.processing_path = os.path.abspath(os.path.join(configurator.output_dir, f"patient_{self.id}")) if processing_path is None else processing_logpath
        self.processing_logpath = os.path.abspath(os.path.join(configurator.log_path, f"patient_{self.id}")) if processing_logpath is None else processing_logpath
        self.report_path = os.path.abspath(os.path.join(configurator.args.outputDir, f"patient_{self.id}", "report")) if report_path is None else report_path
