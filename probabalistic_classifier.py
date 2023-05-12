import argparse
import logging
import sys
from lib import io

from Bio import SeqIO
from scipy.stats import binom


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Classifies reads based on probability")
    parser.add_argument(
        "-t",
        "--tax-id",
        dest="tax_id",
        action="store_true",
        help="Group sequences by tax id (default is by contig)"
    )
    parser.add_argument(
        "reference",
        help="The file to create a k-mer reference from")
    parser.add_argument(
        "fasta_reads",
        help="The file containing fasta reads for classification")
    parser.add_argument(
        "accession2taxid",
        help="The accession2taxid for the reference file"
    )
    parser.add_argument(
        "kmer_size",
        type=int,
        help="The size of k-mer to use in the database"
    )
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Get accession2taxid
    accession2taxid = io.read_accession2taxid(args.accession2taxid)

    # Read the reference file
    logging.info(f"Creating database from reference at {args.reference}")
    database = {}
    fasta_file = SeqIO.parse(args.reference, 'fasta')
    for record in fasta_file:
        label = record.id
        kmer_set = set()
        if args.tax_id:
            label = accession2taxid[record.id]
            if label in database:
                kmer_set = database[label]
        seq = record.seq.upper()
        for i in range(len(seq) - args.kmer_size):
            kmer = seq[i:i + args.kmer_size]
            if 'N' not in kmer:
                kmer_set.add(hash(kmer))
        database[label] = kmer_set
    logging.info("Database created!")

    probabilities = {}
    for label, kmer_set in database.items():
        probabilities[label] = float(len(kmer_set)) / float(4 ** args.kmer_size)

    logging.info("Beginning classification")
    fasta_reads_iter = SeqIO.parse(args.fasta_reads, 'fasta')
    for read_num, read in enumerate(fasta_reads_iter):
        if read_num != 0 and read_num % 500 == 0:
            logging.debug(f"{read_num} reads completed")
        read_kmers = set()
        seq = read.seq.upper()
        for i in range(len(seq) - args.kmer_size):
            kmer = seq[i:i + args.kmer_size]
            if 'N' not in kmer:
                read_kmers.add(hash(kmer))
        num_queries = len(read_kmers)
        hit_counts = {}
        for kmer in read_kmers:
            for label, kmer_set in database.items():
                if kmer in kmer_set:
                    if label in hit_counts:
                        hit_counts[label] += 1
                    else:
                        hit_counts[label] = 1

        best_prob = float('inf')
        best_prob_tax_id = 0
        for label, num_hits in hit_counts.items():
            prob = binom.sf(num_hits, num_queries, probabilities[label])
            if prob < best_prob:
                best_prob = prob
                if args.tax_id:
                    best_prob_tax_id = label
                else:
                    best_prob_tax_id = accession2taxid[label]
        if best_prob < 0.000000000000001:
            print(f"{read.id}\t{best_prob_tax_id}")
        else:
            print(f"{read.id}\t0")

    logging.info("Done!")

if __name__ == '__main__':
    main()
