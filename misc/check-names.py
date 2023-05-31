import argparse
import logging
import sys

from Bio import SeqIO


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a file of names and a reference file and checks if the names are in the reference")
    parser.add_argument(
        "names_file",
        help="The file of names to check")
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

    # Read the names file to get the names
    logging.info(f"Getting names from {args.names_file}")
    names = set()
    with open(args.names_file, 'r') as f:
        for line in f.readlines():
            line = line.strip().split("_")
            name = line[0] + " " + line[1]
            names.add(name)

    # Read the fasta file
    logging.info(f"Looping through reference file at {args.reference_fasta}")
    reference_set = set()
    fasta_file = SeqIO.parse(args.reference_fasta, 'fasta')
    for record in fasta_file:
        name = record.description.strip().split(" ")
        name = name[1] + " " + name[2]
        reference_set.add(name)
    logging.info("Done reading through reference!")

    for name in names:
        if name in reference_set:
            print(f"{name} was found")

    # Read through accession2taxid


if __name__ == '__main__':
    main()
