from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, date as date_cls
import time
import pandas as pd

# --- helpers ---
from selenium import webdriver as _webdriver_internal
import time as _time_internal

def _ensure_date(dt):
    if dt is None:
        return None
    if isinstance(dt, date_cls):
        return dt
    if isinstance(dt, datetime):
        return dt.date()
    if isinstance(dt, str):
        s = dt.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                pass
        try:
            return datetime.fromisoformat(s).date()
        except Exception:
            raise ValueError(f"String date format not supported: {s}")
    raise TypeError(f"Unsupported date type: {type(dt)}")

def _make_chrome_driver(headless=True):
    options = Options()
    if headless:
        try:
            options.add_argument("--headless=new")
        except Exception:
            options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    driver = _webdriver_internal.Chrome(service=service, options=options)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception:
        pass
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    return driver

def _safe_get(driver, url, retries=3, delay=2):
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"[WARN] get {url} failed (attempt {i+1}/{retries}): {e}")
            _time_internal.sleep(delay)
    return False

# -------------- parser function --------------
def parse_rmol_lampung(start_date=None, end_date=None, max_pages=2, max_articles=50, simpan=False, output_file="hasil_rmol_lampung.xlsx"):
    start_date_obj = _ensure_date(start_date)
    end_date_obj = _ensure_date(end_date)

    base = "https://rmollampung.id/?s=lampung&page={}"
    results = []
    driver = _make_chrome_driver(headless=True)
    try:
        found = 0
        for p in range(1, max_pages+1):
            url = base.format(p)
            print(f"🔄 Memuat RMOL halaman {p} -> {url}")
            if not _safe_get(driver, url):
                continue
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # find article links
            for a in soup.find_all("a", href=True):
                href = a['href']
                if "/202" in href or "/news/" in href or "rmollampung" in href:
                    link = href
                    title = a.get_text(strip=True) or None
                    if not title or title.lower().startswith("read more"):
                        continue
                    # open article
                    if found >= max_articles:
                        break
                    if not _safe_get(driver, link):
                        continue
                    time.sleep(0.6)
                    art_soup = BeautifulSoup(driver.page_source, "html.parser")
                    # try to extract tanggal
                    tanggal = None
                    # common patterns: meta property or time tag
                    meta_time = art_soup.find("time")
                    if meta_time and meta_time.has_attr("datetime"):
                        try:
                            tanggal = datetime.fromisoformat(meta_time["datetime"]).date()
                        except Exception:
                            pass
                    if not tanggal:
                        # try to find date in text
                        textnodes = art_soup.find_all(text=True)
                        for tn in textnodes[:50]:
                            txt = tn.strip()
                            if txt and any(m in txt.lower() for m in ["202", "2025", "2024"]):
                                # attempt parse
                                for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
                                    try:
                                        tanggal = datetime.strptime(txt, fmt).date()
                                        break
                                    except Exception:
                                        pass
                            if tanggal:
                                break
                    if not tanggal:
                        tanggal = datetime.now().date()
                    if start_date_obj and tanggal < start_date_obj:
                        continue
                    if end_date_obj and tanggal > end_date_obj:
                        continue
                    paras = art_soup.find_all("p")
                    isi = " ".join(p.get_text(strip=True) for p in paras)
                    results.append({"judul": title.strip(), "link": link, "tanggal": tanggal, "isi": isi})
                    found += 1
            if found >= max_articles:
                break
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    df = pd.DataFrame(results)
    if simpan and not df.empty:
        df.to_excel(output_file, index=False)
    return df
