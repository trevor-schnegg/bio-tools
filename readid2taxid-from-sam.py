import argparse
import logging
import sys

import pandas as pd
import pysam
from taxonomy.taxonomy import Taxonomy


def process_mappings(mapq, taxonomy, readid, readid_mappings):
    readid_mappings = list(readid_mappings)
    if mapq:
        readid_mappings.sort(reverse=True, key=lambda x: x[1])
        top_mapq = readid_mappings[0][1]
        last_idx = 0
        for idx, mapping in enumerate(readid_mappings):
            if mapping[1] == top_mapq:
                last_idx = idx
            else:
                break
        readid_mappings = readid_mappings[0:last_idx + 1]
    if taxonomy is None or len(readid_mappings) <= 1:
        print_mappings(readid, list(map(lambda x: x[0], readid_mappings)))
    else:
        lca = str(readid_mappings[0][0])
        for (taxid, _) in readid_mappings[1:]:
            lca = taxonomy.lca(lca, str(taxid)).id
        print_mappings(readid, [lca])

def print_mappings(readid: str, taxids: list[int]):
    for taxid in taxids:
        print(f"{readid}\t{str(taxid)}")

def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a tsv read id to tax id mapping from a sam file")
    parser.add_argument(
        "-e",
        "--exclude_none",
        action="store_true",
        help="Do not print out reads with no mapping location")
    parser.add_argument(
        "-t",
        "--top_mapq",
        action="store_true",
        help="Only keep the highest MAPQ value for each read "
             "(Note: there may be multiple mappings with the same quality, applies before -l option)")
    parser.add_argument(
        "-l",
        "--lca",
        default=None,
        help="Make each read map to a single tax id by using the lca"
             "(Note: must specify NCBI taxonomy directory if you want lca, applies after -t option)")
    parser.add_argument(
        "accession2taxid",
        help="Tab separated accession to tax id")
    parser.add_argument("sam_file", help="SAM alignment file")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read taxonomy
    taxonomy = None
    if args.lca is not None:
        taxonomy = Taxonomy.from_ncbi(args.lca)

    # Read accession2taxid
    accession2taxid = pd.read_table(
        args.accession2taxid,
        names=["accession", "taxid"],
        dtype={
            'accession': 'string',
            'taxid': 'int'})

    # Read SAM file
    sam_file_iter = iter(pysam.AlignmentFile(args.sam_file, "r"))

    all_readids = set()
    last_readid = ""
    readid_mappings = set()
    while (alignment := next(sam_file_iter, None)) is not None:
        readid = alignment.query_name
        accession = alignment.reference_name
        mapq = alignment.mapping_quality

        if last_readid == readid or last_readid == "":
            # Haven't gathered all information for this read yet
            last_readid = readid
            if accession is not None:
                readid_mappings.add(
                    (accession2taxid.loc[accession2taxid['accession'] == accession]['taxid'].values[0], mapq))
            elif not args.exclude_none:
                readid_mappings.add((0, 0))
            continue
        else:
            # This is a new read
            # Print the information for the last read
            process_mappings(args.top_mapq, taxonomy, last_readid, readid_mappings)
            # Initialize new read stats
            if last_readid not in all_readids:
                all_readids.add(last_readid)
            else:
                raise Exception(f"Read id {last_readid} appeared more than once out of sequence")

            last_readid = readid
            readid_mappings.clear()
            if accession is not None:
                readid_mappings.add(
                    (accession2taxid.loc[accession2taxid['accession'] == accession]['taxid'].values[0], mapq))
            elif not args.exclude_none:
                readid_mappings.add((0, 0))
    process_mappings(args.top_mapq, taxonomy, last_readid, readid_mappings)



if __name__ == '__main__':
    main()
