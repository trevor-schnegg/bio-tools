import argparse
import logging
import os
import random
import subprocess
import sys
from multiprocessing.pool import Pool


def get_info(fasta_file):
    file_size = os.stat(fasta_file).st_size
    return fasta_file, file_size


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a fasta directory with references to genomes in abv of approximately 1/2 input size"
    )
    parser.add_argument(
        "-t", "--threads", type=int, default=14, help="Number of threads to use"
    )
    parser.add_argument(
        "starting_reference", help="Directory containing reference fasta files"
    )
    parser.add_argument(
        "output_directory", help="Location of the directory to output symbolic links to"
    )
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    logging.info(f"Looping through reference files in {args.starting_reference}")
    with Pool(args.threads) as pool:
        ref_files = map(
            lambda x: os.path.realpath(os.path.join(args.starting_reference, x)),
            filter(
                lambda x: x.endswith(".fna") or x.endswith(".fasta"),
                os.listdir(args.starting_reference),
            ),
        )

        # Get the size of each file
        ref_files_info = pool.map(get_info, ref_files)

        # Get the total size of all files
        total_current_size = sum(map(lambda x: x[1], ref_files_info))

        print(f"current total size: {total_current_size}")
        half_total_size = round(total_current_size / 2)
        print(f"goal total size: {half_total_size}")

        # Pop a random file from the group until the size is below the goal
        while total_current_size > half_total_size:
            random_index = random.randint(0, len(ref_files_info) - 1)
            total_current_size -= ref_files_info[random_index][1]
            ref_files_info.pop(random_index)

        total_resulting_size = sum(map(lambda x: x[1], ref_files_info))
        print(f"resulting size: {total_resulting_size}")

        # Symbolic link each output file (instead of copying)
        for file, _ in ref_files_info:
            subprocess.run(["ln", "-s", file, args.output_directory])


if __name__ == "__main__":
    main()
