import argparse
import logging
import sys

from Bio import SeqIO


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Counts the number of base pairs in the input file"
    )
    parser.add_argument(
        "-f",
        "--fasta",
        dest="fasta",
        action="store_true",
        help="Option if the file is fasta (default is fastq)",
    )
    parser.add_argument("file", help="The fastq (or fasta) file")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Read the fasta file and count the base pairs
    logging.info(f"Looping through file at {args.file}")
    total_seq_len = 0
    if args.fasta:
        for record in SeqIO.parse(args.file, "fasta"):
            total_seq_len += len(record.seq)
    else:
        for record in SeqIO.parse(args.file, "fastq"):
            total_seq_len += len(record.seq)
    logging.info(f"total bases: {str(total_seq_len)}")
    logging.info("Done reading through reference!")


if __name__ == "__main__":
    main()
