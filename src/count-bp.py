import argparse
import logging
import sys

from Bio import SeqIO


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Counts the number of base pairs in the input file")
    parser.add_argument(
        "fastq_file",
        help="The fastq file")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read the fasta file and count the base pairs
    logging.info(f"Looping through file at {args.fastq_file}")
    total_seq_len = 0
    for record in SeqIO.parse(args.fastq_file, 'fastq'):
        total_seq_len += len(record.seq)
    logging.info(f"total bases: {str(total_seq_len)}")
    logging.info("Done reading through reference!")


if __name__ == '__main__':
    main()
