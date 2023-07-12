import argparse
import logging
import sys


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes the .custom.fileToAccssnTaxID file from CLARK and updates the tax ids according to a accession2taxid")
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of reference file")
    parser.add_argument(
        "file_to_accession_taxid",
        help=".custom.fileToAccssnTaxID from CLARK")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read in accession2taxid
    accession2taxid = {}
    logging.info(
        f"Reading accession2taxid at {args.accession2taxid}")
    with open(args.accession2taxid, 'r') as accession2taxid_file:
        for line in accession2taxid_file:
            line = line.strip()
            if line.__contains__("\t"):
                split_line = line.split("\t")
            else:
                split_line = line.split(" ")
            accession = split_line[0].split(".")[0]
            if accession in accession2taxid and accession2taxid[accession] != split_line[-1]:
                logging.error(
                    f"{accession} appeared twice with taxids {accession2taxid[accession]} and {split_line[-1]}")
                logging.error(
                    f"please fix this before running again - aborting")
                sys.exit()
            else:
                accession2taxid[accession] = split_line[-1]
    logging.info("Done reading accession2taxid!")

    with open(args.file_to_accession_taxid, 'r') as f:
        for line in f:
            line = line.strip().split("\t")
            print(f"{line[0]}\t{line[1]}\t{accession2taxid[line[1]]}")


if __name__ == '__main__':
    main()
