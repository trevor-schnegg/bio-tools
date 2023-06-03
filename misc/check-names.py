import argparse
import logging
import os
import sys

from multiprocessing.pool import Pool
from Bio import SeqIO


def get_sequence_names(fasta_file):
    names = []
    for record in SeqIO.parse(fasta_file, 'fasta'):
        name = record.description.strip().split(" ")
        name = name[1] + " " + name[2]
        names.append(name)
    return names

def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a file of names and a reference file and checks if the names are in the reference")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=14,
        help="Number of threads to use")
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
    with Pool(args.threads) as pool:
        reference_files = map(lambda x: os.path.join(args.reference_dir, x), filter(lambda x: x.endswith('.fna'), os.listdir(args.reference_dir)))
        files_read = 0
        for result in pool.imap(get_sequence_names, reference_files):
            for name in result:
                reference_set.add(name)
            files_read += 1
            if files_read % 100 == 0:
                logging.debug(f"{files_read} files read")
    logging.info("Done reading through reference!")

    for name in names:
        if name in reference_set:
            print(f"{name} was found")


if __name__ == '__main__':
    main()
