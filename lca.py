import argparse
import logging
import sys

import pandas as pd
from taxonomy.taxonomy import Taxonomy


def lca_of_taxids(taxids, taxonomy: Taxonomy) -> str:
    lca = ""
    for idx, taxid in enumerate(taxids):
        if idx == 0:
            lca = str(taxid)
        else:
            lca = taxonomy.lca(lca, str(taxid)).id
    return lca


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
    readid2taxid = pd.read_table(
        args.readid2taxid,
        names=["readid", "taxid"],
        dtype={
            'readid': 'string',
            'taxid': 'int'})
    readid2taxid.sort_values("readid", inplace=True)
    logging.info("Readid2taxid read!")

    logging.info("Making sure all reads only have one tax id")
    last_readid = ""
    last_readid_taxids = set()
    for _, (readid, taxid) in readid2taxid.iterrows():

        if last_readid == readid or last_readid == "":
            # Haven't gathered all information for this read yet
            last_readid = readid
            last_readid_taxids.add(taxid)
            continue
        else:
            # This is a new read
            lca = lca_of_taxids(last_readid_taxids, taxonomy)
            print(f"{last_readid}\t{lca}")

            last_readid = readid
            last_readid_taxids.clear()
            last_readid_taxids.add(taxid)
    lca = lca_of_taxids(last_readid_taxids, taxonomy)
    print(f"{last_readid}\t{lca}")
    logging.info("Done!")


if __name__ == '__main__':
    main()
