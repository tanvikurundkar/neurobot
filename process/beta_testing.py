import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report


CSV_PATH = "./data/emotions.csv"
OUTPUT_DIR = "./data/emotions_out"
LABEL_COL = "label"
SEED = 42


# load and tidy the csv
def load_data(path):
    df = pd.read_csv(path)
    # first header comes in as "# mean_0_a" - strip the "# "
    df.columns = [c.lstrip("# ").strip() for c in df.columns]
    y = df[LABEL_COL].values
    X = df.drop(columns=[LABEL_COL])
    print("rows: " + str(X.shape[0]) + ", features: " + str(X.shape[1]))
    print(pd.Series(y).value_counts().to_string())
    return X, y


# group features by type, e.g. fft_12_a -> fft_#_a
def feature_group(name):
    return re.sub(r"\d+", "#", name)


# 2d maps of the feature space colored by emotion label
def plot_maps(X_scaled, y, out_dir):
    pca = PCA(n_components=2, random_state=SEED)
    p = pca.fit_transform(X_scaled)
    print("PCA variance explained: " + str(np.round(pca.explained_variance_ratio_, 3)))

    # reduce first so t-sne is fast and less noisy
    reduced = PCA(n_components=50, random_state=SEED).fit_transform(X_scaled)
    t = TSNE(n_components=2, perplexity=30, random_state=SEED).fit_transform(reduced)

    colors = {"NEGATIVE": "tab:red", "NEUTRAL": "tab:gray", "POSITIVE": "tab:green"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, emb, title in [(axes[0], p, "PCA"), (axes[1], t, "t-SNE")]:
        for lab, col in colors.items():
            m = y == lab
            ax.scatter(emb[m, 0], emb[m, 1], s=8, alpha=0.6, c=col, label=lab)
        ax.set_title(title + " of EEG features")
    axes[0].legend()
    path = os.path.join(out_dir, "emotion_map.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("saved " + path)


# which feature types matter most (importances summed per group)
def plot_group_importance(X, y, out_dir):
    rf = RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1)
    rf.fit(X, y)
    imp = pd.Series(rf.feature_importances_, index=X.columns)
    groups = imp.groupby([feature_group(c) for c in imp.index]).sum()
    top = groups.sort_values(ascending=False).head(15)

    fig, ax = plt.subplots(figsize=(8, 6))
    top[::-1].plot.barh(ax=ax)
    ax.set_xlabel("summed importance")
    ax.set_title("top feature groups")
    path = os.path.join(out_dir, "feature_group_importance.png")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print("saved " + path)


# cross-validated classification + confusion matrix
# NOTE: rows are shuffled and likely overlapping windows from the same recording,
# so random folds can leak and look better than they would on a new person/session
def run_classifier(X, y, out_dir):
    rf = RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    pred = cross_val_predict(rf, X, y, cv=cv)

    print(classification_report(y, pred))
    labels = ["NEGATIVE", "NEUTRAL", "POSITIVE"]
    cm = confusion_matrix(y, pred, labels=labels)
    disp = ConfusionMatrixDisplay(cm, display_labels=labels)
    disp.plot(cmap="Blues")
    path = os.path.join(out_dir, "confusion_matrix.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print("saved " + path)


# main
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    X, y = load_data(CSV_PATH)
    X_scaled = StandardScaler().fit_transform(X)

    plot_maps(X_scaled, y, OUTPUT_DIR)
    plot_group_importance(X, y, OUTPUT_DIR)
    run_classifier(X, y, OUTPUT_DIR)

    print("\nall done! files saved to: " + OUTPUT_DIR)