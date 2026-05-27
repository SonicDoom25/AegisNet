import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold
import joblib
import os
import glob
import numpy as np
import logging
from datetime import datetime

DATA_PATH = "../data/"
MODEL_DIR = "../models/"

logging.basicConfig(level=logging.INFO)

def load_data():
    files = glob.glob(DATA_PATH + "*.parquet")
    dfs = []

    for file in files:
        logging.info(f"Loading {file}")
        df = pd.read_parquet(file)

        if "Benign" in file:
            df["Label"] = 0
        else:
            df["Label"] = 1

        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    logging.info(f"Total rows: {len(df)}")
    return df


def preprocess(df):

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    X = df.drop("Label", axis=1)
    y = df["Label"]

    feature_names = X.columns.tolist()

    X = X.astype("float32")

    selector = VarianceThreshold(threshold=0.0001)
    X = selector.fit_transform(X)

    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    return X, y, selector, scaler, feature_names


def hyperparameter_search(X_train, y_train):

    model = lgb.LGBMClassifier(
        n_jobs=-1,
        class_weight={0:1, 1:2}
    )

    param_dist = {
        "n_estimators": [500, 700, 900],
        "learning_rate": [0.01, 0.03, 0.05],
        "num_leaves": [128, 256],
        "max_depth": [10, 20],
        "min_child_samples": [20, 50]
    }

    search = RandomizedSearchCV(
        model,
        param_distributions=param_dist,
        n_iter=12,
        scoring="f1",
        cv=3,
        verbose=1,
        n_jobs=-1
    )

    search.fit(X_train, y_train)

    logging.info(f"Best Parameters: {search.best_params_}")
    return search.best_estimator_


def find_best_threshold(y_true, y_probs):

    best_threshold = 0.5
    best_f1 = 0

    for t in np.arange(0.1, 0.9, 0.05):
        preds = (y_probs >= t).astype(int)
        score = f1_score(y_true, preds)

        if score > best_f1:
            best_f1 = score
            best_threshold = t

    logging.info(f"Best Threshold: {best_threshold} | F1: {best_f1}")
    return best_threshold


def train():

    df = load_data()

    X, y, selector, scaler, feature_names = preprocess(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    best_model = hyperparameter_search(X_train, y_train)

    y_probs = best_model.predict_proba(X_test)[:,1]
    threshold = find_best_threshold(y_test, y_probs)

    y_pred = (y_probs >= threshold).astype(int)

    print("\nFinal Report:")
    print(classification_report(y_test, y_pred))

    os.makedirs(MODEL_DIR, exist_ok=True)

    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = f"{MODEL_DIR}aegisnet_binary_{version}.pkl"

    joblib.dump({
        "model": best_model,
        "threshold": threshold,
        "selector": selector,
        "scaler": scaler,
        "features": feature_names,
        "version": version,
        "metrics": {
            "f1": float(f1_score(y_test, y_pred))
        }
    }, model_path)

    logging.info(f"Model saved: {model_path}")


if __name__ == "__main__":
    train()
