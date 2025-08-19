"""
    This script aggregates individual sample reports
    into a single consolidated table.

    Usage:
        python script_name.py \
            --input <input_directory> \
            --output <output_directory>

    Description:
        The script takes as input a directory containing per-sample report
        files in Excel format.
        It reads all '.xlsx' files from the specified output directory,
        concatenates their data into one combined DataFrame, and saves
        the result as 'report.xlsx' in the same output directory.

    Arguments:
        --input / -i: Path to the directory containing per-sample reports.
        --output / -o: Directory for the output consolidated report.

    Note:
        - Ensure that the specified output directory contains \
        the report files in '.xlsx' format.
        - The script uses pandas for reading \
        and concatenating Excel files.

"""

import argparse
import os

import pandas

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        'This script agregate per sample processed reports to one table')

    arguments = [
        {'name': ('--input', '-i'), 'kwargs': {
            'dest': 'inputDir',
            'type': str,
            'help': 'Path to directory, containing per sample reports',
            'required':  True}},
        {'name': ('--output', '-o'), 'kwargs': {
            'dest': 'outputDir',
            'type': str,
            'help': 'directory for output',
            'required': True}}
        ]

    for arg in arguments:
        parser.add_argument(*arg['name'], **arg['kwargs'])
    args = parser.parse_args()

    file_list = [os.path.join(
        args.outputDir, filepath) for filepath in os.listdir(
            args.outputDir) if filepath.endswith('xlsx')]


    dfs = [pandas.read_excel(file_list[0]),]

    for file in file_list[1:]:
        df = pandas.read_excel(file, header=0)
        dfs.append(df)

    merged_df = pandas.concat(dfs, ignore_index=True)

    merged_df.to_excel(os.path.join(
        args.outputDir, 'report.xlsx'), index=False)
