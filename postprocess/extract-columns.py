import argparse
import logging
import sys
from collections import defaultdict

import pandas as pd


def tab_separated_list(values) -> str:
    string = ""
    for idx, value in enumerate(values):
        # If this is CLARK, switch NA to 0
        if value == "NA":
            value = "0"

        if idx == 0:
            string += value
        else:
            string += ("\t" + value)
    return string


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a tsv of the input columns")
    parser.add_argument(
        "-c",
        "--clark",
        dest="clark",
        action="store_true",
        help="If the output is CLARK, we need to split on commas, not tabs")
    parser.add_argument(
        "-s",
        "--skip-header",
        dest="skip_header",
        action="store_true",
        help="Skip the first line of the input file")
    parser.add_argument("file", help="TSV file to extract columns from")
    parser.add_argument(
        "columns",
        type=str,
        help="Comma separated list of columns to output (0 indexed) "
             "(E.g. 4,6,1 will output 4<tab>6<tab>1)")
    args = parser.parse_args()
    columns = list(map(lambda x: int(x), args.columns.split(",")))
    # Override type inference
    types = {}
    for column in columns:
        types[column] = str

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read the TSV
    logging.info(f"Reading input table for columns {str(columns)}")
    input_table = pd.read_table(
        args.file,
        delimiter="," if args.clark else None,
        skiprows=1 if args.skip_header else None,
        header=None,
        dtype=object,
        usecols=columns)
    logging.info("Sorting table on first column")
    input_table.sort_values(columns[0], inplace=True)
    logging.info("Table read!")

    logging.info("Outputting desired columns")
    # Output the desired columns
    for line in input_table.iterrows():
        # line is a tuple of (row_number, {column: value})
        print(tab_separated_list(map(lambda x: line[1][x], columns)))
    logging.info("Done!")


if __name__ == '__main__':
    main()
