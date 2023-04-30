import argparse
import logging
import sys

import pandas as pd
from Bio import SeqIO


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a tsv of accession to taxid based on a reference file")
    parser.add_argument(
        "accession2taxid",
        help="Entire accession2taxid from NCBI")
    parser.add_argument(
        "reference_fasta",
        help="The reference file in fasta format")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read the fasta file
    logging.info(f"Getting needed accessions from {args.reference_fasta}")
    needed_accessions = set()
    fasta_file = SeqIO.parse(args.reference_fasta, 'fasta')
    for record in fasta_file:
        needed_accessions.add(record.id)
    logging.info("Needed accessions obtained!")

    # Read through accession2taxid
    logging.info(f"Reading accession2taxid at {args.accession2taxid}, this may take awhile...")
    with open(args.accession2taxid, 'r') as accession2taxid:
        for line in accession2taxid:
            formatted_line = line.strip().split('\t')
            if formatted_line[1] in needed_accessions:
                print(f"{formatted_line[1]}\t{formatted_line[2]}")
    logging.info("Done!")


if __name__ == '__main__':
    main()
