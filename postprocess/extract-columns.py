import argparse
import logging
import sys
from collections import defaultdict

import pandas as pd


def get_readid2taxid(filename):
    readid2taxid = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.strip().split('\t')
            readid2taxid[line[0]] = int(line[1])
    return readid2taxid


def tab_separated_list(values, krakenuniq_map) -> str:
    string = ""
    krakenuniq_map_orig = ""
    if krakenuniq_map is not None:
        krakenuniq_map_orig = get_readid2taxid(krakenuniq_map + ".orig")
        krakenuniq_map = dict(reversed(list(krakenuniq_map.items())))

    for idx, value in enumerate(values):
        # If this is CLARK, switch NA to 0
        if value == "NA":
            value = "0"

        # If this is krakenuniq, substitute the assigned tax id for the real one
        if krakenuniq_map is not None:
            try:
                value = int(value)
            except ValueError:
                # If the value isn't an integer, then it is a read id and it stays the same
                value = value
            else:
                value = str(krakenuniq_map_orig[krakenuniq_map[value]])

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
    parser.add_argument(
        "-u",
         "--krakenuniq",
        dest="krakenuniq_map",
        default=None,
        help="The seqid2taxid.map file provided by krakenuniq and the accession2taxid mapping for the dataset")
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
        dtype=types,
        na_values=None,
        keep_default_na=False,
        usecols=columns)
    # logging.info("Sorting table on first column")
    # input_table.sort_values(columns[0], inplace=True)
    # logging.info("Table read!")

    logging.info("Outputting desired columns")
    # Output the desired columns
    for line in input_table.iterrows():
        # line is a tuple of (row_number, {column: value})
        print(tab_separated_list(map(lambda x: line[1][x], columns), args.krakenuniq_map))
    logging.info("Done!")


if __name__ == '__main__':
    main()
