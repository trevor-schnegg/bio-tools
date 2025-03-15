import argparse
import logging
import sys


def get_order_from_output(out_file):
    with open(out_file, "r") as f:
        f = iter(f)
        return list(next(f).strip().split("\t"))


def get_order_from_input(in_file, skip_formula_headers):
    order = []
    with open(in_file, "r") as f:
        f = iter(f)

        # Skip header lines
        if skip_formula_headers:
            for _ in range(6):
                next(f)
        else:
            next(f)

        for line in f:
            order.append(line.strip().split("\t")[0])
    return order


def get_new_row_data(in_file, skip_formula_headers, is_sizes):
    new_row_data = {}
    with open(in_file, "r") as f:
        f = iter(f)

        # Skip header lines
        if skip_formula_headers:
            for _ in range(6):
                next(f)
        else:
            next(f)

        # Add new stats
        for line in f:
            line = line.strip().split("\t")
            if is_sizes:
                new_row_data[line[0]] = line[1]
            else:
                new_row_data[line[0]] = line[6]
    return new_row_data


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a row of data to use in gnuplot"
    )
    parser.add_argument(
        "-f",
        "--first",
        dest="first_line",
        action="store_true",
        help="If this is the first extraction for the gnuplot data",
    )
    parser.add_argument(
        "-s",
        "--skip-formula-headers",
        dest="skip_formula_headers",
        action="store_true",
        help="If the raw statistics has the formula headers",
    )
    parser.add_argument(
        "--sizes",
        dest="is_sizes",
        action="store_true",
        help="If the data is maximum rss sizes",
    )
    parser.add_argument("input_file", help="Tabular report file to extract from")
    parser.add_argument("output_file", help="The output file")

    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Get the new row data from the input file
    new_row_data = get_new_row_data(
        args.input_file, args.skip_formula_headers, args.is_sizes
    )

    # If this is the first line, write the order to the output file
    if args.first_line:
        order = get_order_from_input(args.input_file, args.skip_formula_headers)
        order_str = f"{order[0]}"
        for classifier in order[1:]:
            order_str += f"\t{classifier}"
        with open(args.output_file, "a") as out_file:
            out_file.write(order_str + "\n")

    order = get_order_from_output(args.output_file)
    new_row_str = f"{new_row_data[order[0]]}"
    for classifier in order[1:]:
        new_row_str += f"\t{new_row_data[classifier]}"
    with open(args.output_file, "a") as out_file:
        out_file.write(new_row_str + "\n")

    logging.info("Done!")


if __name__ == "__main__":
    main()
