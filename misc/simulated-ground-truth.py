import argparse
import logging
import os
import sys

from multiprocessing.pool import Pool


def get_readids(file_and_taxid):
    deepsimulator_fasta_dir, taxid = file_and_taxid
    readids = []
    if os.path.isfile(deepsimulator_fasta_dir + "/files.txt"):
        with open(deepsimulator_fasta_dir + "/files.txt", 'r') as f:
            for line in f.readlines():
                prefix = line.strip().split('.')[0]
                readids.append(prefix.split('_')[-1])
        return readids, taxid
    else:
        return None, taxid


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Prints out a tax id to file mapping for the input reference directory")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=20,
        help="Number of threads to use")
    parser.add_argument(
        "deepsimulator_references",
        help="Location of the output of deep simulator for each abv reference"
    )
    parser.add_argument(
        "taxid_to_fasta",
        help="taxid to fasta output of abv")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    fastas_and_taxids = []
    with open(args.taxid_to_fasta, 'r') as f:
        for line in f.readlines():
            line = line.strip().split(' ')
            fastas_and_taxids.append((line[1].split("/")[-1], line[0]))
    fastas_and_taxids = map(
        lambda x: (
            args.deepsimulator_references + x[0], x[1]), fastas_and_taxids)

    logging.info("Looping through deep simulator outputs")
    with Pool(args.threads) as pool:
        for readids, taxid in pool.imap(get_readids, fastas_and_taxids):
            if readids is not None:
                for readid in readids:
                    print(f"{readid}\t{taxid}")


if __name__ == '__main__':
    main()
