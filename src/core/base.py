import logging, argparse, configparser, subprocess
import os, sys, re
from os import PathLike

from importlib.util import find_spec
from types import FunctionType
from typing import AnyStr

class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances: cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

def touch(path: PathLike[AnyStr]) -> None:
	with open(path, 'a'): os.utime(path, None)

def insert_processing_infix(infix_str: str, filename: PathLike[AnyStr]) -> PathLike:
    base, ext = os.path.splitext(filename)
    return f"{base}{infix_str}{ext}"
