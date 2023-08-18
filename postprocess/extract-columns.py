import argparse
import logging
import sys


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a tsv of the input columns")
    parser.add_argument(
        "-c",
        "--csv",
        dest="csv",
        action="store_true",
        help="Option if the file is csv (default is tsv)")
    parser.add_argument(
        "-s",
        "--skip-header",
        dest="skip_header",
        action="store_true",
        help="Skip the first line of the input file")
    parser.add_argument("file", help="TSV file to extract columns from")
    parser.add_argument(
        "columns",
        type=str,
        help="Comma separated list of columns to output (0 indexed) "
             "(E.g. 4,6,1 will output 4<tab>6<tab>1)")
    args = parser.parse_args()
    columns = list(map(lambda x: int(x), args.columns.split(",")))
    split_char = "," if args.csv else "\t"

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read the TSV/CSV
    logging.info(f"Outputting columns {str(columns)} from {args.file}")

    with open(args.file, 'r') as f:
        if args.skip_header:
            next(f)
        for line in f:
            line = list(line.strip().split(split_char))
            acc = ""
            for idx, column in enumerate(columns):
                if idx == 0:
                    acc += line[column]
                else:
                    acc += ("\t" + line[column])
            print(acc)

    logging.info("Done!")


if __name__ == '__main__':
    main()
