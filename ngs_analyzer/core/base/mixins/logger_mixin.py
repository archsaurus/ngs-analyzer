import logging
import sys


class LoggerMixin:
    """Mixin class providing logging capabilities.

        Attributes:
            logger (logging.Logger):
                Custom logger instance.
    """

    def __init__(self, logger: logging.Logger = None):
        """Initializes the LoggerMixin with an optional logger.

        Args:
            logger (Optional[logging.Logger]):
                Custom logger instance.
        """
        self.logger = logger
        self.set_logger(logger)

    def set_logger(self, logger: logging.Logger = None) -> None:
        """Sets the logger instance.

        Args:
            logger (Optional[logging.Logger]):
                New logger to set.
        """
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)

            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            stdout_handler.setFormatter(
                logging.Formatter(
                    r'%(asctime)s - %(levelname)s - %(message)s'))

            self.logger.addHandler(stdout_handler)

        else:
            self.logger = logger
