import argparse
import logging
import sys

def get_order_from_output(out_file):
    with open(out_file, "r") as f:
        f = iter(f)
        return list(next(f).strip().split("\t"))

def get_order_from_input(in_file):
    order = []
    with open(in_file, "r") as f:
        f = iter(f)
        # Skip the header line of the tabular data
        next(f)
        for line in f:
            order.append(line.strip().split("\t")[0])
    return order


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a row of data to use in gnuplot")
    parser.add_argument(
        "-f",
        "--first",
        dest="first_line",
        action="store_true",
        help="If this is the first extraction for the gnuplot data")
    parser.add_argument("input_file", help="Tabular report file to extract from")
    parser.add_argument("output_file", help="The output file")

    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Get the new row data from the input file
    new_row_data = {}
    with open(args.input_file, 'r') as in_file:
        in_file = iter(in_file)
        # Skip the header line of the tabular data
        next(in_file)
        for line in in_file:
            line = list(line.strip().split("\t"))
            new_row_data[line[0]] = line[6]

    # If this is the first line, write the order to the output file
    if args.first_line:
        order = get_order_from_input(args.input_file)
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


if __name__ == '__main__':
    main()
