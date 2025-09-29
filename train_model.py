# train_model.py
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

def train_and_save(csv_path, text_col="isi", label_col="label", out_path="model_berita_svm2.pkl"):
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=[text_col, label_col])
    X = df[text_col].astype(str).tolist()
    y = df[label_col].astype(int).tolist()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), max_df=0.9, min_df=3)),
        ("clf", CalibratedClassifierCV(LinearSVC(max_iter=20000), cv=3))
    ])
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    print(classification_report(y_test, preds))
    joblib.dump(pipeline, out_path)
    print(f"Model saved to {out_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python train_model.py data.csv")
    else:
        train_and_save(sys.argv[1])
