import keras
import numpy as np

import pandas as pd
from prophecy.data.objects import Predictions


def get_eval_labels(model: keras.Model, features: pd.DataFrame, split_name: str):
    """
        Evaluate the model on the given features and labels
    :param model: The model to evaluate
    :param features: The features to evaluate on
    :param split_name: The split name
    :return: labels
    """

    labels = []
    confidence = []

    predictions = model.predict(features)
    # check if the model is binary classification
    if len(predictions[0]) == 1:
        cnt_0 = 0
        cnt_1 = 1
        for i in range(0, len(predictions)):
            confidence.append(np.abs(predictions[i][0] - 0.5))
            if predictions[i][0] > 0.5:
                cnt_1 = cnt_1 + 1
                labels.append(1)
            else:
                cnt_0 = cnt_0 + 1
                labels.append(0)

        print(f"{split_name.upper()}: Label 0:", cnt_0, "Label 1:", cnt_1)
    else:
        # perform multi-class classification
        for i in range(0, len(predictions)):
            labels.append(np.argmax(predictions[i]))
            # get confidence by getting the difference between the highest and second-highest value
            confidence.append(np.max(predictions[i]) - np.partition(predictions[i], -2)[-2])

        # get labels count
        unique, counts = np.unique(labels, return_counts=True)
        counts_str = f"{split_name.upper()}: "

        for i in range(0, len(unique)):
            counts_str += f"Label {unique[i]}: {counts[i]}, "
        print(counts_str)

    return np.array(labels), confidence


def predict_unseen(model: keras.Model, features: pd.DataFrame, labels: np.ndarray) -> Predictions:
    unseen_ops = model.predict(features)
    predictions = Predictions()

    if len(unseen_ops[0]) == 1:
        cnt_0 = 0
        # TODO: why this count is set to one?
        cnt_1 = 1

        for i in range(0, len(unseen_ops)):
            if unseen_ops[i][0] > 0.5:
                cnt_1 += + 1
                predictions.labels.append(1)

                if labels[i] == 1:
                    predictions.correct += 1
                else:
                    predictions.incorrect += 1
            else:
                cnt_0 += 1
                predictions.labels.append(0)
                if labels[i] == 0:
                    predictions.correct += 1
                else:
                    predictions.incorrect += 1

        print("UNSEEN: Label 0:", cnt_0, "Label 1:", cnt_1)
        print("UNSEEN: ACT CORR:", predictions.correct, ", ACT INCORR:", predictions.incorrect)
    else:
        # perform multi-class classification
        for i in range(0, len(unseen_ops)):
            prediction = np.argmax(unseen_ops[i])
            predictions.labels.append(prediction)

            if labels[i] == prediction:
                predictions.correct += 1
            else:
                predictions.incorrect += 1

        # get labels count
        unique, counts = np.unique(predictions.labels, return_counts=True)
        counts_str = "UNSEEN: "
        for i in range(0, len(unique)):
            counts_str += f"Label {unique[i]}: {counts[i]}, "
        print(counts_str)
        print("UNSEEN: ACT CORR:", predictions.correct, ", ACT INCORR:", predictions.incorrect)

    return predictions
