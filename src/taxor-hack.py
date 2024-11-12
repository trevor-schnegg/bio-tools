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
        description="Creates an input tsv file for taxor based on a reference database")
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of reference file")
    parser.add_argument(
        "reference_directory",
        help="Directory containing reference fasta files")
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

    # Read taxonomy
    logging.info(f"Reading taxonomy from directory {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)

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

    logging.info("Getting lineage for all tax ids in the reference")
    taxids_in_ref = set()
    for taxid in accession2taxid.values():
        taxids_in_ref.add(taxid)

    levels = ["superkingdom", "phylum", "class", "order", "family", "genus", "species"]
    taxid_to_lineage = {}
    for taxid in taxids_in_ref:
        organism_names = []
        organism_taxids = []
        for level in levels:
            node = taxonomy.parent(str(taxid), at_rank=level)
            if node is not None:
                if level == "superkingdom":
                    name = f"k__{node.name}"
                else:
                    name = f"{level[0]}__{node.name}"
                organism_names.append(name)
                organism_taxids.append(node.id)
        taxid_to_lineage[taxid] = [organism_names, organism_taxids]

    logging.info("Printing taxor reference strings")
    for file in ref_files:
        file_name_with_extension = os.path.basename(file)

        taxid = accession2taxid[next(SeqIO.parse(file, 'fasta')).id.split(".")[0]]
        lineage = taxid_to_lineage[taxid]
        lineage_names = lineage[0]
        lineage_taxids = lineage[1]
        # Update taxid to the lowest available taxid
        taxid = lineage_taxids[-1]

        lineage_names_str = lineage_names[0]
        for lineage_name in lineage_names[1:]:
            lineage_names_str += f";{lineage_name}"

        lineage_taxid_str = lineage_taxids[0]
        for lineage_taxid in lineage_taxids[1:]:
            lineage_taxid_str += f";{lineage_taxid}"

        assembly_version = ""
        if "_" in file_name_with_extension:
            file_split = file_name_with_extension.split(".")
            assembly_version = file_split[0] + file_split[1].split("_")[0]
        else:
            assembly_version = file_name_with_extension.split(".")[0]

        print(f"{assembly_version}\t{taxid}\t/{file_name_with_extension}\t{lineage_names[-1].split('_')[2:][0]}\t{lineage_names_str}\t{lineage_taxid_str}")


if __name__ == '__main__':
    main()

