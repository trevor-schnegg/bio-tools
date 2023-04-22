import argparse
import logging
import sys

import pandas as pd
from taxonomy.taxonomy import Taxonomy


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a ground truth read id to tax id mapping and computes precision, recall, accuracy, etc. "
                    "of a classifier")
    parser.add_argument(
        "-c",
        "--classifier-name",
        dest="classifier_name",
        default=None,
        help="The name of the classifier whose accuracy is being evaluated")
    parser.add_argument(
        "taxonomy",
        help="NCBI taxonomy directory")
    parser.add_argument(
        "ground_truth_readid2taxid",
        help="Tab separated read id to tax id of bwa-mem or other ground truth")
    parser.add_argument(
        "test_readid2taxid",
        help="Tab separated read id to tax id of the classifier")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read taxonomy
    logging.info(f"Reading taxonomy from directory {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Taxonomy read!")

    logging.info(f"Reading ground_truth_readid2taxid at {args.readid2taxid}")
    # Read both readid2taxids
    ground_truth_readid2taxid = pd.read_table(
        args.readid2taxid,
        names=["readid", "taxid"],
        dtype={
            'readid': 'string',
            'taxid': 'int'})
    test_readid2taxid = pd.read_table(
        args.readid2taxid,
        names=["readid", "taxid"],
        dtype={
            'readid': 'string',
            'taxid': 'int'})
    logging.info("Both readid2taxids read!")

    logging.info("Computing statistics")


if __name__ == '__main__':
    main()
