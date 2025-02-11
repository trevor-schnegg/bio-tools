import argparse
import logging
import sys
from datetime import timedelta


def read_time_output(file):
    file_info = {}
    with open(file, "r") as f:
        for line in f:
            line = line.split(";")[1] if ";" in line else line
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
    parser.add_argument("-f", "--first", dest="first", action="store_true", help="If this is the first classifier being added")
    parser.add_argument("-r", "--rss-max", dest="max_rss", action="store_true", help="The maximum resident set size (memory usage)")
    parser.add_argument("-w", "--wall-clock-time", dest="wall_clock_time", action="store_true", help="The elapsed wall clock time")
    parser.add_argument("file", help="The time output file to parse")
    parser.add_argument("name", help="The name of the classifier being added")

    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    logging.info(f"Reading 'time -v' from {args.file}")

    file_info = read_time_output(args.file)

    if args.max_rss:
        # If this is the first classifier, print the header
        if args.first:
            print("classifier\tmax_rss_(GB)")

        kbytes_str = file_info["Maximum resident set size (kbytes)"]
        gbytes = int(kbytes_str) / 1000000
        print(f"{args.name}\t{str(gbytes)}")

    elif args.wall_clock_time:
        # If this is the first classifier, print the header
        if args.first:
            print("classifier\ttime_(seconds)")

        # Get the string extracted from the 'time -v' file and split on ":"
        time_str = file_info["Elapsed (wall clock) time (h:mm:ss or m:ss)"]
        split_time = list(time_str.split(":"))

        # See the key name for formatting of this string (why this is necessary)
        if len(split_time) == 2:
            minutes = int(split_time[0])
            # In this case, there is also a milliseconds number after a decimal point
            split_time = list(split_time[1].split("."))
            seconds = int(split_time[0])
            milliseconds = int(split_time[1]) * 10
            print(f"{args.name}\t{timedelta(minutes=minutes, seconds=seconds, milliseconds=milliseconds).total_seconds()}")

        elif len(split_time) == 3:
            hours = int(split_time[0])
            minutes = int(split_time[1])
            seconds = int(split_time[2])
            print(f"{args.name}\t{timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()}")

        else:
            logging.error(f"file {args.file} has an unrecognized time format, exiting...")
            sys.exit(1)

    logging.info("Done!")


if __name__ == '__main__':
    main()
