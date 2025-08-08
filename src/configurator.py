from src.core.base import *
from src.core.configurator import *

class Configurator(metaclass=SingletonMeta):
    def __init__(
        self,
        args: argparse.Namespace = None,
        config_path: PathLike[AnyStr] = None,
        log_path: PathLike[AnyStr] = None,
        output_dir: PathLike[AnyStr] = None
    ):
        self.log_path, self.logger = self._setup_logger(
            log_path or 'default.log')

        if args is None: args = self._parse_args()
        self.args = args


        self.output_dir = self._setup_output_directory(
            output_dir or args.outputDir)

        self.config = self._load_configuration(
            config_path or 'config.ini')

    def _parse_args(self) -> argparse.Namespace:
        parser = ArgumentParser()
        return parser.parse()

    def _setup_logger(
        self,
        log_filename: PathLike[AnyStr]
    ) -> (PathLike[AnyStr], logging.Logger):
        logger = LoggingConfigurator(path_validator=PathValidator())
        return (
            os.path.abspath(log_filename),
            logger.set_logger(silent=False))

    def _setup_output_directory(
        self,
        output_dir: PathLike[AnyStr]
    ) -> PathLike[AnyStr]:
        """
            Get the output directory path and validate it \
                for existing as a directory.
        """
        output_dir = os.path.abspath(os.path.normpath(output_dir))

        if os.path.exists(output_dir): # Create output directory
            if not os.path.isdir(output_dir): os.mkdir(output_dir)
            else:
                msg = f"Directory '{output_dir}' already exists"
                self.logger.warning(msg)
                match input(
                    f"Do you want to use existing directory '{output_dir}'"
                    f" as the current output directory [y/n]: ").lower():
                    case 'n': exit(os.EX_OK)
                    case  _ : pass
        else: os.mkdir(output_dir)

        self.logger.info(f"Use '{output_dir}' directory as output")
        return output_dir

    def _load_configuration(self, config_path: PathLike[AnyStr]) -> dict:
        config_loader = ConfigLoader()
        return config_loader.load(target_section='Pathes')

    def parse_configuration(
        self,
        base_config_filepath: PathLike[AnyStr]=os.path.join(
            os.path.curdir, 'src', 'conf', 'config.ini'),
        target_section: AnyStr='Pathes'
    ) -> dict:
        return ConfigLoader().load(base_config_filepath, target_section)
