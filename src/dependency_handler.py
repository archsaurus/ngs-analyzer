"""
    This module provides the DependencyHandler class, which is responsible
    for managing dependencies, checking the existence of reference files
    or archives, extracting archives, verifying module installation,
    attempting to install missing modules via pip,
    and verifying or creating paths.

    Classes:
        - DependencyHandler:
            Singleton class to handle dependencies and reference files.

    Functions:
        - Various static methods for module loading, installation
         path verification, and file extension resolution.

    Usage:
        Instantiate the DependencyHandler singleton to
        perform dependency management tasks, such as checking reference files,
        installing modules, and verifying paths.
"""

# region Imports
import os
import sys
import logging

from os import PathLike
from typing import Optional, AnyStr

from importlib.util import find_spec

from src.core.base import SingletonMeta
from src.core.base import extract_archive
from src.core.base import touch
# endregion

class DependencyHandler(metaclass=SingletonMeta):
    """
        Singleton class to manage dependencies and reference files.

        Provides methods to set loggers, check and resolve
        reference files (including archives), verify and install modules,
        and verify or create filesystem paths.
    """
    def __init__(self, logger: logging.Logger=None):
        self.logger = logger or logging.getLogger(
            name=self.__class__.__name__)

    def set_logger(
        self,
        new_logger: logging.Logger
        ) -> None:
        """
            Sets a new logger for the handler, replacing the current one.

            Args:
                new_logger (logging.Logger):
                    The new logger to set.

            Raises:
                RuntimeError:
                    If the current logger is not set
                    or if the new logger is None.
        """
        if self.logger is None:
            raise RuntimeError(
                f"Current '{self.__class__.__name__}' logger is not set")

        if new_logger is None:
            raise RuntimeError(
                "New '{self.__class__.__name__}' logger must be provided")

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        self.logger = new_logger

    def check_reference(
        self,
        ref_filepath: PathLike[AnyStr],
        ref_dirpath: PathLike[AnyStr]=os.path.curdir
        ) -> PathLike[AnyStr]:
        """
            Check that file or archive with reference sequence exists.
            If there is only an archive, extract it to the current
            reference directory.

            Returns path to reference file if it exists
            or raise FileNotFoundError otherwise.
        """
        def check_for_archive(
            ref_filepath: PathLike[AnyStr],
            ) -> list[PathLike[AnyStr]]:
            """
                Checks if the given file path points to an archive
                file (e.g., ZIP, TAR, GZ).

                If so, extracts its contents and returns a list
                of absolute paths to the extracted files.

                The method performs the following:
                    - Resolves the file path by checking
                    for common archive extensions.
                    - Logs the identified archive and initiates extraction.
                    - Extracts archive contents and logs
                    the list of extracted files.
                    - Returns a list of absolute paths to the extracted files,
                    or the original file path if no archive is found
                    or an error occurs.

                Args:
                    ref_filepath (PathLike[AnyStr]):
                        The path to the file to check.

                Returns:
                    list[PathLike[AnyStr]]:
                        List of absolute paths to the extracted files
                        if extraction occurs successfully; otherwise,
                        returns a list containing the absolute path
                        of the original file.
            """
            try:
                archive_path = self.resolve_file_path_by_extensions(
                    os.path.splitext(ref_filepath)[0],
                    ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.gz']
                )

                self.logger.debug(
                    "The file '%s' identified as an archive. Execute '%s' extraction",
                    archive_path, archive_path)

                archive_file_names = extract_archive(archive_path)
                files_count = len(archive_file_names)

                ending = '' if files_count == 1 else 'es'

                self.logger.debug(
                    "Extraction has successfully done. "
                    "Path%s to extracted fil%s: ",
                    ending, 'e'+ending[-1])
                self.logger.debug(
                    f"{archive_file_names[0] if files_count == 1 else \
                        archive_file_names[0]+', '.join( \
                            archive_file_names[1:-2])+archive_file_names[-1] \
                    }")

                return list(map(
                    os.path.abspath, archive_file_names))

            except (FileNotFoundError, IOError):
                return None
            return os.path.abspath(ref_filepath)

        def select_reference_option(
            path_list: list[PathLike[AnyStr]],
            ) -> PathLike[AnyStr]:
            """
                Prompts the user to select a reference file from a list.

                Args:
                    path_list (list[PathLike[AnyStr]]):
                        List of candidate files.

                Returns:
                    PathLike[AnyStr]:
                        The selected reference file path.
            """
            self.logger.info(
                "There were some files in the archive. "
                "Chose one to use as a reference file:")

            for index, path in enumerate(path_list):
                print(f"{index}) '{path}'")

            ans = int(input())
            self.logger.debug(ans)

            if ans in range(len(path_list)):
                return path_list[ans]

            self.logger.critical("Incorrect value was given. Abort")
            sys.exit(os.EX_USAGE)

        if os.path.exists(ref_filepath):
            if os.path.isfile(ref_filepath):
                path_list = check_for_archive(ref_filepath)

                if path_list is None:
                    self.logger.info(
                        "Reference file '%s' was successfully found",
                        ref_filepath)

                    return ref_filepath

                if len(path_list) == 1:
                    chosen_ref_filepath = path_list[0]
                else:
                    chosen_ref_filepath = select_reference_option(path_list)

                self.logger.info(
                    "Reference file '%s' was successfully found",
                    chosen_ref_filepath)

                return chosen_ref_filepath

            msg = f"Can't find reference file at path '{ref_filepath}'"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        ref_dirpath = os.path.abspath(ref_dirpath)
        self.logger.info(
            "Start searching in references' root directory '%s'",
            ref_dirpath)

        for root, _, files in os.walk(ref_dirpath, followlinks=True):
            if os.path.basename(ref_filepath) in files:
                path_list = check_for_archive(
                    os.path.join(root, ref_filepath))

                if path_list is None:
                    self.logger.info(
                        "Reference file '%s' was found at '%s'",
                        ref_filepath,
                        os.path.abspath(os.path.join(root, ref_filepath)))

                    return ref_filepath

                if len(path_list) == 1:
                    chosen_ref_filepath = path_list[0]
                else:
                    chosen_ref_filepath = select_reference_option(path_list)

                self.logger.info(
                    "Reference '%s' was found at '%s'",
                    os.path.basename(ref_filepath),
                    os.path.abspath(os.path.join(root, chosen_ref_filepath)))

                return chosen_ref_filepath

        raise FileNotFoundError(
            f"Root directory not exists or '{ref_dirpath}' "
            "is not a reference directory")

    @staticmethod
    def is_module_loaded(module_name: AnyStr) -> bool:
        r"""
            Checks if a module is loaded in the current environment.

            Args:
                module_name (str):
                    Name of the module to check.

            Returns:
                bool:
                    True if the module is loaded, False otherwise.
        """
        return bool(find_spec(module_name))

    @staticmethod
    def try_to_install_module(
        module_name: AnyStr,
        logger: Optional[logging.Logger]=None
        ) -> bool:
        """
            Attempts to install a module via pip.

            Args:
                module_name (str):
                    Name of the module to install.

            Returns:
                bool:
                    True if installation succeeded, False otherwise.
        """
        if not logger:
            logger = logging.getLogger(__name__)

        if not DependencyHandler.is_module_loaded(module_name):
            try:
                if os.system(f'pip install {module_name}') == os.EX_OK:
                    logger.info(
                        "The module '%s' has been successfully installed",
                        module_name)
                    return True

                logger.warning(
                    "The module '%s' has not been installed",
                    module_name)
                return False
            except (OSError, SystemError, SystemExit) as e:
                logger.critical(
                    "A critical error '%s' occured at '%s'",
                    repr(e), e.__traceback__.tb_frame)
                raise e

        logger.info("The module '%s' is currently installed", module_name)
        return True

    @staticmethod
    def fetch_dependency(
        module_name: AnyStr,
        logger: Optional[logging.Logger]=None
        ) -> None:
        """
            Attempts to fetch a dependency module from pip,
            prompting the user if needed.

            Args:
                module_name (str):
                    Name of the module to fetch.

            Exits:
                - Exits with code os.EX_SOFTWARE if installation fails.
                - Exits with code os.EX_OK if user chooses not to install.
                - Exits with code os.EX_USAGE if command is unrecognized.
        """
        if not logger:
            logger = logging.getLogger(__name__)
        logger.warning(
            "Can't import '%s' module. Is it installed with current interpreter?",
            module_name)

        ans = input(
            f"Can't import '{module_name}' module. "
            "Do you want to try to fetch it from pip distro [y/n]: ")
        match ans.lower():
            case 'y':
                if not DependencyHandler.try_to_install_module(module_name):
                    logger.critical(
                        "The module '%s' neither found nor installed. Abort",
                        module_name)
                    sys.exit(os.EX_SOFTWARE)

                logger.info(
                    "Module '%s' has successfully installed",
                    module_name)

            case 'n':
                sys.exit(os.EX_OK)
            case _:
                logger.critical(
                    "Unrecognized command '%s' was given. Abort", ans)

                sys.exit(os.EX_USAGE)

    @staticmethod
    def verify_path(
        src: str,
        logger: Optional[logging.Logger]=None
        ) -> bool:
        """
            Checks the existence of the file
            or directory at the given path src.

            If the path does not exist,
            creates the necessary directories and the file.

            Args:
                src (str):
                    The path to the file or directory to check or create.
            Returns:
                bool:
                    True if the path exists or was successfully created,
                    otherwise False.
        """
        if not logger:
            logger = logging.getLogger(__name__)

        if not os.path.exists(src):
            src_dirname = os.path.dirname(src)
            if src_dirname and not os.path.exists(src_dirname):
                try:
                    os.makedirs(src_dirname, exist_ok=True)
                except (IOError, SystemError, OSError) as e:
                    logger.critical(
                        "A fatal error '%s' occured at '%s'",
                        repr(e), e.__traceback__.tb_frame)
                    return False
            try:
                touch(src)
            except (FileNotFoundError, IOError, SyntaxError):
                logger.critical(
                    "A fatal error '%s' occured at '%s'",
                    repr(e), e.__traceback__.tb_frame)
                return False

        return True

    @staticmethod
    def resolve_file_path_by_extensions(
        base_name: PathLike[AnyStr],
        extension_list: list[str]
        ) -> PathLike[AnyStr]:
        """
            Searches for the first existing file that matches
                the base name with any of the provided extensions.

            Args:
                base_name (PathLike[AnyStr]):
                    The base file path without extension.
                extension_list (list[str]):
                    A list of file extensions to check
                        (including the dot, e.g., '.txt').

            Returns:
                PathLike[AnyStr]:
                    The full path to the first existing file
                        that matches the base name with one of the extensions.

            Raises:
                FileNotFoundError:
                    If no file matching the base name
                        with any of the provided extensions is found.
        """
        for path in [os.path.abspath(os.path.join(
            base_name + ext)) for ext in extension_list]:
            if os.path.exists(path):
                return path
        raise FileNotFoundError()
