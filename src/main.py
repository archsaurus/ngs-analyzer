from src.core.base import *
from src.core.analyzer import Analyzer
from src.settings import dependency_handler, configurator

if __name__ == '__main__':
    brca1_analyzer = Analyzer()
    brca1_analyzer.analyze()