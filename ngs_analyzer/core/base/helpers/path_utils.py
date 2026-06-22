import os
import time
from os import PathLike
from pathlib import Path
from typing import AnyStr


def get_unique_path(
    parent_dir: PathLike[AnyStr] = Path(os.path.curdir)
) -> Path:
    """Produce a Path object with directory name based on timestamp."""
    default_outpath = Path(os.path.abspath(parent_dir))

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_outpath = default_outpath / f"output_{timestamp}"

    cnt = 1
    while unique_outpath.exists():
        unique_outpath = default_outpath / f"output_{timestamp}_{cnt}"
        cnt += 1

    os.makedirs(unique_outpath)

    return unique_outpath


def insert_processing_infix(
    infix_str: str,
    filename: PathLike[AnyStr]
) -> PathLike:
    """Inserts an infix string into a filename before its extension.

        Args:
            infix_str (str):
                String to insert.
            filename (PathLike[AnyStr]):
                Original filename.

        Returns:
            PathLike:
                Modified filename with infix inserted.
    """
    base, ext = os.path.splitext(filename)
    if ext in [".gz", ".zip"]:
        sub_base, sub_ext = os.path.splitext(base)
        return f"{sub_base}{infix_str}{sub_ext}{ext}"
    return f"{base}{infix_str}{ext}"
