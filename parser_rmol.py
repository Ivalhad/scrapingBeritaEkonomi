# parser_rmol.py (FIXED)
# ... (import statements and helper functions remain the same) ...
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

def _safe_get(driver, url, retries=3, delay=2):
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"[WARN] get {url} failed (attempt {i+1}/{retries}): {e}")
            _time_internal.sleep(delay)
    return False

# SIGNATURE UPDATED to accept 'driver'
def parse_rmol_lampung(driver, start_date=None, end_date=None, max_pages=2, max_articles=50, simpan=False, output_file="hasil_rmol_lampung.xlsx"):
    start_date_obj = _ensure_date(start_date)
    end_date_obj = _ensure_date(end_date)

    base = "https://rmollampung.id/?s=lampung&page={}"
    results = []
    
    # REMOVED driver creation and driver.quit() block
    found = 0
    for p in range(1, max_pages+1):
        if found >= max_articles:
            break
        url = base.format(p)
        print(f"🔄 Memuat RMOL halaman {p} -> {url}")
        if not _safe_get(driver, url):
            continue
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        links = []
        for a in soup.find_all("a", href=True):
            href = a['href']
            if "/berita/" in href and "rmollampung.id" in href:
                 title = a.get_text(strip=True)
                 if title and href not in [l[1] for l in links]:
                     links.append((title, href))
        
        for title, link in links:
            if found >= max_articles:
                break
            if not _safe_get(driver, link):
                continue
            time.sleep(0.6)
            art_soup = BeautifulSoup(driver.page_source, "html.parser")
            
            tanggal = None
            meta_time = art_soup.find("time")
            if meta_time and meta_time.has_attr("datetime"):
                try:
                    tanggal = datetime.fromisoformat(meta_time["datetime"]).date()
                except Exception:
                    pass
            
            if not tanggal:
                date_text_element = art_soup.select_one(".text-body-tertiary.d-inline-block.me-3")
                if date_text_element:
                    date_text = date_text_element.text.strip()
                    try:
                       tanggal = datetime.strptime(date_text, "%A, %d %B %Y | %H:%M WIB").date()
                    except ValueError:
                        pass
            if not tanggal:
                tanggal = datetime.now().date()

            if (start_date_obj and tanggal < start_date_obj) or \
               (end_date_obj and tanggal > end_date_obj):
                continue

            paras = art_soup.find("div", class_="read-content").find_all("p")
            isi = " ".join(p.get_text(strip=True) for p in paras)
            results.append({"judul": title.strip(), "link": link, "tanggal": tanggal, "isi": isi})
            found += 1

    df = pd.DataFrame(results)
    if simpan and not df.empty:
        df.to_excel(output_file, index=False)
    return df