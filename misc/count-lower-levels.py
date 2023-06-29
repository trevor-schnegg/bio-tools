import argparse
import logging
import os
import sys

from multiprocessing.pool import Pool
from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy


def get_accessions(fasta_file):
    accessions = []
    for record in SeqIO.parse(fasta_file, 'fasta'):
        accessions.append(record.id)
    return accessions


def get_first_accession(fasta_file):
    return next(SeqIO.parse(fasta_file, 'fasta')).id


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a file of names and a reference file and checks if the names are in the reference")
    parser.add_argument(
        "-r",
        "--rank",
        type=str,
        default="species",
        help="Taxonomic rank to count at"
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=14,
        help="Number of threads to use")
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of reference file")
    parser.add_argument(
        "reference_dir",
        help="The reference directory with fasta files")
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
            accession2taxid[formatted_line[0]] = formatted_line[4]
    logging.info("Done reading accession2taxid!")

    # Read in taxonomy
    logging.info(f"Reading taxonomy from {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Done reading taxonomy!")

    # Read the fasta file
    logging.info(f"Looping through reference files in {args.reference_dir}")
    parent_to_count = {}
    with Pool(args.threads) as pool:
        reference_files = map(
            lambda x: os.path.join(
                args.reference_dir, x), filter(
                lambda x: x.endswith('.fna'), os.listdir(
                    args.reference_dir)))
        files_read = 0
        for accession in pool.imap(get_first_accession, reference_files):
            species_parent = taxonomy.parent(
                accession2taxid[accession], args.rank)
            print(species_parent)
            if species_parent is not None:
                if species_parent in parent_to_count:
                    parent_to_count[species_parent] += 1
                else:
                    parent_to_count[species_parent] = 1
            files_read += 1
            if files_read % 1000 == 0:
                logging.debug(f"{files_read} files processed")
    logging.info("Done reading through reference!")
    all_counts = []
    for parent, count in parent_to_count.items():
        all_counts.append((count, parent))
    for (
            count,
            parent) in sorted(
            all_counts,
            key=lambda x: x[0],
            reverse=True):
        print(f"{parent.id}\t{count}")


if __name__ == '__main__':
    main()
