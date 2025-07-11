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
        def check_for_archive(ref_filepath: PathLike[AnyStr]) -> list[PathLike[AnyStr]]:
            """
                Checks if the given file path points to an archive file (e.g., ZIP, TAR, GZ).
                If so, extracts its contents and returns a list of absolute paths to the extracted files.

                The method performs the following:
                - Resolves the file path by checking for common archive extensions.
                - Logs the identified archive and initiates extraction.
                - Extracts archive contents and logs the list of extracted files.
                - Returns a list of absolute paths to the extracted files, or the original file path if no archive is found or an error occurs.

                Args:
                    ref_filepath (PathLike[AnyStr]): The path to the file to check.

                Returns:
                    list[PathLike[AnyStr]]: List of absolute paths to the extracted files if extraction occurs successfully; \
                                            otherwise, returns a list containing the absolute path of the original file.
            """
            try:
                archive_path = self.resolve_file_path_by_extensions(
                    os.path.splitext(ref_filepath)[0],
                    ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.gz']
                )
                self.logger.debug(f"The file '{archive_path}' identified as an archive. Execute '{archive_path}' extraction")
                
                archive_file_names = extract_archive(archive_path)
                files_count = len(archive_file_names)
                self.logger.debug(
                    f"Extraction has successfully done. "
                    f"Path{'' if files_count == 1 else 'es'} to extracted "
                    f"fil{ 'e' if files_count == 1 else 'es'}: "
                    f"{
                        archive_file_names[0] if files_count == 1 else
                        archive_file_names[0]+', '.join(archive_file_names[1:-2])+archive_file_names[-1]
                    }" 
                )

                return list(map(os.path.abspath, archive_file_names))

            except (FileNotFoundError, IOError): return None
            return os.path.abspath(ref_filepath)

        def select_reference_option(path_list: list[PathLike[AnyStr]]) -> PathLike[AnyStr]:
            self.logger.info(f"There were some files in the archive. Chose one to use as a reference file:")
            
            for i in range(len(path_list)): print(f"{i}) '{path_list[i]}'")
            
            ans = int(input())
            self.logger.debug(ans)

            if ans in range(1, len(path_list)): return path_list[ans]
            else:
                self.logger.critical(f"Incorrect value was given. Abort")
                exit(os.EX_SOFTWARE)

        if os.path.exists(ref_filepath):
            if os.path.isfile(ref_filepath):
                path_list = check_for_archive(ref_filepath)

                if path_list is None:
                    self.logger.info(f"Reference file '{ref_filepath}' was successfully found")
                    return ref_filepath
                else:
                    chosen_ref_filepath = path_list[0] if len(path_list) == 1 else select_reference_option(path_list)
                    self.logger.info(f"Reference file '{chosen_ref_filepath}' was successfully found")
                    return chosen_ref_filepath
            else:
                msg = f"Can't find reference file at path '{ref_filepath}'"
                self.logger.error(msg)
                raise FileNotFoundError(msg)
        else:
            ref_dirpath = os.path.abspath(ref_dirpath)
            self.logger.info(f"Start searching in references' root directory '{ref_dirpath}'")
            for root, dirs, files in os.walk(ref_dirpath, followlinks=True):
                if os.path.basename(ref_filepath) in files:
                    path_list = check_for_archive(os.path.join(root, ref_filepath))
                    
                    if path_list is None:
                        self.logger.info(f"Reference file '{ref_filepath}' was found at '{os.path.abspath(os.path.join(root, ref_filepath))}'")
                        return ref_filepath
                    else:
                        chosen_ref_filepath = path_list[0] if len(path_list) == 1 else select_reference_option(path_list)
                        self.logger.info(
                            f"Reference '{os.path.basename(ref_filepath)}' "
                            f"was found at '{os.path.abspath(os.path.join(root, chosen_ref_filepath))}'"
                        )
                        return chosen_ref_filepath
            raise FileNotFoundError(f"Root directory not exists or '{ref_dirpath}' is not a reference directory")

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

    @staticmethod
    def resolve_file_path_by_extensions(
        base_name: PathLike[AnyStr],
        extension_list: list[str]
    ) -> PathLike[AnyStr]:
        """
            Searches for the first existing file that matches the base name with any of the provided extensions.

            Args:
                base_name (PathLike[AnyStr]): The base file path without extension.
                extension_list (list[str]): A list of file extensions to check (including the dot, e.g., '.txt').

            Returns:
                PathLike[AnyStr]: The full path to the first existing file that matches the base name with one of the extensions.

            Raises:
                FileNotFoundError: If no file matching the base name with any of the provided extensions is found.
        """
        for path in [os.path.abspath(os.path.join(base_name + ext)) for ext in extension_list]:
            if os.path.exists(path): return path
        raise FileNotFoundError()
