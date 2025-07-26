from src.core.base import *

class IDemultiplexorAdapter(Protocol):
    def demultiplex(self): ...
