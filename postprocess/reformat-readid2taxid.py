import argparse
import logging
import sys


def get_readid2taxid(filename):
    readid2taxid = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.strip().split('\t')
            readid2taxid[line[0]] = int(line[1])
    return readid2taxid

def get_krakenuniq_readid2readid(filename):
    krakenuniq_accession2taxid = get_readid2taxid(filename)
    accession2taxid = get_readid2taxid(filename + ".orig")
    taxid2taxid = {}
    for accession, taxid in krakenuniq_accession2taxid.items():
        real_taxid = accession2taxid[accession]
        taxid2taxid[taxid] = real_taxid
    return taxid2taxid


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a tsv of the input columns")
    parser.add_argument(
        "-c",
        "--clark",
        dest="clark",
        action="store_true",
        help="If the read id to tax id is CLARK, we need to replace NA with 0")
    parser.add_argument(
        "-u",
        "--krakenuniq",
        dest="krakenuniq_map",
        default=None,
        help="The seqid2taxid.map file provided by krakenuniq and the accession2taxid mapping for the dataset")
    parser.add_argument("file", help="read id to tax id file to reformat")
    args = parser.parse_args()
    krakenuniq_taxid2taxid = None if args.krakenuniq_map is None else get_krakenuniq_readid2readid(args.krakenuniq_map)

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read the TSV/CSV
    logging.info(f"Reformatting {args.file}")

    with open(args.file, 'r') as f:
        for line in f.readlines():
            line = list(line.strip().split("\t"))
            readid = line[0]
            value = line[1]
            if args.clark and value == "NA":
                value = "0"
            elif krakenuniq_taxid2taxid is not None:
                value = int(value)
                if value > 1000000000:
                    value = krakenuniq_taxid2taxid[value]
                value = str(value)
            print(f"{readid}\t{value}")

    logging.info("Done reformatting!")


if __name__ == '__main__':
    main()
