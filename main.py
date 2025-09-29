# main.py (refactor)
import os
import pandas as pd

def run_scrapers(start_date=None, end_date=None, max_articles=10):
    try:
        from scraper_all import scrape_dan_klasifikasi
    except Exception as e:
        print("scraper_all tidak ditemukan atau error:", e)
        raise
    df_all, df_ekonomi = scrape_dan_klasifikasi(start_date, end_date, max_articles)
    if not df_all.empty:
        df_all.to_excel("hasil_semua_portal.xlsx", index=False)
        df_ekonomi.to_excel("Berita_Ekonomi.xlsx", index=False)
        print("Hasil disimpan: hasil_semua_portal.xlsx, Berita_Ekonomi.xlsx")
    return df_all, df_ekonomi

if __name__ == "__main__":
    run_scrapers()
