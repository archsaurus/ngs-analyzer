#!/bin/python
"""
    FAST(A|Q) Reads Merger

    This script consolidates paired-end FASTQ file
    from a specified directory by merging multiple files per sample
    if necessary, or copying single files directly.
    It identifies samples based on a provided pattern,
    and processes R1 and R2 read files separately.

    Usage:
        python script_name.py -i <input> -o <output> \
            -id <id_regex> -r1 <r1_pattern> -r2 <r2_pattern>

    Options:
        --path        Input directory containing FASTQ files.
        --outpath     Output directory for merged FASTQ files.
        --id_pattern  Regex pattern to extract sample IDs from filenames.
        --r1_pattern  Regex pattern for R1 read files.
        --r2_pattern  Regex pattern for R2 read files.

    Example:
        python3.13 read_merger.py \
        --path <workdir>/input_dir \
        --outpath <workdir>/output_dir \
        --id_pattern '<sample_base>_[\d]{4}_([^_]*){1,2}' \
        --r1_pattern '.*R1.*\.fastq\.gz' \
        --r2_pattern '.*R2.*\.fastq\.gz'

"""

# region Imports
import os
import sys
import re

from os import PathLike
from typing import AnyStr

import argparse
# endregion

def parse_args() -> argparse.Namespace:
    """
        Parses command-line arguments for input and output paths,
        and patterns.

        Returns:
            args:
                Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="FAST(A|Q) Reads Merger",
        description="Merges paired-end FASTQ files from a specified directory.")

    arguments = [
        {'name': ('--path', '-i'), 'kwargs': {
            'dest': 'path',
            'type': str,
            'required': True,
            'help': 'Input directory containing FASTQ files'}},
        {'name': ('--outpath', '-o'), 'kwargs': {
            'dest': 'outpath',
            'type': str,
            'required': True,
            'help': 'Output directory for merged files'}},
        {'name': ('--id_pattern', '-id'), 'kwargs': {
            'dest': 'id_pattern',
            'type': str,
            'required': True,
            'help': 'Regex pattern to identify sample IDs'}},
        {'name': ('--r1_pattern', '-r1'), 'kwargs': {
            'dest': 'r1_pattern',
            'type': str,
            'required': True,
            'help': 'Pattern for r1 reads'}},
        {'name': ('--r2_pattern', '-r2'), 'kwargs': {
            'dest': 'r2_pattern',
            'type': str,
            'required': True,
            'help': 'Pattern for r2 reads'}}
        ]

    for arg in arguments:
        parser.add_argument(*arg['name'], **arg['kwargs'])
    return parser.parse_args()

def merge_fastq(
    path: PathLike[AnyStr],
    outpath: PathLike[AnyStr],
    id_pattern: str=r"(?:russco_[\d]{4}_(?:ffpe_cr|leu))",
    r1_pattern: str=r"[^\s]*R1[^\s]*(?:\.fa(?:st(?:a|q)))(?:\.(?:gz|bz|bgz))?",
    r2_pattern: str=r"[^\s]*R2[^\s]*(?:\.fa(?:st(?:a|q)))(?:\.(?:gz|bz|bgz))?"
    ):
    """Merges R1 and R2 FASTQ files per sample based on provided patterns."""
    error_msg = "Wrong regexp pattern was given or there are no any " \
        "coincided with the pattern files in input directory.\n" \
        f"Input directory: {path}\nOutput directory: {outpath}" \
        f"ID pattern: {id_pattern}\n" \
        f"R1 pattern: {r1_pattern}\n" \
        f"R2 pattern: {r2_pattern}"

    dir_content = ' '.join(os.listdir(path))

    samples = set(re.findall(id_pattern, dir_content))

    try:
        for sample in samples:
            r1_cursor = re.compile(sample+r1_pattern)
            r2_cursor = re.compile(sample+r2_pattern)

            for cursor in [r1_cursor, r2_cursor]:
                files = [f"{sample}{file}"
                    for file in cursor.findall(dir_content)]
                if len(files) > 1:
                    cat_list = [f"{sample}_{file[file.index('R'):]}"
                        for file in files]

                    cmd = ' '.join([
                        'cat', ' '.join([os.path.join(
                            path, file) for file in files]),
                        '>',
                        os.path.abspath(os.path.join(
                            outpath,
                            f"{sample}_{'R1' if 'R1' in cat_list[0] else 'R2'}.fastq.gz"))
                        ])
                    os.system(cmd)

                elif len(files) == 1:
                    cmd = ' '.join([
                        'cp', os.path.join(path, files[0]), outpath])
                    os.system(cmd)

    except re.PatternError:
        print(error_msg)
        sys.exit(os.EX_USAGE)

if __name__ == '__main__':
    args = parse_args()

    if not os.path.exists(args.outpath):
        os.makedirs(os.path.abspath(args.outpath))

    merge_fastq(
        args.path,
        args.outpath,
        args.id_pattern,
        args.r1_pattern,
        args.r2_pattern)
