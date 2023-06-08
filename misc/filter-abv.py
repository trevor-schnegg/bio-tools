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
        description="Outputs a fasta directory with references to genomes in abv of approximately 1/2 input size")
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
    args = parser.parse_args()

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
        all_files = pool.map(get_info, reference_files)
        # 73300000 is the size of the zymo genomes
        total_current_size = sum(map(lambda x: x[1], all_files))
        print(total_current_size)
        half_total_size = round(total_current_size / 2)
        print(half_total_size)
        while total_current_size > half_total_size:
            random_index = random.randint(0, len(all_files) - 1)
            total_current_size -= all_files[random_index][1]
            all_files.pop(random_index)
        for (file, _) in all_files:
            subprocess.run(["ln", "-s", file, args.output_dir])


if __name__ == '__main__':
    main()
