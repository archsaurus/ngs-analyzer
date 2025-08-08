from . import *

class IPathValidator(Protocol):
    @abstractmethod
    def verify_path(
        self,
        path:
        PathLike[AnyStr],
        create_if_missing: bool=False
    ) -> bool: ...

class PathValidator(LoggerMixin, IPathValidator):
    def __init__(self, logger: logging.Logger=None):
        super().__init__(logger=logger)

    @staticmethod
    def verify_path(
        src: PathLike[AnyStr],
        create_if_missing: bool=False
    ) -> bool:
        """
            Checks the existence of the file or directory \
                at the given path src.
            If the path does not exist, creates \
                the necessary directories and the file.
            Args:
                src (PathLike[AnyStr]): \
                    The path to the file or directory to check or create.
                create_if_missing (bool): Whether to create the path \
                    if it doesn't exist. Defaults to False.
            Returns:
                bool: True if the path exists or was \
                    successfully created, otherwise False.
        """
        try:
            if not os.path.exists(src):
                src_dirname = os.path.dirname(src)

                if not os.path.exists(src_dirname):
                    if create_if_missing:
                        try:
                            os.makedirs(src_dirname, exist_ok=True)
                            try:
                                touch(src)
                                return True

                            except Exception: return False
                        
                        except Exception as e:
                            self.logger.critical(
                                f"A fatal error '{e.__repr__()}' occured "
                                f"at '{e.__traceback__.tb_frame}'")

                            return False
                else:
                    if create_if_missing:
                        try:
                            touch(src)
                            return True

                        except Exception as e:
                            self.logger.critical(
                                f"A fatal error '{e.__repr__()}' occured at "
                                f"'{e.__traceback__.tb_frame}'")

                            return False
            elif os.path.isfile(src): return True
            else: return False

        except OSError as e:
            self.logger.critical(
                f"Error creating directory structure: '{e}'")

            return False
