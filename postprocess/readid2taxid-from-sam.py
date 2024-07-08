import argparse
import logging
import sys

import pandas as pd
import pysam
from taxonomy.taxonomy import Taxonomy

def load_accession2taxid(file):
    accession2taxid = {}
    with open(file, 'r') as f:
        for line in f:
            line = line.strip().split('\t')
            accession2taxid[line[0]] = int(line[1])
    return accession2taxid

def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a tsv read id to tax id mapping from a sam file")
    parser.add_argument(
        "-e",
        "--exclude-none",
        dest="exclude_none",
        action="store_true",
        help="Do not print out reads with no mapping location")
    parser.add_argument(
        "accession2taxid",
        help="Tab separated accession to tax id")
    parser.add_argument(
        "sam_file",
        help="SAM alignment file")
    parser.add_argument(
        "taxonomy",
        help="The NCBI taxonomy location")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read taxonomy
    logging.info(f"Attempting to read taxonomy from directory {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Taxonomy read!")

    # Read accession2taxid
    logging.info(f"Reading accession2taxid at {args.accession2taxid}")
    accession2taxid = load_accession2taxid(args.accession2taxid)
    logging.info("Accession2taxid read!")

    last_readid = ""
    last_readid_highest_mapq = -1
    mappings_buffer = []
    logging.info("Extracting readid2taxid from SAM file")
    for alignment in pysam.AlignmentFile(args.sam_file, 'r'):
        readid = alignment.query_name
        accession = alignment.reference_name
        mapq = alignment.mapping_quality

        if last_readid == readid or last_readid == "":
            # Haven't gathered all information for this read yet
            if last_readid == "":
                last_readid = readid
            
            if mapq >= last_readid_highest_mapq:
                mappings_buffer.clear()
                last_readid_highest_mapq = mapq
                mappings_buffer.append(accession)

        else:
            # This is a new read
            # Print the information for the last read
            if len(mappings_buffer) == 1:
                print_accession = mappings_buffer[0]
                if print_accession is None:
                    print(f"{last_readid}\t0")
                else:
                    print(f"{last_readid}\t{accession2taxid[mappings_buffer[0]]}")
            else:
                lca = accession2taxid[mappings_buffer[0]]
                for accession in mappings_buffer[1:]:
                    lca = taxonomy.lca(lca, accession2taxid[accession]).id
                print(f"{last_readid}\t{lca}")
            
            # Start the new readid
            last_readid = readid
            mappings_buffer.clear()
            mappings_buffer.append(accession)
            last_readid_highest_mapq = mapq
    
    # Print remaining information in the buffer
    if len(mappings_buffer) == 1:
        print_accession = mappings_buffer[0]
        if print_accession is None:
            print(f"{last_readid}\t0")
        else:
            print(f"{last_readid}\t{accession2taxid[mappings_buffer[0]]}")
    else:
        lca = accession2taxid[mappings_buffer[0]]
        for accession in mappings_buffer[1:]:
            lca = taxonomy.lca(lca, accession2taxid[accession]).id
        print(f"{last_readid}\t{lca}")

    logging.info("Done!")


if __name__ == '__main__':
    main()
