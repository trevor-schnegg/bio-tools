import argparse
import logging
import sys

import pandas as pd
from taxonomy.taxonomy import Taxonomy


def get_taxid_of_readid(dataframe: pd.DataFrame, readid: str):
    try:
        taxid = dataframe.loc[dataframe["readid"] == readid]["taxid"].values[0]
    except IndexError:
        return 0
    else:
        return taxid


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
    logging.info("Taxonomy read!")

    logging.info(
        f"Reading ground_truth_readid2taxid at {args.ground_truth_readid2taxid}")
    # Read both readid2taxids
    ground_truth_readid2taxid = pd.read_table(
        args.ground_truth_readid2taxid,
        names=["readid", "taxid"],
        dtype={
            'readid': 'string',
            'taxid': 'int'})
    logging.info(
        f"Reading predicted_readid2taxid at {args.predicted_readid2taxid}")
    predicted_readid2taxid = pd.read_table(
        args.predicted_readid2taxid,
        names=["readid", "taxid"],
        dtype={
            'readid': 'string',
            'taxid': 'int'})
    logging.info("Both readid2taxids read!")

    # Compute the desired statistics for each tax id
    logging.info("Computing statistics")
    evaluation_levels = ["genus", "species"]
    stats = {}
    for level in evaluation_levels:
        stats[level + "_total"] = 0
        stats[level + "_tp"] = 0
        stats[level + "_fp"] = 0
        stats[level + "_fn"] = 0
    for _, values in ground_truth_readid2taxid.iterrows():
        if values["taxid"] == 0:
            # If the tax id of the ground truth is 0, ignore this read
            continue
        else:
            # Get ground truth value and lineage
            ground_truth = values["taxid"]
            ground_truth_lineage = list(
                filter(
                    lambda x: True if x.rank in evaluation_levels else False,
                    taxonomy.lineage(
                        str(ground_truth))))
            ground_truth_lineage.reverse()

            # Increment the ground truth total numbers immediately
            for node in ground_truth_lineage:
                stats[node.rank + "_total"] += 1

            # Get the predicted tax id
            prediction = get_taxid_of_readid(
                predicted_readid2taxid, values["readid"])

            # If the predicted tax id is 0, it has no lineage and will throw an error
            # Therefore, increment false negative counts and continue
            if prediction == 0:
                for node in ground_truth_lineage:
                    stats[node.rank + "_fn"] += 1
                continue

            # Get the lineage for the predicted tax id
            prediction_lineage = list(
                filter(
                    lambda x: True if x.rank in evaluation_levels else False,
                    taxonomy.lineage(
                        str(prediction))))
            prediction_lineage.reverse()

            # Ignores classifier assignments that are more specific than the
            # ground truth
            is_predicted_shorter = False
            for index, true_node in enumerate(ground_truth_lineage):
                try:
                    if is_predicted_shorter:
                        stats[true_node.rank + "_fn"] += 1
                        continue
                    predicted_node = prediction_lineage[index]
                except IndexError:
                    is_predicted_shorter = True
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
        print("accuracy = TP / (TP + FP + FN)\n")

    statistics = ["precision", "recall", "accuracy"]
    # Print header line if required
    if args.include_header:
        header_string = ""
        if args.classifier_name is not None:
            header_string = "classifier"
        for stat in statistics:
            for level in evaluation_levels:
                header_string += f"\t{level + '_' + stat}"
        print(header_string.strip())

    # Print statistics
    report_string = ""
    if args.classifier_name is not None:
        report_string = args.classifier_name
    for stat in statistics:
        for level in evaluation_levels:
            total = stats[level + "_total"]
            true_postives = stats[level + "_tp"]
            if stat == "precision":
                report_string += f'\t{true_postives/(true_postives + stats[level + "_fp"])}'
            elif stat == "recall":
                report_string += f'\t{true_postives/(true_postives + stats[level + "_fn"])}'
            elif stat == "accuracy":
                report_string += f'\t{true_postives / (true_postives + stats[level + "_fp"] + stats[level + "_fn"])}'
    print(report_string.strip())


if __name__ == '__main__':
    main()
