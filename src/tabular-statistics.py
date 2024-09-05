import argparse

def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes tsv output from report-statistics.py and takes it tabular")
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
        f = iter(f)
        curr_line = next(f, None)
        if args.skip_headers:
            for _ in range(11):
                curr_line = next(f, None)

        print("classifier\tgenus_prec\tgenus_recall\tgenus_acc\tspecies_prec\tspecies_recall\tspecies_acc")

        # Each iteration of the while loop processes a full classifier
        while curr_line is not None:
            classifier_name = next(f, None)
            if classifier_name is None:
                break
            classifier_name = classifier_name.strip()

            stats_line_1 = next(f).strip().split("\t")

            # "Burn" the middle line -- doesn't have precision, recall, or accuracy
            next(f)

            stats_line_3 = next(f).strip().split("\t")

            print(f"{classifier_name}\t{stats_line_3[0]}\t{stats_line_1[2]}\t{stats_line_3[2]}\t{stats_line_3[4]}\t{stats_line_1[6]}\t{stats_line_3[6]}")

            # "Burn" the newline between classifier outputs
            curr_line = next(f, None)


if __name__ == '__main__':
    main()
