import argparse
import logging
import sys


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Quick script to add the groud truth taxid to the tsv file")
    parser.add_argument("original_file", help="TSV file to add to")
    parser.add_argument(
        "true_readid2taxid",
        type=str,
        help="The true readid2taxid to add")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    true_readid2taxid = {}
    with open(args.true_readid2taxid, 'r') as f:
        for line in f:
            line = line.strip().split('\t')
            true_readid2taxid[line[0]] = line[1]

    with open(args.original_file, 'r') as f:
        for line in f:
            readid = line.strip().split('\t')[0]
            true_taxid = true_readid2taxid[readid]
            print(line.strip() + '\t' + true_taxid)


if __name__ == '__main__':
    main()
