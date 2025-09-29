from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime, date as date_cls
import time
import pandas as pd

# --- helpers added for robustness ---
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
def parse_detik_lampung(start_date=None, end_date=None, max_pages=2, max_articles=50, simpan=False, output_file="hasil_detik_lampung.xlsx"):
    """
    Returns DataFrame with columns: judul, link, tanggal (datetime.date), isi
    start_date/end_date can be None, str, datetime.date, datetime.datetime.
    """
    start_date_obj = _ensure_date(start_date)
    end_date_obj = _ensure_date(end_date)

    base_url = "https://www.detik.com/tag/lampung/?sortby=time&page={}"
    results = []

    driver = _make_chrome_driver(headless=True)
    try:
        total_found = 0
        for p in range(1, max_pages + 1):
            url = base_url.format(p)
            print(f"🔄 Memproses halaman {p} → {url}")
            if not _safe_get(driver, url):
                print("  ❌ Gagal load page, lanjut ke page berikutnya.")
                continue
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.select("article, .list-content, .media__title, .dt-list__item")  # broad selectors
            # fallback: find links in <a> tags inside list
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if "/news/" in href or "detik.com" in href:
                    links.append((a.get_text(strip=True), href))
            # de-duplicate preserving order
            seen = set()
            clean_links = []
            for t,href in links:
                if href not in seen:
                    seen.add(href)
                    clean_links.append((t, href))
            # iterate through discovered article links
            for title, link in clean_links:
                if total_found >= max_articles:
                    break
                try:
                    if not _safe_get(driver, link):
                        continue
                    time.sleep(0.6)
                    art_soup = BeautifulSoup(driver.page_source, "html.parser")
                    # find tanggal (detik often uses <time> or class)
                    tanggal = None
                    time_tag = art_soup.find("time")
                    if time_tag and time_tag.has_attr("datetime"):
                        try:
                            tanggal = datetime.fromisoformat(time_tag["datetime"]).date()
                        except Exception:
                            pass
                    if not tanggal:
                        # try to parse displayed text
                        ttxt = art_soup.find(class_="date") or art_soup.find(class_="time")
                        if ttxt:
                            txt = ttxt.get_text(strip=True)
                            # attempt several formats
                            for fmt in ("%A, %d %b %Y %H:%M", "%d %b %Y %H:%M", "%Y-%m-%d %H:%M"):
                                try:
                                    tanggal = datetime.strptime(txt, fmt).date()
                                    break
                                except Exception:
                                    pass
                    # fallback: today
                    if not tanggal:
                        tanggal = datetime.now().date()
                    # filter by date range if provided
                    if start_date_obj and tanggal < start_date_obj:
                        print("     ⏩ Lewat (tanggal tidak sesuai):", tanggal)
                        continue
                    if end_date_obj and tanggal > end_date_obj:
                        print("     ⏩ Lewat (tanggal > end):", tanggal)
                        continue
                    # isi content
                    paras = art_soup.find_all('p')
                    isi = " ".join(p.get_text(strip=True) for p in paras)
                    results.append({
                        "judul": title.strip(),
                        "link": link,
                        "tanggal": tanggal,
                        "isi": isi
                    })
                    total_found += 1
                except Exception as e:
                    print("   [warn] gagal parse artikel:", link, e)
                    continue
            if total_found >= max_articles:
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
