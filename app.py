from flask import Flask, render_template, request
from scraper_all import scrape_dan_klasifikasi
import pandas as pd

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    hasil_all = None
    hasil_ekonomi = None

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        max_articles = int(request.form.get("max_articles") or 5)

        # Menampilkan pesan status di konsol
        print(f"Menerima permintaan: start_date={start_date}, end_date={end_date}, max_articles={max_articles}")
        print("Memulai proses scraping dan klasifikasi...")

        df_all, df_ekonomi = scrape_dan_klasifikasi(start_date, end_date, max_articles)

        if not df_all.empty:
            hasil_all = df_all.to_dict(orient="records")
            # Pastikan kolom 'isi' tidak terlalu panjang untuk ditampilkan
            for item in hasil_all:
                item['isi'] = (item['isi'][:200] + '...') if len(item['isi']) > 200 else item['isi']

        if not df_ekonomi.empty:
            hasil_ekonomi = df_ekonomi.to_dict(orient="records")
            for item in hasil_ekonomi:
                item['isi'] = (item['isi'][:200] + '...') if len(item['isi']) > 200 else item['isi']
        
        print("Proses selesai. Mengirim hasil ke template.")

    return render_template("index.html", hasil_all=hasil_all, hasil_ekonomi=hasil_ekonomi)

if __name__ == "__main__":
    app.run(debug=True)