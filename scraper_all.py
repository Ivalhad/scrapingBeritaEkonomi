# scraper_all.py (Optimized)
import os
import pandas as pd
import traceback
import joblib
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

# Fungsi untuk membuat driver dipindahkan ke sini
def _make_chrome_driver(headless=True):
    """Membuat satu instance Chrome driver yang akan digunakan kembali."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Blok ini untuk mencegah deteksi otomatisasi
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception as e:
        print(f"Gagal menginstal/setup ChromeDriver, coba cara manual: {e}")
        # Fallback jika webdriver-manager gagal (misalnya karena firewall)
        driver = webdriver.Chrome(options=options)

    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    print("[INFO] Chrome driver berhasil dibuat.")
    return driver

# ... (Fungsi _try_call dan _load_model_safe tetap sama) ...
def _try_call(parser_fn, *args, **kwargs):
    try:
        return parser_fn(*args, **kwargs)
    except Exception as e:
        print(f"[WARNING] Parser {getattr(parser_fn,'__name__',parser_fn)} gagal: {e}")
        traceback.print_exc()
        return pd.DataFrame()

def _load_model_safe(model_path="model_berita_svm2.pkl"):
    candidate = os.path.join(os.path.dirname(__file__), model_path)
    if not os.path.exists(candidate):
        print(f"[INFO] Model tidak ditemukan di {candidate}. Lewati klasifikasi.")
        return None
    try:
        model = joblib.load(candidate)
        print(f"[INFO] Model berhasil dimuat: {candidate}")
        return model
    except Exception as e:
        print(f"[WARNING] Gagal memuat model: {e}")
        return None


# Fungsi utama yang dimodifikasi
def scrape_dan_klasifikasi(start_date=None, end_date=None, max_articles=5):
    # Buat SATU driver untuk semua parser
    driver = _make_chrome_driver(headless=True)
    
    dfs = []
    # Import parsers
    from parser_detik import parse_detik_lampung
    from parser_rmol import parse_rmol_lampung
    from parsersAntara import parse_antara
    from lampost_parser import parse_lampost
    from parser_radarlampung import parse_radar_lampung

    parsers = {
        "Detik Lampung": parse_detik_lampung,
        "RMOL Lampung": parse_rmol_lampung,
        "Antara News": parse_antara,
        "Lampost": parse_lampost,
        "Radar Lampung": parse_radar_lampung
    }

    try:
        # Jalankan setiap parser dengan driver yang sama
        for name, parser_func in parsers.items():
            print(f"--- Menjalankan parser: {name} ---")
            df = _try_call(parser_func, driver=driver, start_date=start_date, end_date=end_date, max_articles=max_articles)
            if isinstance(df, pd.DataFrame) and not df.empty:
                dfs.append(df)
    finally:
        # Tutup driver HANYA setelah semua parser selesai
        if driver:
            driver.quit()
            print("[INFO] Chrome driver ditutup.")

    if not dfs:
        print("❌ Tidak ada hasil dari parser mana pun.")
        return pd.DataFrame(), pd.DataFrame()

    df_all = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["link"]).reset_index(drop=True)
    
    # ... (Sisa kode untuk klasifikasi tetap sama) ...
    model = _load_model_safe("model_berita_svm2.pkl")
    if model is not None:
        try:
            texts = df_all["isi"].fillna("").astype(str).tolist()
            df_all["label"] = model.predict(texts)
        except Exception as e:
            print(f"[WARNING] Klasifikasi gagal: {e}")
            df_all["label"] = -1
    else:
        df_all["label"] = -1

    df_ekonomi = df_all[df_all["label"] == 1].reset_index(drop=True)
    return df_all, df_ekonomi
