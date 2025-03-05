import argparse
import logging
import sys

from taxonomy.taxonomy import Taxonomy


def get_readid2taxid(filename):
    readid2taxid = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip().split('\t')
            readid2taxid[line[0]] = int(line[1])
    return readid2taxid

def get_taxids_in_reference(filename, taxonomy, evaluation_levels):
    taxids = set()
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip().split('\t')
            for level in evaluation_levels:
                taxid = taxonomy.parent(line[1], at_rank=level)
                if taxid is not None:
                    taxids.add(taxid.id)
    return taxids

def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Takes a ground truth read id to tax id mapping and computes precision, recall, accuracy, etc. "
                    "of a classifier")
    parser.add_argument(
        "-g",
        "--give-formulas",
        dest="give_formulas",
        action="store_true",
        help="If specified, print the formulas used for precision, recall, and accuracy"
    )
    parser.add_argument(
        "-i",
        "--include-header",
        dest="include_header",
        action="store_true",
        help="Prints the header line before the output")
    parser.add_argument(
        "-u",
        "--ignore-unclassified",
        dest="ignore_unclassified",
        action="store_true",
        help="Include this option if you want to exclude reads unclassified by the ground truth")
    parser.add_argument(
        "-c",
        "--classifier-name",
        dest="classifier_name",
        default=None,
        help="The name of the classifier whose accuracy is being evaluated")
    parser.add_argument(
        "taxonomy",
        help="NCBI taxonomy directory")
    parser.add_argument(
        "ground_truth_readid2taxid",
        help="Tab separated read id to tax id of bwa-mem or other ground truth")
    parser.add_argument(
        "predicted_readid2taxid",
        help="Tab separated read id to tax id of the classifier")
    parser.add_argument(
        "reference_seqid2taxid",
        help="Tab separated seqid to taxid of the reference")
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

    evaluation_levels = ["genus", "species"]

    # Read taxonomy
    logging.info(f"Reading taxonomy from directory {args.taxonomy}")
    taxonomy: Taxonomy = Taxonomy.from_ncbi(args.taxonomy)

    logging.info(
        f"Reading ground truth readid2taxid from {args.ground_truth_readid2taxid}")
    # Read both readid2taxids
    ground_truth_readid2taxid = get_readid2taxid(
        args.ground_truth_readid2taxid)
    logging.info(
        f"Reading predicted readid2taxid from {args.predicted_readid2taxid}")
    predicted_readid2taxid = get_readid2taxid(args.predicted_readid2taxid)
    logging.info("Both readid2taxids read!")

    logging.info("Reading taxids from the reference")
    reference_taxids = get_taxids_in_reference(args.reference_seqid2taxid, taxonomy, evaluation_levels)
    logging.info("Reference taxids obtained!")

    # Compute the desired statistics for each tax id
    logging.info(f"Computing statistics for {args.classifier_name}, this takes about 15 seconds max...")
    stats = {}
    for level in evaluation_levels:
        stats[level + "_total"] = 0
        stats[level + "_tp"] = 0
        stats[level + "_fp"] = 0
        stats[level + "_fn"] = 0
        stats[level + "_unclassified_tn"] = 0
        stats[level + "_unclassified_fp"] = 0
        stats[level + "_not_in_ref_fp"] = 0
        stats[level + "_not_in_ref_tn"] = 0

    cache = {}

    for readid, true_taxid in ground_truth_readid2taxid.items():
        if true_taxid == 0 and args.ignore_unclassified:
            continue

        # Get ground truth lineage nodes
        true_lineage = []
        if true_taxid in cache:
            true_lineage = cache[true_taxid]
        else:
            for tax_level in evaluation_levels:
                true_lineage.append(
                    taxonomy.parent(
                        str(true_taxid),
                        at_rank=tax_level))
            cache[true_taxid] = true_lineage

        # Get the predicted taxid
        predicted_taxid = predicted_readid2taxid[readid] if readid in predicted_readid2taxid else 0

        # Get the lineage nodes for the predicted taxid
        predicted_lineage = []
        if predicted_taxid in cache:
            predicted_lineage = cache[predicted_taxid]
        else:
            for tax_level in evaluation_levels:
                predicted_lineage.append(
                    taxonomy.parent(
                        str(predicted_taxid),
                        at_rank=tax_level))
            cache[predicted_taxid] = predicted_lineage

        # Increment the correct count based on the observed lineage
        for true_node, predicted_node, level in zip(
                true_lineage, predicted_lineage, evaluation_levels):

            if true_node is None and predicted_node is None:
                stats[level + "_unclassified_tn"] += 1
            elif true_node is None and predicted_node is not None:
                stats[level + "_unclassified_fp"] += 1
            elif true_node is not None and predicted_node is None:
                if true_node.id in reference_taxids:
                    # Classifier could have made the correct assignment but failed to do so
                    stats[level + "_fn"] += 1
                else:
                    # Classifier could not have made the correct assignment
                    # and correctly abstained from making one
                    stats[level + "_not_in_ref_tn"] += 1
            else:
                # Both true node and predicted node are NOT 'None'
                if true_node.id in reference_taxids:
                    # Classifer could have made the correct assignment, check if it did
                    if true_node.id == predicted_node.id:
                        stats[level + "_tp"] += 1
                    else:
                        stats[level + "_fp"] += 1
                else:
                    # Classifier could not have made the correct assignment, but it made an assignment anyways
                    assert true_node.id != predicted_node.id
                    stats[level + "_not_in_ref_fp"] += 1

            # Increment the total count
            stats[level + "_total"] += 1

    if args.ignore_unclassified:
        taxonomy_issue_detected = False
        if stats["genus_unclassified_fp"] > 0 or stats["genus_unclassified_tn"] > 0:
            taxonomy_issue_detected = True
        if stats["species_unclassified_fp"] > 0 or stats["species_unclassified_tn"] > 0:
            taxonomy_issue_detected = True

        if taxonomy_issue_detected:
            # Log issue if there was one
            logging.warning("Argument to ignore unclassified reads provided, but None values were detected in the ground truth")
            logging.warning("There is likely an issue with the taxonomy or the ground truth read assignments")

    # Print formulas if needed
    if args.give_formulas:
        print("TP = True Positives, FP = False Positives, FN = False Negatives")
        print("precision = TP / (TP + FP)")
        print("recall = TP / (TP + FN)")
        print("accuracy = (TP + TN) / (TP + FP + FN + TN)\n")

    print_string = ""
    # Print statistics
    if args.classifier_name is not None:
        print_string += f"{args.classifier_name}\t"
    else:
        print_string += "<No name provided>\t"

    genus_tp, genus_fn = stats["genus_tp"], stats["genus_fn"]
    genus_fp = stats["genus_fp"] + stats["genus_unclassified_fp"] + stats["genus_not_in_ref_fp"]
    genus_tn = stats["genus_unclassified_tn"] + stats["genus_not_in_ref_tn"]
    species_tp, species_fn = stats["species_tp"], stats["species_fn"]
    species_fp = stats["species_fp"] + stats["species_unclassified_fp"] + stats["species_not_in_ref_fp"]
    species_tn = stats["species_unclassified_tn"] + stats["species_not_in_ref_tn"]

    genus_recall = (genus_tp/(genus_tp+genus_fn)) * 100
    genus_precision = (genus_tp/(genus_tp+genus_fp)) * 100
    genus_accuracy = ((genus_tp+genus_tn)/(genus_tp+genus_tn+genus_fn+genus_fp)) * 100

    species_recall = (species_tp/(species_tp+species_fn)) * 100
    species_precision = (species_tp/(species_tp+species_fp)) * 100
    species_accuracy = ((species_tp+species_tn)/(species_tp+species_tn+species_fn+species_fp)) * 100

    if args.include_header:
        print("classifier\tgenus_recall\tgenus_precision\tgenus_accuracy\tspecies_recall\tspecies_precision\tspecies_accuracy\t"
              "genus_TP\tgenus_FP\tgenus_FN\tgenus_TN\tspecies_TP\tspecies_FP\tspecies_FN\tspecies_TN")

    print_string += f"{genus_recall}\t{genus_precision}\t{genus_accuracy}\t{species_recall}\t{species_precision}\t{species_accuracy}\t"
    print_string += f"{genus_tp}\t{genus_fp}\t{genus_fn}\t{genus_tn}\t{species_tp}\t{species_fp}\t{species_fn}\t{species_tn}"
    print(print_string)

    logging.info("Done reporting statistics!")


if __name__ == '__main__':
    main()
