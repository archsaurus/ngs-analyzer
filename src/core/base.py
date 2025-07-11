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

def extract_archive(archive_filepath: PathLike[AnyStr]) -> PathLike[AnyStr]:
    archive_absolute_filepath = os.path.abspath(archive_filepath)
    
    if os.path.exists(archive_absolute_filepath) and os.path.isfile(archive_absolute_filepath):
        file_basename, ext = os.path.splitext(archive_absolute_filepath)
        base_dir = os.path.dirname(archive_absolute_filepath)
        match ext:
            case '.zip':
                import zipfile
                with zipfile.ZipFile(archive_absolute_filepath, 'r') as zf:
                    zf.extractall(base_dir)
                    return zf.namelist()
            case '.tar' | '.tar.gz' | '.tar.bz2' | '.tar.xz':
                import tarfile

                with tarfile.open(archive_absolute_filepath, f'r:{ext.split('.')[-1]}') as tf:
                    tf.extractall(base_dir)
                    return tf.getnames()
            case '.gz':
                import gzip
                with gzip.open(archive_absolute_filepath, 'rb') as gf:
                    try:
                        with open(file_basename, 'wb') as output:
                            while True:
                                # read input files in 64KB chunks to avoid high memory usage while handling large files
                                chunk = gf.read(1024 * 64)
                                if not chunk: break
                                output.write(chunk)
                            return gf.name
                    except Exception as e:
                        f"A fatal error '{e.__repr__()}' occured at '{e.__traceback__.tb_frame}'"

            case _: raise IOError(f"The program doesn't support decompression of '{ext}' files")
    else: raise FileNotFoundError
