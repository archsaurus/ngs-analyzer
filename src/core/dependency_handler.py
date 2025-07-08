from src.core.base import *
class DependencyHandler(metaclass=SingletonMeta):
    def __init__(self, logger: logging.Logger=None):
        if logger is None: self.logger = logging.getLogger(name=self.__class__.__name__)
        else: self.logger = logger
        
    def set_logger(self, new_logger: logging.Logger=None) -> None:
        if self.logger is None: raise RuntimeError(f"Current '{self.__class__.__name__}' logger is not set")
        if new_logger is None: raise RuntimeError("New '{self.__class__.__name__}' logger must be provided")
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        self.logger = new_logger

    def check_reference(self, ref_filepath: PathLike[AnyStr], ref_dirpath: PathLike[AnyStr]=os.path.curdir) -> PathLike[AnyStr]:
        """
            Check that file or archive with reference sequence exists.
            If there is only an archive, extract it to the current reference directory.

            Returns path to reference file if it exists or raise FileNotFoundError otherwise.
        """
        # TODO: Нужно добавить обработку случая, когда референс - архив 
        if os.path.exists(ref_filepath):
            if os.path.isfile(ref_filepath):
                msg = f"Reference file '{ref_filepath}' was successfully found"
                self.logger.info(msg)
                return os.path.abspath(ref_filepath)
            else:
                msg = f"Can't find reference file at path '{ref_filepath}'"
                self.logger.error(msg)
                raise FileNotFoundError(msg)
        else:
            ref_rootpath = os.path.abspath(ref_dirpath)
            self.logger.info(f"Start searching in references' root directory '{ref_rootpath}'")
            for root, dirs, files in os.walk(ref_rootpath):
                if os.path.basename(ref_filepath) in files:
                    self.logger.info(f"Reference file '{ref_filepath}' was found at '{os.path.abspath(os.path.join(root, ref_filepath))}'")
                    return os.path.abspath(os.path.join(root, ref_filepath))
            raise FileNotFoundError(f"Root directory not exists or '{ref_rootpath}' is not a reference directory")

    @staticmethod
    def is_module_loaded(module_name: AnyStr) -> bool:
        return False if isinstance(find_spec(module_name), type(None)) else True

    @staticmethod
    def try_to_install_module(module_name: AnyStr) -> bool:
        if not is_module_loaded(module_name):
            return True if os.system(f'pip install {module_name}') == os.EX_OK else False

    @staticmethod
    def fetch_dependency(module_name: AnyStr) -> None:
        """Tries to fetch depended module from pip distro. In case of failure calls exit function with suggested error code"""
        self.logger.warning(f"Can't import '{module_name}' module. Is it installed with current interpreter?")
        ans = input(f"Can't import '{module_name}' module. Do you want to try to fetch it from pip distro [y/n]: ")
        match ans.lower():
            case 'y':
                if try_to_install_module(module_name): self.logger.info(f"Module '{module_name}' has successfully installed")
                else:
                    self.logger.critical(f"The module '{module_name}' neither found nor installed. Abort")
                    sys.exit(os.EX_SOFTWARE)
            case 'n': sys.exit(os.EX_OK)
            case _:
                self.logger.critical(f"Unrecognized command '{ans}' was given. Abort")
                sys.exit(os.EX_USAGE)

    @staticmethod
    def verify_path(src: str) -> bool:
        """
            Checks the existence of the file or directory at the given path src.
            If the path does not exist, creates the necessary directories and the file.
            Args:
                src (str): The path to the file or directory to check or create.
            Returns:
                bool: True if the path exists or was successfully created, otherwise False.
        """
        if not os.path.exists(src):
            src_dirname = os.path.dirname(src)
            if src_dirname and not os.path.exists(src_dirname):
                try: os.makedirs(src_dirname, exist_ok=True)
                except Exception as e:
                    msg = f"A fatal error '{e.__repr__()}' occured at '{e.__traceback__.tb_frame}'"
                    try:
                        self.logger.critical(msg)
                    except Exception:
                        print(msg, filename=sys.stderr)
                        return False
            try: touch(src)
            except Exception: return False
        return True    
