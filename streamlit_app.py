# streamlit_app.py
import streamlit as st
from datetime import date
import pandas as pd

st.set_page_config(page_title="Scraping Klasifikasi", layout="wide")
st.title("Scraping + Klasifikasi (Streamlit)")

start = st.date_input("Start date", value=None)
end = st.date_input("End date", value=None)
max_articles = st.number_input("Max articles per portal", min_value=1, max_value=200, value=10)

if st.button("Run scraper"):
    with st.spinner("Menjalankan parser..."):
        try:
            from scraper_all import scrape_dan_klasifikasi
            df_all, df_ekonomi = scrape_dan_klasifikasi(start_date=start, end_date=end, max_articles=max_articles)
            st.success(f"Selesai. Artikel total: {len(df_all)}; Ekonomi: {len(df_ekonomi)}")
            if not df_all.empty:
                st.write("Semua Artikel (sample):")
                st.dataframe(df_all.head(200))
                csv_all = df_all.to_csv(index=False).encode('utf-8')
                st.download_button("Download semua CSV", data=csv_all, file_name="hasil_semua_portal.csv")
            else:
                st.info("Tidak ada artikel yang ditemukan.")
        except Exception as e:
            st.error(f"Gagal menjalankan scraper: {e}")
            import traceback; st.text(traceback.format_exc())
