import argparse
import logging
import sys


def read_time_output(file):
    file_info = {}
    with open(file, "r") as f:
        for line in f:
            split_line = line.strip().split(" ")
            value = split_line[-1]
            key = f"{split_line[0]}"
            for split in split_line[1:-1]:
                key += f" {split}"
            file_info[key.strip(":")] = value
    return file_info


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs the requested features of the 'time -v' command")
    parser.add_argument("-w", "--wall-clock-time", dest="wall_clock_time", action="store_true", help="The elapsed wall clock time")
    parser.add_argument("-r", "--rss-max", dest="maximum_rss_size", action="store_true", help="The maximum resident set size (memory usage)")
    parser.add_argument("file", help="The time output file to parse")

    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    file_info = read_time_output(args.file)

    if args.wall_clock_time:
        "Elapsed (wall clock) time (h:mm:ss or m:ss)"
    elif args.max_rss:
        "Maximum resident set size (kbytes)"

    logging.info("Done!")


if __name__ == '__main__':
    main()
