import argparse

from prophecy.data.dataset import Dataset
from prophecy.utils.misc import get_model
from prophecy.core.extract import get_model_fingerprints, extract_rules
from prophecy.core.learn import learn_val_rules, learn_act_rules


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Infer Data Precondition')
    parser.add_argument('--model', type=str, help='Model to infer the precondition', required=True,
                        choices=['PD'])
    parser.add_argument('--version', type=int, help='Version of the model', required=True)
    parser.add_argument('--dataset', type=str, help='target dataset', required=True, choices=['PD'])
    parser.add_argument('--split', type=str, help='Dataset split', required=True,
                        choices=['train', 'val', 'unseen'])
    args = parser.parse_args()
    
    model = get_model(args.model, args.version)
    dataset = Dataset(args.dataset)

    accuracy_labels, decision_labels = extract_rules(model, dataset, 'train')
    fingerprints = get_model_fingerprints(model, dataset, 'train')

    print("DECISION RULES:")
    print("Invoking Dec-tree classifier based on INPUT FEATURES.")
    learn_val_rules(decision_labels, dataset)

    print("CORRECT/INCORRECT RULES:")
    print("Invoking Dec-tree classifier based on neuron values.")
    learn_val_rules(accuracy_labels, dataset)

    print("DECISION RULES:")
    learn_act_rules(decision_labels, fingerprints)

    print("CORRECT/INCORRECT RULES:")
    learn_act_rules(accuracy_labels, fingerprints)
