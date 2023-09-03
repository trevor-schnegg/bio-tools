import argparse
import logging
import sys
from functools import reduce

from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a fastq reads file and prints all the read lengths line by line")
    parser.add_argument(
        "fastq_file",
        help="The reads file")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    logging.info(f"Printing all sequence lengths from {args.fastq_file}")
    for record in SeqIO.parse(args.fastq_file, "fastq"):
        print(len(record.seq))
    logging.info("Done!")


if __name__ == '__main__':
    main()
