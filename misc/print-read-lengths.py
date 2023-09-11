import argparse
import logging
import sys

from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a fasta reads file and prints all the read lengths line by line")
    parser.add_argument(
        "fasta_file",
        help="The reads file")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    length2count = {}
    longest_length = 0
    logging.info(f"Printing all sequence lengths from {args.fastq_file}")
    for record in SeqIO.parse(args.fasta_file, "fasta"):
        length = len(record.seq)
        if length > longest_length:
            longest_length = length
        if length in length2count:
            length2count[length] += 1
        else:
            length2count[length] = 1

    for i in range(longest_length + 1):
        if i in length2count:
            print(f"{str(i)}\t{str(length2count[i])}")
        else:
            print(f"{str(i)}\t0")

    logging.info("Done!")


if __name__ == '__main__':
    main()
