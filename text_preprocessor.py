# text_preprocessor.py
# Shim minimal untuk menghindari "No module named 'text_preprocessor'" saat unpickle.
import re
from sklearn.base import TransformerMixin, BaseEstimator

def clean_text_simple(s):
    if s is None:
        return ""
    s = str(s)
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    return s

class TextPreprocessor(BaseEstimator, TransformerMixin):
    """
    Minimal implementation supaya unpickling model yang
    mengacu pada modul text_preprocessor tidak gagal.
    Jika model asli memakai metode/atribut lain, tambahkan di sini.
    """
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return [clean_text_simple(x) for x in X]

    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)

# alias nama fungsi jika model mengharapkan fungsi bernama preprocess_text
def preprocess_text(s):
    return clean_text_simple(s)
