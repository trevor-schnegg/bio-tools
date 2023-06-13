import argparse
import logging
import sys

from Bio import SeqIO


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Compares raw reads to basecalled signals from deepsimulator")
    parser.add_argument(
        "file1",
        help="First file (fasta or fastq)")
    parser.add_argument(
        "file2",
        help="Second file (fasta or fastq)"
    )
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')


if __name__ == '__main__':
    main()
