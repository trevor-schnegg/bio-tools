import argparse

def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes tsv output from report-statistics.py and converts to tabular data for the paper")
    parser.add_argument(
        "file"
    )
    parser.add_argument(
        "-s",
        "--skip-headers",
        action="store_true",
        dest="skip_headers",
    )
    args = parser.parse_args()

    with open(args.file, 'r') as f:
        file_iter = iter(f)
        value = next(file_iter, None)
        if args.skip_headers:
            for _ in range(11):
                value = next(file_iter, None)

        while value is not None:
            classifier = next(file_iter, None)
            if classifier is None:
                break
            classifier = classifier.strip()
            first_line = next(file_iter).strip().split("\t")
            next(file_iter)
            third_line = next(file_iter).strip().split("\t")
            print(f"{classifier}\t{third_line[0]}\t{first_line[2]}\t{third_line[2]}\t{third_line[4]}\t{first_line[6]}\t{third_line[6]}")
            value = next(file_iter, None)


if __name__ == '__main__':
    main()