import argparse
import logging
import os
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
        "reference_dir",
        help="The reference directory with fasta files")
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
    logging.info(f"Looping through reference files in {args.reference_dir}")
    reference_set = set()
    for file in os.listdir(args.reference_dir):
        if file.endswith('.fna'):
            fasta_file = SeqIO.parse(os.path.join(args.reference_dir, file), 'fasta')
            for record in fasta_file:
                name = record.description.strip().split(" ")
                name = name[1] + " " + name[2]
                if name == "Saccharomyces cerevisiae":
                    print(record)
                reference_set.add(name)
    logging.info("Done reading through reference!")

    for name in names:
        if name in reference_set:
            print(f"{name} was found")


if __name__ == '__main__':
    main()
