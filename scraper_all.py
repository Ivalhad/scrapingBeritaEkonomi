# scraper_all.py
import os
import pandas as pd
import traceback
import joblib

def _try_call(parser_fn, *args, **kwargs):
    try:
        return parser_fn(*args, **kwargs)
    except Exception as e:
        print(f"[WARNING] Parser {getattr(parser_fn,'__name__',parser_fn)} gagal: {e}")
        traceback.print_exc()
        return pd.DataFrame()

def _load_model_safe(model_path="model_berita_svm2.pkl"):
    # try candidate path relative to this file
    candidate = os.path.join(os.path.dirname(__file__), model_path) if not os.path.isabs(model_path) else model_path
    if not os.path.exists(candidate):
        print(f"[INFO] Model tidak ditemukan di {candidate}. Lewati klasifikasi.")
        return None
    try:
        model = joblib.load(candidate)
        print(f"[INFO] Model berhasil dimuat: {candidate}")
        return model
    except Exception as e:
        print(f"[WARNING] Gagal memuat model: {e}")
        traceback.print_exc()
        return None

def scrape_dan_klasifikasi(start_date=None, end_date=None, max_articles=5):
    dfs = []
    # import parsers lazily
    try:
        from parser_detik import parse_detik_lampung
    except Exception as e:
        parse_detik_lampung = None
    try:
        from parser_rmol import parse_rmol_lampung
    except Exception:
        parse_rmol_lampung = None
    try:
        from parsersAntara import parse_antara
    except Exception:
        parse_antara = None
    try:
        from lampost_parser import parse_lampost
    except Exception:
        parse_lampost = None
    try:
        from parser_radarlampung import parse_radar_lampung
    except Exception:
        parse_radar_lampung = None

    if parse_detik_lampung:
        df = _try_call(parse_detik_lampung, start_date, end_date, max_pages=2, max_articles=max_articles)
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)
    if parse_rmol_lampung:
        df = _try_call(parse_rmol_lampung, start_date, end_date, max_pages=2, max_articles=max_articles)
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)
    if parse_antara:
        df = _try_call(parse_antara, start_date, end_date, max_pages=2, max_articles=max_articles)
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)
    if parse_lampost:
        df = _try_call(parse_lampost, start_date, end_date, max_pages=2, max_articles=max_articles)
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)
    if parse_radar_lampung:
        df = _try_call(parse_radar_lampung, None, start_date, end_date, max_articles= max_articles)
        if isinstance(df, pd.DataFrame) and not df.empty:
            dfs.append(df)

    if not dfs:
        print("❌ Tidak ada hasil dari parser mana pun.")
        return pd.DataFrame(), pd.DataFrame()

    df_all = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["link"]).reset_index(drop=True)
    for col in ["judul","link","tanggal","isi"]:
        if col not in df_all.columns:
            df_all[col] = df_all.get(col, "")

    # classification if model exists
    model = _load_model_safe("model_berita_svm2.pkl")
    if model is not None:
        try:
            texts = df_all["isi"].fillna("").astype(str).tolist()
            if hasattr(model, "predict"):
                df_all["label"] = model.predict(texts)
            else:
                df_all["label"] = -1
        except Exception as e:
            print(f"[WARNING] Klasifikasi gagal: {e}")
            traceback.print_exc()
            df_all["label"] = -1
    else:
        df_all["label"] = -1

    df_ekonomi = df_all[df_all["label"] == 1].reset_index(drop=True)
    return df_all, df_ekonomi
