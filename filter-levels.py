import argparse
import logging
import sys

from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a fasta file with the input taxon levels excluded")
    parser.add_argument(
        "-d",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Option to not actually output sequences only to log what the size change would be"
    )
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of reference file")
    parser.add_argument(
        "reference_fasta",
        help="The reference file in fasta format")
    parser.add_argument(
        "taxonomy",
        help="NCBI taxonomy directory")
    parser.add_argument(
        "taxon_levels",
        type=str,
        help="Comma separated taxon levels to exclude"
    )
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    exclude_taxon_levels = list(args.taxon_levels.strip().split(","))
    logging.info(f"filtering out levels: {exclude_taxon_levels}")

    # Read in accession2taxid
    accession2taxid = {}
    logging.info(
        f"Reading accession2taxid at {args.accession2taxid}")
    with open(args.accession2taxid, 'r') as accession2taxid_file:
        for line in accession2taxid_file:
            formatted_line = line.strip().split('\t')
            accession2taxid[formatted_line[0]] = formatted_line[1]
    logging.info("Done reading accession2taxid!")

    # Read in taxonomy
    logging.info(f"Reading taxonomy from {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Done reading taxonomy!")

    # Read through reference fasta
    reference = SeqIO.parse(args.reference_fasta, 'fasta')

    if args.dry_run:
        total_sequence_len = 0
        filtered_sequence_len = 0
        for record in reference:
            total_sequence_len += len(record.seq)
            tax_node = taxonomy.node(accession2taxid[record.id])
            if tax_node.rank not in exclude_taxon_levels:
                filtered_sequence_len += len(record.seq)
        logging.info(f"total sequence length was: {total_sequence_len}")
        logging.info(f"filtered sequence length was {filtered_sequence_len}")
    else:
        for record in reference:
            tax_node = taxonomy.node(accession2taxid[record.id])
            if tax_node.rank not in exclude_taxon_levels:
                SeqIO.write(record, sys.stdout, "fasta")


if __name__ == '__main__':
    main()
