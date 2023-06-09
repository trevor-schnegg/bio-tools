import argparse
import logging
import os
import random
import subprocess
import sys
from multiprocessing.pool import Pool

from Bio import SeqIO


def run_deepsim(info):
    orig_fasta_path = info[0]
    orig_fasta_file = orig_fasta_path.split("/")[-1]
    longest_record = info[1]

    deepsim_binary = info[2]
    output_dir = info[3]
    shortest_seq = info[4]
    # If the longest record is None, then there is only one record in the fasta file. We can just run Deep Simulator
    # on the original file
    if longest_record is None:
        output_path = os.path.join(output_dir, orig_fasta_file)
        record_length = len(next(SeqIO.parse(orig_fasta_path, 'fasta')).seq)
        subprocess.run([deepsim_binary, '-i', orig_fasta_path, '-o', output_path])
    else:



def get_info(fasta_file):
    longest_record = None
    largest_record_index = -1
    for i, record in enumerate(SeqIO.parse(fasta_file, 'fasta')):
        largest_record_index = i
        if longest_record is None:
            longest_record = record
        elif len(record.seq) > len(longest_record.seq):
            longest_record = record
    return fasta_file, None if largest_record_index == 0 else longest_record, len(longest_record.seq)


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Calls Deep-Simulator to create the desired simulated reads")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=19,
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
        all_info = pool.map(get_info, reference_files)
        shortest_seq = min(all_info, key=lambda x: x[2])
        longest_seq = max(all_info, key=lambda x: x[2])
        print(f"shortest: {shortest_seq}")
        print(f"longest: {longest_seq}")
        sys.exit()
        for res in pool.map(run_deepsim, map(lambda x: (x[0], x[1], args.deepsim_binary, args.output_dir, shortest_seq), all_info)):
            try:
                assert res[0]
            except AssertionError:
                logging.error(f"Error occurred when running Deep Simulator on {res[1]}")

if __name__ == '__main__':
    main()