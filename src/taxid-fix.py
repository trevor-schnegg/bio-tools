import argparse
import logging
import sys


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Changes the taxid for a specific file in SKiM output"
    )
    parser.add_argument("file_name", help="The file name to update")
    parser.add_argument("new_taxid", help="What to update the taxid to")
    parser.add_argument("tsv_file", help="TSV file to fix")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Read the TSV/CSV
    logging.info(
        f"Updating {args.file_name} to taxid {args.new_taxid} for {args.tsv_file}"
    )

    total_updated = 0

    with open(args.tsv_file, "r") as f:
        for line in f:
            stripped_line = line.strip()
            split_line = list(stripped_line.split("\t"))
            if split_line[3] == args.file_name:
                print(
                    f"{split_line[0]}\t{split_line[1]}\t{args.new_taxid}\t{split_line[3]}"
                )
                total_updated += 1
            else:
                print(stripped_line)

    logging.info(f"total updated tax ids: {str(total_updated)}")

    logging.info("Done!")


if __name__ == "__main__":
    main()
