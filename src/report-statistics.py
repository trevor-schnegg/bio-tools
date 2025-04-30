import argparse
import logging
import sys

from taxonomy.taxonomy import Taxonomy


def get_readid2taxid(filename):
    readid2taxid = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip().split("\t")
            readid2taxid[line[0]] = int(line[1])
    return readid2taxid


def get_lineages_in_reference(filename, taxonomy, verbose):
    warned = False
    lineages = {}
    lineages[0] = (None, None)

    with open(filename, "r") as f:
        for line in f:
            ref_taxid = line.strip().split("\t")[1]

            # Find the species node
            species_node = taxonomy.parent(ref_taxid, at_rank="species")
            if species_node is None:
                # If no species node is found, log it then exit
                logging.error(
                    f"no species node found for reference tax id: {ref_taxid} - fix this and run again"
                )
                exit(1)

            # Find the genus node
            genus_node = taxonomy.parent(ref_taxid, at_rank="genus")
            if genus_node is None:
                # If no genus node is found, log appropriate messages
                if not warned and not verbose:
                    logging.warning("a tax id that did not have a genus node was found")
                    logging.info(
                        "provide option '-v' to log all tax ids without genus nodes"
                    )
                    warned = True
                elif verbose:
                    logging.warning(f"tax id {ref_taxid} has no genus node")

                # After logging, set the genus node to be the parent of the species node
                genus_node = taxonomy.node(species_node.parent)

            # Finally, add the lineages to the dictionary
            species_taxid = int(species_node.id)
            genus_taxid = int(genus_node.id)
            ref_taxid_int = int(ref_taxid)
            lineages[ref_taxid_int] = (genus_taxid, species_taxid)
            if ref_taxid_int != species_taxid:
                # The reference tax id isn't the same as the species tax id
                # It is likely at a lower level, so add the species tax id too
                lineages[species_taxid] = (genus_taxid, species_taxid)
            lineages[genus_taxid] = (genus_taxid, None)

    return lineages, warned


def get_lineage(taxid, taxonomy, verbose, warned):
    # Find the species node
    species_node = taxonomy.parent(taxid, at_rank="species")
    species_taxid = int(species_node.id) if species_node is not None else None

    # Find the genus node
    genus_node = taxonomy.parent(taxid, at_rank="genus")
    if genus_node is None:
        # If no genus node is found, log appropriate messages
        if not warned and not verbose:
            logging.warning("a tax id that did not have a genus node was found")
            logging.info("provide option '-v' to log all tax ids without genus nodes")
            warned = True
        elif verbose:
            logging.warning(f"tax id {taxid} has no genus node")

        # After logging, try to set the genus node to be the parent of the species node
        genus_node = (
            taxonomy.node(species_node.parent) if species_node is not None else None
        )
    genus_taxid = int(genus_node.id) if genus_node is not None else None

    return (genus_taxid, species_taxid), warned


