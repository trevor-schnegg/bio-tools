import argparse
import logging
import os
import sys

from multiprocessing.pool import Pool
from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy


def get_first_accession(fasta_file):
    return fasta_file, next(SeqIO.parse(fasta_file, 'fasta')).id


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Prints out a tax id to file mapping for the input reference directory")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=20,
        help="Number of threads to use")
    parser.add_argument(
        "abv",
        help="Directory containing fasta files for abv")
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of abv")
    parser.add_argument(
        "taxonomy",
        help="NCBI taxonomy directory")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read in accession2taxid
    accession2taxid = {}
    logging.info(
        f"Reading accession2taxid at {args.accession2taxid}")
    with open(args.accession2taxid, 'r') as accession2taxid_file:
        for line in accession2taxid_file:
            formatted_line = line.strip().split(' ')
            accession2taxid[formatted_line[0]] = formatted_line[-1]
    logging.info("Done reading accession2taxid!")

    # Read in taxonomy
    logging.info(f"Reading taxonomy from {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Done reading taxonomy!")

    logging.info(f"Looping through reference files in {args.abv}")
    with Pool(args.threads) as pool:
        reference_files = map(
            lambda x: os.path.realpath(
                os.path.join(
                    args.abv, x)), filter(
                lambda x: x.endswith('.fna') or x.endswith('.fasta'), os.listdir(
                    args.abv)))
        for fasta_path, first_accession in pool.imap(get_first_accession, reference_files):
            print(f"{accession2taxid[first_accession]} {fasta_path}")


if __name__ == '__main__':
    main()