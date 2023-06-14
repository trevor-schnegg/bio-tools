import argparse
import logging
import sys


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a stats file and aggregates statistics")
    parser.add_argument(
        "file",
        help="Location of stats file"
    )
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    agg_id_pct = 0.0
    num_id_pct = 0
    agg_gap_pct = 0.0
    num_gap_pct = 0
    with open(args.file, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("Identity:"):
                pct = float(line.split("(")[-1].strip("%)").strip())
                agg_id_pct += pct
                num_id_pct += 1
            elif line.startswith("Gaps:"):
                pct = float(line.split("(")[-1].strip("%)").strip())
                agg_gap_pct += pct
                num_gap_pct += 1
    print(f"Average identity percent: {str(agg_id_pct / num_id_pct)}")
    print(f"Average gap percent: {str(agg_gap_pct / num_gap_pct)}")


if __name__ == '__main__':
    main()