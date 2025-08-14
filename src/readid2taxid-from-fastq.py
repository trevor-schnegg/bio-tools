import argparse
import logging
import sys

from Bio import SeqIO

from lib.lib import load_accession2taxid


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a tsv read id to tax id mapping from a Badread simulated FASTQ reads"
    )
    parser.add_argument("accession2taxid", help="Tab separated accession to tax id")
    parser.add_argument("fastq_reads", help="Simulated FASTQ reads")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Read accession2taxid
    logging.info(f"Reading accession2taxid at {args.accession2taxid}")
    accession2taxid = load_accession2taxid(args.accession2taxid)
    logging.info("Accession2taxid read!")

    logging.info("Extracting readid2taxid from FASTQ file")
    for read in SeqIO.parse(args.fastq_reads, "fastq"):
        accession = read.description.strip().split(" ")[1].split(",")[0].split(".")[0]
        print(f"{read.id}\t{accession2taxid[accession]}")

    logging.info("Done!")


if __name__ == "__main__":
    main()
