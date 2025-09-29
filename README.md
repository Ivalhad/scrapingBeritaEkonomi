# Scraping Klasifikasi (patche d untuk Streamlit)

## Setup
1) buat virtualenv:
   python -m venv .venv
   .venv\Scripts\activate  (Windows) OR source .venv/bin/activate

2) install requirement:
   pip install -r requirements.txt

## Menjalankan Streamlit
streamlit run streamlit_app.py

## Catatan
- Parser memakai webdriver-manager sehingga Anda tidak perlu menyertakan chromedriver.exe.
- Jika ingin klasifikasi, letakkan `model_berita_svm2.pkl` (sklearn pipeline joblib) di folder project.
- Jika model lama bergantung modul custom (mis. `text_preprocessor`), retrain dengan `train_model.py`.
