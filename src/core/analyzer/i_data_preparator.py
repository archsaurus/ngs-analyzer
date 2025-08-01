from . import *

class IDataPreparator(Protocol):
    def perform(self): ...
