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

        df_all, df_ekonomi = scrape_dan_klasifikasi(start_date, end_date, max_articles)

        if df_all is not None:
            hasil_all = df_all.to_dict(orient="records")
            hasil_ekonomi = df_ekonomi.to_dict(orient="records")
            df_all.to_excel("hasil_semua_portal.xlsx", index=False)
            df_ekonomi.to_excel("Berita_Ekonomi.xlsx", index=False)

    return render_template("index.html", hasil_all=hasil_all, hasil_ekonomi=hasil_ekonomi)

if __name__ == "__main__":
    app.run(debug=True)
