import argparse
import logging
import sys


def get_seqid2taxid(filename, columns=None):
    readid2taxid = {}
    with open(filename, "r") as f:
        for line in f.readlines():
            line = line.strip().split("\t")
            if columns is None:
                readid2taxid[line[0]] = int(line[1])
            else:
                readid2taxid[line[columns[0]]] = int(line[columns[1]])
    return readid2taxid


def get_krakenuniq_taxid2taxid(filename):
    krakenuniq_seq2taxid = get_seqid2taxid(filename)
    seqid2taxid = get_seqid2taxid(filename + ".orig")
    taxid2taxid = {}
    for seqid, taxid in krakenuniq_seq2taxid.items():
        real_taxid = seqid2taxid[seqid]
        taxid2taxid[taxid] = real_taxid
    return taxid2taxid


def get_kasa_taxid2taxid(ref_content, seqid2taxid):
    kasa_readid2taxid = get_seqid2taxid(ref_content, (3, 2))
    seqid2taxid = get_seqid2taxid(seqid2taxid)
    taxid2taxid = {}
    for seqid, taxid in kasa_readid2taxid.items():
        real_taxid = seqid2taxid[seqid]
        taxid2taxid[taxid] = real_taxid
    return taxid2taxid


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(description="Outputs a tsv of the input columns")
    parser.add_argument(
        "-c",
        "--clark",
        dest="clark",
        action="store_true",
        help="If the read id to tax id is CLARK, we need to replace NA with 0",
    )
    parser.add_argument(
        "-u",
        "--krakenuniq",
        dest="krakenuniq_map",
        default=None,
        help="The seqid2taxid.map file provided by krakenuniq and the accession2taxid mapping for the dataset",
    )
    parser.add_argument(
        "-k",
        "--kasa",
        dest="kasa_map_and_seqid2taxid",
        default=None,
        help="<ref_content.txt>,<seqid2taxid> -- ref_content.txt provided by kASA's database",
    )
    parser.add_argument("file", help="read id to tax id file to reformat")
    args = parser.parse_args()
    krakenuniq_taxid2taxid = (
        None
        if args.krakenuniq_map is None
        else get_krakenuniq_taxid2taxid(args.krakenuniq_map)
    )
    kasa_files = None
    if args.kasa_map_and_seqid2taxid is not None:
        split_files = list(args.kasa_map_and_seqid2taxid.split(","))
        kasa_files = (split_files[0], split_files[1])
    kasa_taxid2taxid = (
        None
        if args.kasa_map_and_seqid2taxid is None
        else get_kasa_taxid2taxid(kasa_files[0], kasa_files[1])
    )

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Read the TSV/CSV
    logging.info(f"Reformatting {args.file}")

    with open(args.file, "r") as f:
        for line in f.readlines():
            line = list(line.strip().split("\t"))
            readid = line[0]
            value = line[1]
            if args.clark and value == "NA":
                value = "0"
            elif krakenuniq_taxid2taxid is not None:
                value = int(value)
                if value > 1000000000:
                    value = krakenuniq_taxid2taxid[value]
                value = str(value)
            elif kasa_taxid2taxid is not None:
                value = int(value)
                value = str(kasa_taxid2taxid[value])
            print(f"{readid}\t{value}")

    logging.info("Done reformatting!")


if __name__ == "__main__":
    main()
