import gzip
import os
import tarfile
import zipfile
from os import PathLike
from typing import AnyStr


def extract_archive(archive_filepath: PathLike[AnyStr]) -> PathLike[AnyStr]:
    """Extract an archive file (zip, tar, gzip).

    Args:
        archive_filepath (PathLike[AnyStr]): Path to archive file.

    Returns:
        PathLike:
            List of extracted file names or extracted filename for gzip.

    Raises:
        FileNotFoundError: If the archive file does not exist.
        IOError: If the archive format is unsupported or extraction fails.
    """
    archive_absolute_filepath = os.path.abspath(archive_filepath)

    if os.path.exists(archive_absolute_filepath) and \
       os.path.isfile(archive_absolute_filepath):
        file_basename, ext = os.path.splitext(archive_absolute_filepath)
        base_dir = os.path.dirname(archive_absolute_filepath)
        match ext:
            case '.zip':
                with zipfile.ZipFile(archive_absolute_filepath, 'r') as zf:
                    zf.extractall(base_dir)
                    return zf.namelist()

            case '.tar' | '.tar.gz' | '.tar.bz2' | '.tar.xz':
                with tarfile.open(
                    archive_absolute_filepath,
                    f'r:{ext.split(".")[-1]}',
                ) as tf:
                    tf.extractall(base_dir)
                    return tf.getnames()

            case '.gz':
                with gzip.open(archive_absolute_filepath, 'rb') as gf:
                    try:
                        with open(file_basename, 'wb') as output:
                            while True:
                                # read input files in 64KB chunks to avoid
                                # high memory usage while handling large files
                                chunk = gf.read(1024 * 64)
                                if not chunk:
                                    break
                                output.write(chunk)
                            return gf.name

                    except (
                        OSError,
                        SystemError,
                        PermissionError,
                        IOError,
                    ) as e:
                        raise e

            case _:
                raise IOError(
                    "The program doesn't support decompression "
                    f"of '{ext}' files")

    else:
        raise FileNotFoundError
