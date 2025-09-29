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

def parse_lampost(start_date=None, end_date=None, max_articles=50, max_pages=2, simpan=False, output_file="hasil_lampost.xlsx"):
    start_date_obj = _ensure_date(start_date)
    end_date_obj = _ensure_date(end_date)

    base = "https://lampost.co.id/tag/lampung/page/{}"
    results = []
    driver = _make_chrome_driver(headless=True)
    try:
        count = 0
        for p in range(1, max_pages+1):
            url = base.format(p)
            print(f"🔄 Memuat Lampost halaman {p} -> {url}")
            if not _safe_get(driver, url):
                continue
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a['href']
                if "/202" in href and "lampost" in href:
                    link = href
                    title = a.get_text(strip=True)
                    if count >= max_articles:
                        break
                    if not _safe_get(driver, link):
                        continue
                    time.sleep(0.6)
                    art = BeautifulSoup(driver.page_source, "html.parser")
                    tanggal = None
                    time_tags = art.find_all("time")
                    if time_tags:
                        for t in time_tags:
                            if t.has_attr("datetime"):
                                try:
                                    tanggal = datetime.fromisoformat(t["datetime"]).date()
                                    break
                                except Exception:
                                    pass
                    if not tanggal:
                        # try parse from text nodes
                        possible = art.find(class_="published") or art.find("span", class_="date")
                        if possible:
                            txt = possible.get_text(strip=True).split(" -")[0]
                            try:
                                tanggal = datetime.strptime(txt, "%d %B %Y").date()
                            except Exception:
                                try:
                                    tanggal = datetime.fromisoformat(txt).date()
                                except Exception:
                                    tanggal = None
                    if not tanggal:
                        tanggal = datetime.now().date()
                    if start_date_obj and tanggal < start_date_obj:
                        continue
                    if end_date_obj and tanggal > end_date_obj:
                        continue
                    paras = art.find_all("p")
                    isi = " ".join(p.get_text(strip=True) for p in paras)
                    results.append({"judul": title.strip(), "link": link, "tanggal": tanggal, "isi": isi})
                    count += 1
            if count >= max_articles:
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
