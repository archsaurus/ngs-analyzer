from . import *

class ILoggingConfigurator(Protocol):
    def set_logger(self, silet: bool=False) -> logging.Logger: ...

class LoggingConfigurator(ILoggingConfigurator):
    def __init__(
        self,
        path_validator: IPathValidator,
        log_path: PathLike[AnyStr]=os.curdir,
        args: argparse.Namespace=None
    ):
        self.args = args if args is not None else None
        self.log_path = log_path
        self.path_validator = path_validator

    def set_logger(self, silent: bool=False) -> logging.Logger:
        try:
            if not self.args is None: base_logpath = os.path.abspath(
                os.path.join(self.log_path, self.args.logFilename))
            else: base_logpath = os.path.abspath(os.path.join(
                self.log_path, 'default_analyzer.log'))

            if not self.path_validator.verify_path(
                base_logpath, create_if_missing=True):
                exit(os.EX_SOFTWARE)

            handlers=[logging.FileHandler(filename=base_logpath)]

            if not silent: handlers.append(
                logging.StreamHandler(stream=sys.stdout))

            logging.basicConfig(
                level=logging.INFO,
                format=r'%(asctime)s - %(levelname)s - %(message)s',
                handlers=handlers)

            configuration_logger = logging.getLogger()
            configuration_logger.propagate = False

            return configuration_logger

        except Exception as e:
            print(
                f"A fatal error '{e.__repr__()}' occured at "
                f"'{e.__traceback__.tb_frame}'", file=sys.stdout)

            exit(os.EX_SOFTWARE)
