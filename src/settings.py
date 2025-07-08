from src.core.base import *

from src.core.configurator import Configurator
from src.core.dependency_handler import DependencyHandler

configurator = Configurator()

dependency_handler = DependencyHandler()
dependency_handler.set_logger(configurator.logger)
