import argparse
import logging
import sys
import statistics


def get_readid2taxid(filename):
    readid2taxid = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.strip().split('\t')
            readid2taxid[line[0]] = int(line[1])
    return readid2taxid


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Quick test for myself")
    parser.add_argument(
        "accession2taxid",
        help="Tab separated accession2taxid file")
    parser.add_argument(
        "ground_truth_readid2taxid",
        help="Tab separated read id to tax id of minimap2 or other ground truth")
    parser.add_argument(
        "accession2probabilities",
        help="Tab separated accession to probability from the classifier")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    logging.info(
        f"Reading accession2taxid from {args.accession2taxid}")
    accession2taxid = get_readid2taxid(
        args.accession2taxid)

    logging.info(
        f"Reading ground truth readid2taxid from {args.ground_truth_readid2taxid}")
    ground_truth_readid2taxid = get_readid2taxid(
        args.ground_truth_readid2taxid)

    ne_probabilities = []
    e_probabilities = []
    current_accession2probabilities = {}
    with open(args.accession2probabilities, 'r') as f:
        for line in f.readlines():
            if line.__contains__('\t'):
                line = line.strip().split('\t')
                current_accession2probabilities[line[0]] = float(line[1])
            else:
                readid = line.strip()
                ground_truth_taxid = ground_truth_readid2taxid[readid] if readid in ground_truth_readid2taxid else 0
                for accession, prob in current_accession2probabilities.items():
                    if accession2taxid[accession] != ground_truth_taxid:
                        ne_probabilities.append(prob)
                    else:
                        e_probabilities.append((prob))


    print(f"average: {str(statistics.mean(ne_probabilities))}")
    print(f"std dev: {str(statistics.stdev(ne_probabilities))}")
    print(f"average: {str(statistics.mean(e_probabilities))}")
    print(f"std dev: {str(statistics.stdev(e_probabilities))}")


if __name__ == '__main__':
    main()
