import argparse
import logging
import sys

from taxonomy.taxonomy import Taxonomy


def get_readid2taxid(filename):
    readid2taxid = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.strip().split('\t')
            readid2taxid[line[0]] = int(line[1])
    return readid2taxid


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
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format='[%(asctime)s %(threadName)s %(levelname)s] %(message)s',
        datefmt='%m-%d-%Y %I:%M:%S%p')

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

    # Compute the desired statistics for each tax id
    logging.info("Computing statistics, this usually takes about 15 seconds...")
    evaluation_levels = ["genus", "species"]
    stats = {
        "yeast_tn": 0,
        "yeast_fp": 0,
        "unclassified_fp": 0,
        "unclassified_tn": 0}
    for level in evaluation_levels:
        stats[level + "_total"] = 0
        stats[level + "_tp"] = 0
        stats[level + "_fp"] = 0
        stats[level + "_fn"] = 0

    for readid, taxid in ground_truth_readid2taxid.items():
        # If the ground truth tax id is 0, the read was unclassified according
        # to minimap2
        if taxid == 0:
            # Get the predicted tax id
            prediction = predicted_readid2taxid[readid] if readid in predicted_readid2taxid else 0
            if prediction == 0:
                stats["unclassified_tn"] += 1
            else:
                stats["unclassified_fp"] += 1

        # If the ground truth tax id value is either of the two yeast tax ids
        elif taxid == 5207 or taxid == 4932:
            # Get the predicted tax id
            prediction = predicted_readid2taxid[readid] if readid in predicted_readid2taxid else 0
            if prediction == 0:
                stats["yeast_tn"] += 1
            else:
                stats["yeast_fp"] += 1

        else:
            # Get ground truth value and lineage
            ground_truth = taxid
            ground_truth_lineage = []
            for tax_level in evaluation_levels:
                ground_truth_lineage.append(
                    taxonomy.parent(
                        str(ground_truth),
                        at_rank=tax_level))

            # Increment the ground truth total numbers immediately
            for node in ground_truth_lineage:
                if node is not None:
                    stats[node.rank + "_total"] += 1

            # Get the predicted tax id
            prediction = predicted_readid2taxid[readid] if readid in predicted_readid2taxid else 0

            # If the predicted tax id is 0, it has no lineage and will throw an error
            # Therefore, increment false negative counts and continue
            if prediction == 0:
                for node in ground_truth_lineage:
                    if node is not None:
                        stats[node.rank + "_fn"] += 1
                continue

            # Get the lineage for the predicted tax id
            prediction_lineage = []
            for tax_level in evaluation_levels:
                prediction_lineage.append(
                    taxonomy.parent(
                        str(prediction),
                        at_rank=tax_level))

            # Ignores classifier assignments that are more specific than the
            # ground truth
            for true_node, predicted_node in zip(
                    ground_truth_lineage, prediction_lineage):
                if true_node is None:
                    continue
                else:
                    if predicted_node is None:
                        stats[true_node.rank + "_fn"] += 1
                    else:
                        assert true_node.rank == predicted_node.rank
                        if true_node.id == predicted_node.id:
                            stats[true_node.rank + "_tp"] += 1
                        else:
                            stats[true_node.rank + "_fp"] += 1

    # Print formulas if needed
    if args.give_formulas:
        print("TP = True Positives, FP = False Positives, FN = False Negatives")
        print("precision = TP / (TP + FP)")
        print("recall = TP / (TP + FN)")
        print("accuracy = TP / (TP + FP + FN + TN)\n")

    statistics = ["precision", "recall", "accuracy"]
    # Print header line if required
    if args.include_header:
        print("Output is formatted in the following manner:\n")
        print("<Classifier Name>")
        print("genus_TP\tgenus_FN\tgenus_recall\t\tspecies_TP\tspecies_FN\tspecies_recall")
        print("genus_FP\tgenus_TN\t\t\tspecies_FP\tspecies_TN")
        print(
            "genus_precision\t\tgenus_accuracy\t\tspecies_precision\t\tspecies_accuracy\n")

    # Print statistics
    if args.classifier_name is not None:
        print(args.classifier_name)
    else:
        print("<No classifier name provided>")

    genus_tp, genus_fn, genus_fp, genus_tn = stats["genus_tp"], stats["genus_fn"], str(
        stats['genus_fp']), ""
    species_tp, species_fn, species_fp, species_tn = stats["species_tp"], stats["species_fn"], str(
        stats['species_fp']), ""

    if args.ignore_unclassified:
        genus_fp += ("+" + str(stats["yeast_fp"]))
        genus_tn += str(stats["yeast_tn"])
        species_fp += ("+" + str(stats["yeast_fp"]))
        species_tn += str(stats["yeast_tn"])
    else:
        genus_fp += ("+" + str(stats["yeast_fp"]) + "+" + str(stats["unclassified_fp"]))
        genus_tn += (str(stats["yeast_tn"]) + "+" + str(stats["unclassified_tn"]))
        species_fp += ("+" + str(stats["yeast_fp"]) + "+" + str(stats["unclassified_fp"]))
        species_tn += (str(stats["yeast_tn"]) + "+" + str(stats["unclassified_tn"]))

    print(
        f"{str(genus_tp)}\t{str(genus_fn)}\t{str(genus_tp/(genus_tp+genus_fn))}\t\t{str(species_tp)}\t{str(species_fn)}\t{str(species_tp/(species_tp+species_fn))}")
    print(f"{genus_fp}\t{genus_tn}\t\t\t{species_fp}\t{species_tn}")
    print(
        f"{str(genus_tp/(genus_tp+eval(genus_fp)))}"
        f"\t\t{str((genus_tp+eval(genus_tn))/(genus_tp+eval(genus_tn)+genus_fn+eval(genus_fp)))}"
        f"\t\t{str(species_tp/(species_tp+eval(species_fp)))}"
        f"\t\t{str((species_tp+eval(species_tn))/(species_tp+eval(species_tn)+species_fn+eval(species_fp)))}\n")

    logging.info("Done reporting statistics!")


if __name__ == '__main__':
    main()
