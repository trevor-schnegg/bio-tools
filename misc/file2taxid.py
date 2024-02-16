import argparse
import logging
import os
import sys
from Bio import SeqIO

def get_accession2taxid(file):
    accession2taxid = {}
    with open(file, 'r') as accession2taxid_file:
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
    return accession2taxid

def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Creates a file to taxid mapping")
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of reference file")
    parser.add_argument(
        "reference_sequences",
        help="a file directory containing reference sequences")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read in accession2taxid
    logging.info(
        f"Reading accession2taxid at {args.accession2taxid}")
    accession2taxid = get_accession2taxid(args.accession2taxid)
    logging.info("Done reading accession2taxid!")

    files_and_taxids = []
    for i, file in enumerate(os.listdir(args.reference_sequences)):
        if i % 1000 == 0 and i != 0:
            logging.info(f"{str(i)} files processed")
        file = os.path.join(args.reference_sequences, file)
        if os.path.isfile(file):
            if file.endswith(".fasta") or file.endswith(".fna"):
                first = next(SeqIO.parse(file, 'fasta'))
                files_and_taxids.append((file, accession2taxid[first.id.split('.')[0]]))
    files_and_taxids.sort(key=lambda x: x[1])
    for file, taxid in files_and_taxids:
        print(f"{file}\t{taxid}")


if __name__ == '__main__':
    main()
