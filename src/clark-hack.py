import argparse
import logging
import sys

from lib.lib import load_accession2taxid


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes the .custom.fileToAccssnTaxID file from CLARK and updates the tax ids according to a accession2taxid (prints to stdout)"
    )
    parser.add_argument("accession2taxid", help="accession2taxid of reference file")
    parser.add_argument(
        "file_to_accession_taxid", help=".custom.fileToAccssnTaxID from CLARK"
    )
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Read in accession2taxid
    logging.info(f"Reading accession2taxid at {args.accession2taxid}")
    accession2taxid = load_accession2taxid(args.accession2taxid)
    logging.info("Done reading accession2taxid!")

    with open(args.file_to_accession_taxid, "r") as f:
        for line in f:
            line = line.strip().split("\t")
            print(f"{line[0]}\t{line[1]}\t{accession2taxid[line[1]]}")


if __name__ == "__main__":
    main()
