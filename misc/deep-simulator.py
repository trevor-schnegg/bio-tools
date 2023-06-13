import argparse
import logging
import os
import subprocess
import sys
from multiprocessing.pool import Pool

from Bio import SeqIO


def create_deepsim_bash_script(args_tuple):
    fasta_file_path, deepsim_binary, output_dir = args_tuple

    file_info = get_longest_record(fasta_file_path)
    longest_record, longest_record_length = file_info

    fasta_file = fasta_file_path.split("/")[-1]
    output_path = os.path.join(output_dir, fasta_file)

    # If the longest record is None, then there is only one record in the fasta file. We can just run Deep Simulator
    # on the original file
    if longest_record is None:
        print(f"{deepsim_binary} -i {fasta_file_path} -o {output_path} -n {str(round(longest_record_length / 220) * 5)} -c 20 -e 1.25 -s 1.25")

    else:
        temp_file = os.path.join(output_dir, fasta_file + ".tmp")
        with open(temp_file, "w") as f:
            SeqIO.write(longest_record, f, 'fasta')

        print(f"{deepsim_binary} -i {temp_file} -o {output_path} -n {str(round(longest_record_length / 220) * 5)} -c 20 -e 1.25 -s 1.25")
        print(f"rm {temp_file}")


def get_longest_record(fasta_file):
    longest_record = None
    largest_record_index = -1
    for i, record in enumerate(SeqIO.parse(fasta_file, 'fasta')):
        largest_record_index = i
        if longest_record is None:
            longest_record = record
        elif len(record.seq) > len(longest_record.seq):
            longest_record = record
    return None if largest_record_index == 0 else longest_record, len(
        longest_record.seq)


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Calls Deep-Simulator to create the desired simulated reads")
    parser.add_argument(
        "-c",
        "--calculate-stats",
        dest="calculate_stats",
        action="store_true",
        help="Option to calculate the total number of bases to be used for simulation"
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=7,
        help="Number of threads to use")
    parser.add_argument(
        "abv",
        help="Directory containing fasta files for abv")
    parser.add_argument(
        "deepsim_binary",
        help="The bash file for deep simulator"
    )
    parser.add_argument(
        "output_dir",
        help="Location to output Deep Simulator data"
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
            lambda x: os.path.realpath(
                os.path.join(
                    args.abv, x)), filter(
                lambda x: x.endswith('.fna') or x.endswith('.fasta'), os.listdir(
                    args.abv)))
        if args.calculate_stats:
            total_len = 0
            for info in pool.imap(get_longest_record, reference_files):
                total_len += info[1]
            print(f"total bases: {total_len}")
        else:
            deepsim_args = map(
                lambda file: (
                    file,
                    args.deepsim_binary,
                    args.output_dir),
                reference_files)
            for _ in pool.imap(create_deepsim_bash_script, deepsim_args):
                continue


if __name__ == '__main__':
    main()
