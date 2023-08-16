import argparse
import logging
import sys
from functools import reduce

from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy


def get_postfix(num: int) -> str:
    id_postfix = str(num)
    while len(id_postfix) < 6:
        id_postfix = "0" + id_postfix
    id_postfix += ".1"
    return id_postfix


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes the Zymo reference and adds accessions to the records")
    parser.add_argument(
        "taxonomy",
        help="NCBI taxonomy directory")
    parser.add_argument(
        "zymo_reference",
        help="The zymo reference file")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read taxonomy
    logging.info(f"Reading taxonomy from directory {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Taxonomy read!")

    # Create output file name
    split_input_file = args.zymo_reference.split("/")[-1].split("_")
    genus = split_input_file[0]
    species = split_input_file[1]
    id_prefix = genus[0] + species[0]
    id_number = 1
    output_file_prefix = reduce(
        lambda acc, x: acc + "/" + x, args.zymo_reference.split("/")[
            :-1]) + "/" + genus + "_" + species + "_formatted"
    logging.info(f"Will write to files with prefix '{output_file_prefix}'")

    # Get tax id of all records
    potential_nodes = taxonomy.find_all_by_name(genus + " " + species)
    if len(potential_nodes) != 1:
        logging.error(
            f"{genus} {species} didn't return exactly 1 node, don't know what to do")
        logging.error(f"The following nodes were found: {potential_nodes}")
        sys.exit()
    else:
        tax_node = potential_nodes[0]
        tax_id = tax_node.id

    # Read the reference fasta file and create a new fasta file and
    # accession2taxid for the new file
    logging.info(f"Looping through reference file at {args.zymo_reference}")
    fasta_file = SeqIO.parse(args.zymo_reference, 'fasta')
    with open(output_file_prefix + ".fasta", "w") as out_file_handle:
        with open(output_file_prefix + ".accession2taxid", "w") as accession2taxid:
            for record in fasta_file:
                id_postfix = get_postfix(id_number)
                id_number += 1
                record.id = id_prefix + "_" + id_postfix
                record.description = record.id + " " + record.description
                accession2taxid.write(f"{record.id}\t{tax_id}\n")
                SeqIO.write(record, out_file_handle, 'fasta')
            logging.info("Done reading through reference!")


if __name__ == '__main__':
    main()
