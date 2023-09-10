import argparse
import logging
import sys

import pandas as pd
from taxonomy.taxonomy import Taxonomy


def lca_of_taxids(taxids, taxonomy: Taxonomy) -> str:
    lca = ""
    for idx, taxid in enumerate(taxids):
        if taxid == 0:
            return "0"

        if idx == 0:
            lca = str(taxid)
        else:
            lca = taxonomy.lca(lca, str(taxid)).id
    return lca


def get_readid2taxid_for_lca(filename):
    readid2taxid = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.strip().split('\t')
            read_id = line[0]
            if read_id in readid2taxid:
                readid2taxid[read_id].append(int(line[1]))
            else:
                readid2taxid[read_id] = [int(line[1])]
    return readid2taxid


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes read id to tax id mapping. "
                    "Ensures that each read id has only one tax id by using the lca if needed")
    parser.add_argument(
        "taxonomy",
        help="NCBI taxonomy directory")
    parser.add_argument(
        "readid2taxid",
        help="Tab separated read id to tax id")
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

    logging.info(f"Reading readid2taxid at {args.readid2taxid}")
    # Read readid2taxid
    readid2taxid = get_readid2taxid_for_lca(args.readid2taxid)
    logging.info("Readid2taxid read!")

    logging.info("Computing the LCA of all reads")
    for read_id, tax_ids in readid2taxid.items():
        lca = lca_of_taxids(tax_ids, taxonomy)
        print(f"{read_id}\t{lca}")

    logging.info("Done!")


if __name__ == '__main__':
    main()
