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
            # fallback try iso
            try:
                return datetime.fromisoformat(dt).date()
            except Exception:
                raise ValueError(f"Cannot parse date string: {dt}")
    raise TypeError(f"Unsupported date type: {type(dt)}")

def _make_chrome_driver(headless=True):
    options = Options()
    if headless:
        try:
            options.add_argument("--headless=new")
        except:
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

def parse_antara(start_date=None, end_date=None, max_pages=2, max_articles=50, simpan=False, output_file='antara_lampung.xlsx'):
    # Normalize input dates
    start_date = _ensure_date(start_date)
    end_date = _ensure_date(end_date)

    options = None
    results = []
    driver = _make_chrome_driver(headless=True)
    try:
        base = "https://lampung.antaranews.com/lampung-update?page={}"
        total = 0
        for page in range(1, max_pages+1):
            url = base.format(page)
            print(f"🔄 Memproses halaman {page} → {url}")
            if not _safe_get(driver, url):
                continue
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # find list of article links
            cards = soup.select("article, .list-berita, .post, .berita")
            links = []
            for a in soup.find_all("a", href=True):
                href = a['href']
                if "/lampung-update/" in href or "antaranews.com" in href:
                    txt = a.get_text(strip=True)
                    if href not in [l[1] for l in links]:
                        links.append((txt, href))
            for title, link in links:
                if total >= max_articles:
                    break
                if not _safe_get(driver, link):
                    continue
                time.sleep(0.6)
                art = BeautifulSoup(driver.page_source, "html.parser")
                # parse tanggal
                tanggal = None
                date_nodes = art.find_all("time")
                if date_nodes:
                    for dn in date_nodes:
                        if dn.has_attr("datetime"):
                            try:
                                tanggal = datetime.fromisoformat(dn["datetime"]).date()
                                break
                            except Exception:
                                pass
                if not tanggal:
                    # try text extraction
                    possible = art.find(class_="date") or art.find("p", class_="date")
                    if possible:
                        txt = possible.get_text(strip=True)
                        try:
                            tanggal = dateparser.parse(txt).date()
                        except Exception:
                            pass
                if not tanggal:
                    tanggal = datetime.now().date()
                # filter
                if start_date and tanggal < start_date:
                    print("     ⏩ Lewat (tanggal tidak sesuai):", tanggal)
                    continue
                if end_date and tanggal > end_date:
                    continue
                paras = art.find_all("p")
                isi = " ".join(p.get_text(strip=True) for p in paras)
                results.append({"judul": title.strip(), "link": link, "tanggal": tanggal, "isi": isi})
                total += 1
            if total >= max_articles:
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
