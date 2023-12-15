import argparse
import pandas as pd

from prophecy.data.dataset import Dataset
from prophecy.utils.misc import lookup_models, get_model, lookup_settings, load_settings, lookup_datasets
from prophecy.core.extract import RuleExtractor
from prophecy.core.detect import Detector
from prophecy.utils.paths import results_path

SETTINGS = lookup_settings()
MODELS = lookup_models()
model_choices = sorted(list(MODELS.keys()))
DATASETS = lookup_datasets()
dataset_choices = sorted(list(DATASETS.keys()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Infer Data Precondition')
    parser.add_argument('--model', type=str, help='Model to infer the precondition', required=True,
                        choices=model_choices)
    parser.add_argument('--dataset', type=str, help='target dataset', required=True,
                        choices=dataset_choices)
    parser.add_argument('--settings', type=str, help='settings', required=True, choices=SETTINGS.keys())

    subparsers = parser.add_subparsers(dest='subparser')
    detect_parser = subparsers.add_parser('detect')
    detect_parser.add_argument('-t', '--threshold', type=float, help='rule F1-threshold', default=0.0)
    detect_parser.add_argument('-bf', '--brute-force', action='store_true', default=False,
                               help='try all possible combinations of layers')

    extract_parser = subparsers.add_parser('extract')

    args = parser.parse_args()

    # check if model name is equal to the dataset name
    if args.model[:-1] != args.dataset:
        print(f"Model ({args.model}) must match dataset ({args.dataset}).")
        exit()

    model = get_model(MODELS[args.model])
    dataset = Dataset(args.dataset)
    settings = load_settings(SETTINGS[args.settings])

    base_path = results_path / args.model
    rules_path = base_path / "rules" / settings.rules / settings.fingerprint
    rules_path.mkdir(parents=True, exist_ok=True)
    predictions_path = base_path / "predictions" / settings.rules / settings.fingerprint
    predictions_path.mkdir(parents=True, exist_ok=True)

    if args.subparser == 'extract':
        rule_extractor = RuleExtractor(model=model, dataset=dataset, settings=settings)
        ruleset = rule_extractor()

        for layer, rules in ruleset.items():
            df = pd.DataFrame(rules)

            if len(df) == 0:
                continue

            df.to_csv(rules_path / f'{layer}.csv', index=False)

    elif args.subparser == 'detect':
        results = []
        output_path = predictions_path / ('results_bf.csv' if args.brute_force else f'results.csv')
        detector = Detector(model=model, dataset=dataset)

        dfs = []
        for f in rules_path.iterdir():
            if f.is_file() and f.suffix == '.csv':
                layer = f.stem
                rules = pd.read_csv(f)
                rules['layer_count'] = rules['layer']
                rules['layer'] = layer
                dfs.append(rules)

        ruleset = pd.concat(dfs)
        ruleset = ruleset[ruleset['f1'] >= args.threshold]

        if args.brute_force:
            layers = sorted(ruleset['layer_count'].unique())
            # get all combination of layers
            from itertools import combinations
            for i in range(1, len(layers)+1):
                for comb in combinations(layers, i):
                    print(f"Running detector for layers combination: {comb}")
                    outcome = detector(ruleset=ruleset[ruleset['layer_count'].isin(comb)])
                    outcome['layers'] = '_'.join(str(c) for c in comb)
                    results.append(outcome)
        else:
            results.append(detector(ruleset=ruleset))

        pd.DataFrame(results).to_csv(output_path, index=False)
    else:
        print("Please specify a command ['extract', 'detect'].")
        exit()
