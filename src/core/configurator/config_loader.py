from . import *

class IConfigLoader(Protocol):
    def load(): ...

class ConfigLoader(LoggerMixin, IConfigLoader):
    def __init__(self, logger: Optional[logging.Logger]=None):
        super().__init__(logger)

    def load(
        self,
        base_config_filepath: PathLike[AnyStr]=os.path.join(os.path.curdir, 'src', 'conf', 'config.ini'),
        target_section: AnyStr='Pathes'
    ) -> dict:
        if os.path.exists(base_config_filepath) and os.path.isfile(base_config_filepath):
            conf = configparser.ConfigParser(inline_comment_prefixes=[';', '#'], comment_prefixes=[';', '#'])
            conf.read(os.path.join(base_config_filepath))

            config_dict = {'target_section': target_section}
            if target_section in conf:
                for path_value in conf[target_section]: config_dict[path_value] = conf[target_section][path_value]
            else: raise ConfigurationError(f"Can't parse configuration file under path '{base_config_filepath}'. See the project config documentation")
            return config_dict
        else:
            self.logger.critical(msg=f"Can't find configuration file under path '{base_config_filepath}'")
            raise FileNotFoundError()
