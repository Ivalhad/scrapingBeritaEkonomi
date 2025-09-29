# parsersAntara.py (FIXED)
# ... (import statements and helper functions remain the same) ...
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, date as date_cls
import time
from dateutil import parser as dateparser

# helpers
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
        try:
            return dateparser.parse(dt).date()
        except Exception:
            try:
                return datetime.fromisoformat(dt).date()
            except Exception:
                raise ValueError(f"Cannot parse date string: {dt}")
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
def parse_antara(driver, start_date=None, end_date=None, max_pages=2, max_articles=50, simpan=False, output_file='antara_lampung.xlsx'):
    start_date = _ensure_date(start_date)
    end_date = _ensure_date(end_date)

    results = []
    
    # REMOVED driver creation and driver.quit() block
    base = "https://lampung.antaranews.com/lampung-update?page={}"
    total = 0
    for page in range(1, max_pages+1):
        if total >= max_articles:
            break
        url = base.format(page)
        print(f"🔄 Memproses halaman {page} → {url}")
        if not _safe_get(driver, url):
            continue
        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        links = []
        for a in soup.find_all("a", class_="figure", href=True):
             href = a['href']
             title_tag = a.find("h3", class_="title")
             if title_tag:
                 title = title_tag.get_text(strip=True)
                 if href not in [l[1] for l in links]:
                     links.append((title, href))

        for title, link in links:
            if total >= max_articles:
                break
            if not _safe_get(driver, link):
                continue
            time.sleep(0.6)
            art = BeautifulSoup(driver.page_source, "html.parser")
            
            tanggal = None
            date_node = art.find("p", class_="date")
            if date_node:
                try:
                    tanggal = dateparser.parse(date_node.get_text(strip=True)).date()
                except Exception:
                    pass
            if not tanggal:
                tanggal = datetime.now().date()
            
            if (start_date and tanggal < start_date) or (end_date and tanggal > end_date):
                continue
                
            content_div = art.find("div", class_="post-content")
            if content_div:
                paras = content_div.find_all("p")
                isi = " ".join(p.get_text(strip=True) for p in paras)
                results.append({"judul": title.strip(), "link": link, "tanggal": tanggal, "isi": isi})
                total += 1

    df = pd.DataFrame(results)
    if simpan and not df.empty:
        df.to_excel(output_file, index=False)
    return df