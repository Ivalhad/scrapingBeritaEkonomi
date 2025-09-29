from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime, date as date_cls
import time
import pandas as pd

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

def parse_radar_lampung(driver=None, start_date=None, end_date=None, max_articles=30, max_pages=2):
    """
    Note: original repo used this parser with a driver passed in — we keep the signature.
    If driver is None, we'll create one.
    """
    start_date = _ensure_date(start_date)
    end_date = _ensure_date(end_date)

    close_driver = False
    if driver is None:
        driver = _make_chrome_driver(headless=True)
        close_driver = True

    results = []
    try:
        found = 0
        for page in range(1, max_pages+1):
            offset = (page - 1) * 10
            url = f"https://radarlampung.disway.id/kategori/458/lampung-raya/{offset}"
            print(f"🌐 Memuat halaman: {url}")
            if not _safe_get(driver, url):
                continue
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            article_links = []
            for p in soup.find_all('p'):
                a_tag = p.find('a', href=True)
                if a_tag:
                    href = a_tag['href']
                    if href and "radarlampung" in href:
                        title = a_tag.get_text(strip=True)
                        if href not in [l[1] for l in article_links]:
                            article_links.append((title, href))

            for title, link in article_links:
                if found >= max_articles:
                    break
                if not _safe_get(driver, link):
                    continue
                time.sleep(0.6)
                art_soup = BeautifulSoup(driver.page_source, "html.parser")
                tanggal = None
                # try to parse time tag or text
                ttag = art_soup.find("time")
                if ttag and ttag.has_attr("datetime"):
                    try:
                        tanggal = datetime.fromisoformat(ttag["datetime"]).date()
                    except Exception:
                        pass
                if not tanggal:
                    # fallback parse from text nodes
                    textnodes = art_soup.find_all(text=True)[:120]
                    for tn in textnodes:
                        txt = tn.strip()
                        if txt and any(c.isdigit() for c in txt):
                            for fmt in ("%d %B %Y", "%Y-%m-%d"):
                                try:
                                    tanggal = datetime.strptime(txt, fmt).date()
                                    break
                                except Exception:
                                    pass
                        if tanggal:
                            break
                if not tanggal:
                    tanggal = datetime.now().date()
                if start_date and tanggal < start_date:
                    continue
                if end_date and tanggal > end_date:
                    continue
                paras = art_soup.find_all("p")
                isi = " ".join(p.get_text(strip=True) for p in paras)
                results.append({"judul": title.strip(), "link": link, "tanggal": tanggal, "isi": isi})
                found += 1
            if found >= max_articles:
                break
    finally:
        if close_driver:
            try:
                driver.quit()
            except Exception:
                pass

    df = pd.DataFrame(results)
    return df
