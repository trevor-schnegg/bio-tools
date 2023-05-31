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
        "-i",
        "--include",
        dest="include",
        action="store_true",
        help="Option that makes the selected taxon levels to be INCLUDED instead of excluded"
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

    taxon_levels = list(args.taxon_levels.strip().split(","))
    if args.include:
        logging.info(f"including levels: {taxon_levels}")
    else:
        logging.info(f"filtering out levels: {taxon_levels}")

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
        # genus_counts = {}
        total_sequence_len = 0
        included_sequence_len = 0
        excluded_sequence_len = 0
        skipped_sequence_len = 0
        for record in reference:
            total_sequence_len += len(record.seq)
            tax_node = taxonomy.node(accession2taxid[record.id])
            if tax_node is None:
                skipped_sequence_len += len(record.seq)
                logging.warning(
                    f"taxid '{accession2taxid[record.id]}' not found in taxonomy, skipping...")
                continue

            # # Block to determine the genus and increment counts, if there is one
            # genus = taxonomy.parent(accession2taxid[record.id], at_rank='genus')
            # if genus is not None:
            #     if genus.name in genus_counts:
            #         genus_counts[genus.name] += 1
            #     else:
            #         genus_counts[genus.name] = 1

            if args.include and tax_node.rank in taxon_levels:
                included_sequence_len += len(record.seq)
            elif not args.include and tax_node.rank not in taxon_levels:
                included_sequence_len += len(record.seq)
            else:
                excluded_sequence_len += len(record.seq)
        logging.info(f"total sequence length was: {total_sequence_len}")
        logging.info(f"skipped sequence length was: {skipped_sequence_len}")
        logging.info(f"included sequence length was {included_sequence_len}")
        logging.info(f"excluded sequence length was {excluded_sequence_len}")
        # for name, count in genus_counts.items():
        #     print(f"{name}\t{count}")
    else:
        for record in reference:
            tax_node = taxonomy.node(accession2taxid[record.id])
            if tax_node is None:
                logging.warning(
                    f"taxid '{accession2taxid[record.id]}' not found in taxonomy, skipping...")
                continue
            elif args.include and tax_node.rank in taxon_levels:
                SeqIO.write(record, sys.stdout, "fasta")
            elif not args.include and tax_node.rank not in taxon_levels:
                SeqIO.write(record, sys.stdout, "fasta")


if __name__ == '__main__':
    main()