def main():
    # Parse arguments from command line
    parser = argparse.ArgumentParser(
        description="Computes genus and species-level statistics for classifier's mapping. If this is the first classifier, run with options '-guic <CLASSIFIER_NAME> ...', otherwise run with '-uc <CLASSIFIER_NAME> ...'"
    )
    parser.add_argument(
        "-c",
        "--classifier-name",
        dest="classifier_name",
        default=None,
        help="The name of the classifier being evaluated",
    )
    parser.add_argument(
        "-g",
        "--give-formulas",
        dest="give_formulas",
        action="store_true",
        help="Prints the formulas used for precision, recall, and accuracy",
    )
    parser.add_argument(
        "-i",
        "--include-header",
        dest="include_header",
        action="store_true",
        help="Prints the header line before the output",
    )
    parser.add_argument(
        "-o",
        "--outside-reference",
        dest="outside_reference",
        action="store_true",
        help="Computes statistics only for reads outside the reference",
    )
    parser.add_argument(
        "-u",
        "--ignore-unclassified",
        dest="ignore_unclassified",
        action="store_true",
        help="Excludes unclassified ground truth reads",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Logs additional information about program execution",
    )
    parser.add_argument(
        "taxonomy", help="NCBI taxonomy directory (with names.dmp and nodes.dmp)"
    )
    parser.add_argument(
        "ground_truth_readid2taxid",
        help="Tab separated read id to tax id of minimap2 or other ground truth",
    )
    parser.add_argument(
        "predicted_readid2taxid",
        help="Tab separated read id to tax id of the classifier",
    )
    parser.add_argument(
        "reference_seqid2taxid", help="Tab separated seq id to tax id of the reference"
    )
    args = parser.parse_args()

    # Initialize event logger
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG,
        format="[%(asctime)s %(threadName)s %(levelname)s] %(message)s",
        datefmt="%m-%d-%Y %I:%M:%S%p",
    )

    # Read taxonomy
    logging.info(f"reading taxonomy from directory {args.taxonomy}...")
    taxonomy: Taxonomy = Taxonomy.from_ncbi(args.taxonomy)

    # Read both readid2taxids
    logging.info(
        f"reading ground truth readid2taxid from {args.ground_truth_readid2taxid}..."
    )
    ground_truth_readid2taxid = get_readid2taxid(args.ground_truth_readid2taxid)
    logging.info(
        f"reading predicted readid2taxid from {args.predicted_readid2taxid}..."
    )
    predicted_readid2taxid = get_readid2taxid(args.predicted_readid2taxid)

    logging.info("getting lineages from the reference...")
    reference_lineages, warned = get_lineages_in_reference(
        args.reference_seqid2taxid, taxonomy, args.verbose
    )

    # Compute the desired statistics for each tax id
    logging.info(f"computing statistics for {args.classifier_name}...")
    evaluation_levels = ("genus", "species")
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

    additional_lineages = {}

    for readid, true_taxid in ground_truth_readid2taxid.items():
        if true_taxid == 0 and args.ignore_unclassified:
            continue

        if args.outside_reference and true_taxid in reference_lineages:
            continue

        # Get ground truth lineage nodes
        true_lineage = (None, None)
        if true_taxid in reference_lineages:
            true_lineage = reference_lineages[true_taxid]
        elif true_taxid in additional_lineages:
            true_lineage = additional_lineages[true_taxid]
        else:
            true_lineage, warned = get_lineage(
                str(true_taxid), taxonomy, args.verbose, warned
            )
            additional_lineages[true_taxid] = true_lineage
            if true_taxid != true_lineage[1] and true_lineage[1] is not None:
                additional_lineages[(true_lineage[1])] = true_lineage
            if true_lineage[0] is not None:
                additional_lineages[true_lineage[0]] = (true_lineage[0], None)

        # # Test that the ground truth lineage doesn't have a None value
        # if true_lineage[0] is None or true_lineage[1] is None:
        #     logging.error(f"ground truth lineage was (genus, species): {true_lineage}")
        #     exit()

        # Get the predicted taxid
        predicted_taxid = (
            predicted_readid2taxid[readid] if readid in predicted_readid2taxid else 0
        )

        # Get the lineage nodes for the predicted taxid
        predicted_lineage = (None, None)
        if predicted_taxid in reference_lineages:
            predicted_lineage = reference_lineages[predicted_taxid]
        elif predicted_taxid in additional_lineages:
            predicted_lineage = additional_lineages[predicted_taxid]
        else:
            predicted_lineage, warned = get_lineage(
                str(predicted_taxid), taxonomy, args.verbose, warned
            )
            additional_lineages[predicted_taxid] = predicted_lineage
            if (
                predicted_taxid != predicted_lineage[1]
                and predicted_lineage[1] is not None
            ):
                additional_lineages[(predicted_lineage[1])] = predicted_lineage
            if predicted_lineage[0] is not None:
                additional_lineages[predicted_lineage[0]] = (predicted_lineage[0], None)

        # Increment the correct count based on the observed lineage
        for true_taxid, predicted_taxid, level in zip(
            true_lineage, predicted_lineage, evaluation_levels
        ):

            if true_taxid is None and predicted_taxid is None:
                stats[level + "_unclassified_tn"] += 1
            elif true_taxid is None and predicted_taxid is not None:
                stats[level + "_unclassified_fp"] += 1
            elif true_taxid is not None and predicted_taxid is None:
                if true_taxid in reference_lineages:
                    # Classifier could have made the correct assignment but failed to do so
                    stats[level + "_fn"] += 1
                else:
                    # Classifier could not have made the correct assignment
                    # and correctly abstained from making one
                    stats[level + "_not_in_ref_tn"] += 1
            else:
                # Both true tax id and predicted tax id are NOT 'None'
                if true_taxid in reference_lineages:
                    # Classifer could have made the correct assignment, check if it did
                    if true_taxid == predicted_taxid:
                        stats[level + "_tp"] += 1
                    else:
                        stats[level + "_fp"] += 1
                else:
                    # Classifier could not have made the correct assignment, but it made an assignment anyways
                    assert true_taxid != predicted_taxid
                    stats[level + "_not_in_ref_fp"] += 1

            # Increment the total count
            stats[level + "_total"] += 1

    # Some assertions for logic correctness
    if args.ignore_unclassified:
        for level in evaluation_levels:
            assert stats[level + "_unclassified_fp"] == 0
            assert stats[level + "_unclassified_tn"] == 0

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
    genus_fp = (
        stats["genus_fp"]
        + stats["genus_unclassified_fp"]
        + stats["genus_not_in_ref_fp"]
    )
    genus_tn = stats["genus_unclassified_tn"] + stats["genus_not_in_ref_tn"]

    species_tp, species_fn = stats["species_tp"], stats["species_fn"]
    species_fp = (
        stats["species_fp"]
        + stats["species_unclassified_fp"]
        + stats["species_not_in_ref_fp"]
    )
    species_tn = stats["species_unclassified_tn"] + stats["species_not_in_ref_tn"]

    try:
        genus_recall = (genus_tp / (genus_tp + genus_fn)) * 100
    except ZeroDivisionError:
        genus_recall = "undef"

    try:
        genus_precision = (genus_tp / (genus_tp + genus_fp)) * 100
    except ZeroDivisionError:
        genus_precision = "undef"

    try:
        genus_accuracy = (
            (genus_tp + genus_tn) / (genus_tp + genus_tn + genus_fn + genus_fp)
        ) * 100
    except ZeroDivisionError:
        genus_accuracy = "undef"

    try:
        species_recall = (species_tp / (species_tp + species_fn)) * 100
    except ZeroDivisionError:
        species_recall = "undef"

    try:
        species_precision = (species_tp / (species_tp + species_fp)) * 100
    except ZeroDivisionError:
        species_precision = "undef"

    try:
        species_accuracy = (
            (species_tp + species_tn)
            / (species_tp + species_tn + species_fn + species_fp)
        ) * 100
    except ZeroDivisionError:
        species_accuracy = "undef"

    if args.outside_reference and args.give_formulas:
        print(f"total outside reference reads: {stats['species_total']}\n")

    if args.include_header:
        print(
            "classifier\tgenus_recall\tgenus_precision\tgenus_accuracy\tspecies_recall\tspecies_precision\tspecies_accuracy\t"
            "genus_TP\tgenus_FP\tgenus_FN\tgenus_TN\tspecies_TP\tspecies_FP\tspecies_FN\tspecies_TN"
        )

    print_string += f"{genus_recall}\t{genus_precision}\t{genus_accuracy}\t{species_recall}\t{species_precision}\t{species_accuracy}\t"
    print_string += f"{genus_tp}\t{genus_fp}\t{genus_fn}\t{genus_tn}\t{species_tp}\t{species_fp}\t{species_fn}\t{species_tn}"
    print(print_string)

    logging.info("done reporting statistics!")


if __name__ == "__main__":
    main()
