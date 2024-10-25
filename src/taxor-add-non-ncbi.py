import argparse
import logging
import os
import sys

from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy
from lib.lib import load_accession2taxid


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="")
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of reference file")
    parser.add_argument(
        "reference_directory",
        help="Directory containing reference fasta files")
#    parser.add_argument(
#        "taxonomy",
#        help="NCBI taxonomy directory")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

#    # Read taxonomy
#    logging.info(f"Reading taxonomy from directory {args.taxonomy}")
#    taxonomy = Taxonomy.from_ncbi(args.taxonomy)

    # Read in accession2taxid
    logging.info(
        f"Reading accession2taxid at {args.accession2taxid}")
    accession2taxid = load_accession2taxid(args.accession2taxid)

    logging.info(f"Collecting reference files from: {args.reference_directory}")
    ref_files = map(
        lambda x: os.path.realpath(
            os.path.join(
                args.reference_directory, x)), filter(
            lambda y: y.endswith('.fna') or y.endswith('.fasta'), os.listdir(
                args.reference_directory)))

    logging.info("Printing taxor reference strings")
    for file in ref_files:
        file_name_with_extension = os.path.basename(file)
        taxid = accession2taxid[next(SeqIO.parse(file, 'fasta')).id.split(".")[0]]
        assembly_version = ""
        if "_" in file_name_with_extension:
            file_split = file_name_with_extension.split(".")
            assembly_version = file_split[0] + file_split[1].split("_")[0]
        else:
            assembly_version = file_name_with_extension.split(".")[0]
        print(f"{assembly_version}\t{taxid}\t/{file_name_with_extension}\t<None>\t<None>\t<None>")


if __name__ == '__main__':
    main()

