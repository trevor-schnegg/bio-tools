import argparse
import logging
import os
import sys
from multiprocessing.pool import Pool

from Bio import SeqIO
from taxonomy.taxonomy import Taxonomy


def get_info(fasta_file):
    file_size = os.stat(fasta_file).st_size
    first_record = next(SeqIO.parse(fasta_file, 'fasta'))
    first_accession = first_record.id
    return fasta_file, first_accession, file_size, True if first_record.description.__contains__(
        "strain") or first_record.description.__contains__("str.") or first_record.description.__contains__("isolate") else False


def create_ratios(archaea_len, bacteria_len, viral_len):
    minimum = min(archaea_len, bacteria_len, viral_len)
    return archaea_len / minimum, bacteria_len / minimum, viral_len / minimum


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Outputs a fasta directory with references to genomes in abv of approximately the input size")
    parser.add_argument(
        "-b",
        "--below",
        action="store_true",
        help="Use this option if you need the reference to stay below the target amount. By default it will be slightly above")
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=14,
        help="Number of threads to use")
    parser.add_argument(
        "accession2taxid",
        help="accession2taxid of reference file")
    parser.add_argument(
        "abv",
        help="Directory containing fasta files for abv")
    parser.add_argument(
        "size",
        type=int,
        help="The size of the filtered abv you'd like to create (in bytes)"
    )
    parser.add_argument(
        "taxonomy",
        help="NCBI taxonomy directory")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    # Read in accession2taxid
    accession2taxid = {}
    logging.info(
        f"Reading accession2taxid at {args.accession2taxid}")
    with open(args.accession2taxid, 'r') as accession2taxid_file:
        for line in accession2taxid_file:
            formatted_line = line.strip().split(' ')
            accession2taxid[formatted_line[0]] = formatted_line[4]
    logging.info("Done reading accession2taxid!")

    # Read in taxonomy
    logging.info(f"Reading taxonomy from {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Done reading taxonomy!")

    logging.info(f"Looping through reference files in {args.abv}")
    species_counts = {"Archaea": {}, "Bacteria": {}, "Viruses": {}}
    with Pool(args.threads) as pool:
        reference_files = map(
            lambda x: os.path.join(
                args.abv, x), filter(
                lambda x: x.endswith('.fna'), os.listdir(
                    args.abv)))
        files_read = 0
        for (
                file_name,
                first_accession,
                size,
                is_strain) in pool.imap(
                get_info,
                reference_files):
            tax_node = taxonomy.node(accession2taxid[first_accession])
            # If there is no tax node for this tax id, skip it
            if tax_node is None:
                continue

            taxid = tax_node.id
            super_kingdom_dict = species_counts[taxonomy.parent(
                taxid, at_rank="superkingdom").name]

            # If the node is a species node and 'strain' wasn't anywhere in the
            # description
            if tax_node.rank == "species" and not is_strain:
                # Check if this tax id has already been added to the dictionary
                if taxid in super_kingdom_dict:
                    # If it has already been added, check if another "proper"
                    # species has been added
                    if "files" in super_kingdom_dict[taxid]:
                        super_kingdom_dict[taxid]["files"].append(file_name)
                        super_kingdom_dict[taxid]["size"] += size
                    else:
                        super_kingdom_dict[taxid]["count"] += 1
                        super_kingdom_dict[taxid]["files"] = [file_name]
                        super_kingdom_dict[taxid]["size"] = size
                # If the tax id hasn't been added, add it
                else:
                    super_kingdom_dict[taxid] = {
                        "files": [file_name], "count": 1, "size": size}
            # If this is not a "proper" species, then try to find its parent
            # species
            else:
                species_parent = taxonomy.parent(
                    taxid, at_rank="species")
                # If there is no species parent, add just this to the
                # dictionary (there are only 2 of these in abv)
                if species_parent is None:
                    logging.warning(
                        f"{tax_node} does not have a species parent. including alone")
                    super_kingdom_dict[taxid] = {
                        "temp_files": [file_name], "count": 1, "temp_size": size}
                # If there is a species parent and the tax id is already in the
                # dictionary
                elif species_parent.id in super_kingdom_dict:
                    if "files" in super_kingdom_dict[species_parent.id]:
                        super_kingdom_dict[species_parent.id]["count"] += 1
                    else:
                        super_kingdom_dict[species_parent.id]["count"] += 1
                        # super_kingdom_dict[species_parent.id]["temp_files"].append(file_name)
                        # super_kingdom_dict[species_parent.id]["temp_size"] += size
                # If there is a species parent and the tax id is not in the
                # dictionary
                else:
                    super_kingdom_dict[species_parent.id] = {
                        "count": 1, "temp_size": size, "temp_files": [file_name]}

            files_read += 1
            if files_read % 1000 == 0:
                logging.debug(f"{files_read} files processed")

    logging.info("Files read, sorting by counts")
    sorted_counts = {}
    for super_kingdom_dict, stats in species_counts.items():
        sorted_counts[super_kingdom_dict] = []
        for taxid, info in stats.items():
            if "files" not in info:
                sorted_counts[super_kingdom_dict].append(
                    (info["count"], info["temp_size"], info["temp_files"]))
            else:
                sorted_counts[super_kingdom_dict].append(
                    (info["count"], info["size"], info["files"]))
        sorted_counts[super_kingdom_dict] = sorted(
            sorted_counts[super_kingdom_dict], key=lambda x: x[0], reverse=True)

    logging.info("Sorted, finding subset")
    current_size = 0
    archaea_ratio, bacteria_ratio, viral_ratio = create_ratios(len(
        sorted_counts["Archaea"]), len(sorted_counts["Bacteria"]), len(sorted_counts["Viruses"]))
    archaea_sizes, bacteria_sizes, viral_sizes = list(map(
        lambda x: x[1], sorted_counts["Archaea"])), list(map(
            lambda x: x[1], sorted_counts["Bacteria"])), list(map(
                lambda x: x[1], sorted_counts["Viruses"]))
    curr_archaea, curr_bacteria, curr_viral = 0, 0, 0
    while current_size < args.size:
        curr_archaea += archaea_ratio
        curr_bacteria += bacteria_ratio
        curr_viral += viral_ratio
        current_size = sum(archaea_sizes[:round(curr_archaea)]) + sum(
            bacteria_sizes[:round(curr_bacteria)]) + sum(viral_sizes[:round(curr_viral)])

    for (_, _, files) in sorted_counts["Archaea"][:round(curr_archaea)]:
        for file in files:
            print(file)
    for (_, _, files) in sorted_counts["Bacteria"][:round(curr_bacteria)]:
        for file in files:
            print(file)
    for (_, _, files) in sorted_counts["Viruses"][:round(curr_viral)]:
        for file in files:
            print(file)
    logging.info("Done!")


if __name__ == '__main__':
    main()
