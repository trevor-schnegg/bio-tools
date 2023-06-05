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
        description="Outputs a fasta directory with references to genomes in abv of approximately the input size")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=14,
        help="Number of threads to use")
    parser.add_argument(
        "abv",
        help="Directory containing fasta files for abv")
    parser.add_argument(
        "output_dir",
        help="Location of the directory to output symbolic links to"
    )
    parser.add_argument(
        "size",
        type=int,
        help="The size of the filtered abv you'd like to create (in bytes)"
    )
    args = parser.parse_args()

    # 73300000 is the size of the zymo genomes
    output_size = args.size - 73300000

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    logging.info(f"Looping through reference files in {args.abv}")
    with Pool(args.threads) as pool:
        reference_files = map(
            lambda x: os.path.join(
                args.abv, x), filter(
                lambda x: x.endswith('.fna'), os.listdir(
                    args.abv)))
        total_size = 0
        all_files = pool.map(get_info, reference_files)
        while total_size < output_size:
            random_index = random.randint(0, len(all_files) - 1)
            subprocess.run(["ln", "-s", all_files[random_index][0], args.output_dir])
            total_size += all_files[random_index][1]
            all_files.pop(random_index)


if __name__ == '__main__':
    main()
