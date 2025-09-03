import argparse
import logging
import sys

from taxonomy.taxonomy import Taxonomy


def count_leaf_nodes_below(taxonomy, node, level):
    leaf_nodes_below = 0
    children = taxonomy.children(node.id)
    if children:
        # "if children" returns true if the list is non-empty
        for child in children:
            leaf_nodes_below += count_leaf_nodes_below(taxonomy, child, level)
    else:
        # otherwise the list is empty and this is a leaf node
        return 1

    if node.rank == level:
        print(f"{node.id}\t{str(leaf_nodes_below)}")

    return leaf_nodes_below


def main():

    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Counts nodes below the given tax level"
    )
    parser.add_argument("level", help="NCBI taxonomy level to print")
    parser.add_argument("taxonomy", help="NCBI taxonomy directory")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Read taxonomy
    logging.info(f"Reading taxonomy from directory {args.taxonomy}")
    taxonomy = Taxonomy.from_ncbi(args.taxonomy)
    logging.info("Taxonomy read!")

    count_leaf_nodes_below(taxonomy, taxonomy.root, args.level)

    logging.info("Done!")


if __name__ == "__main__":
    main()
