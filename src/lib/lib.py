import logging
import sys


def load_accession2taxid(file):
    accession2taxid = {}
    with open(file, "r") as f:
        for line in f:
            line = line.strip()
            if line.__contains__("\t"):
                # If the line has a tab, split on tab
                split_line = line.split("\t")
            else:
                # Otherwise, split on space
                split_line = line.split(" ")

            # If the accession has a period, remove everything after the period
            accession = split_line[0].split(".")[0]

            # Check to make sure the same accession isn't assigned a tax id twice
            if (
                accession in accession2taxid
                and accession2taxid[accession] != split_line[-1]
            ):
                logging.error(
                    f"{accession} appeared twice with taxids {accession2taxid[accession]} and {split_line[-1]}"
                )
                logging.error(f"please fix this before running again - exiting")
                sys.exit(1)
            else:
                accession2taxid[accession] = split_line[-1]
    return accession2taxid
