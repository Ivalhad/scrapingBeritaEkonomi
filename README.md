# Scraper & Klasifikasi Berita Lampung

## Ikhtisar Proyek

Aplikasi web ini dirancang untuk melakukan *web scraping* berita dari berbagai portal media online di Lampung. Setelah berita berhasil dikumpulkan, aplikasi akan melakukan klasifikasi menggunakan model *machine learning* yang telah dilatih untuk mengidentifikasi berita dengan kategori "Ekonomi".

Hasil scraping (semua berita dan berita ekonomi) kemudian ditampilkan dalam antarmuka web yang bersih dan responsif yang dibangun menggunakan framework Flask dan Bootstrap.



## Fitur Utama

-   **Scraping Multi-Sumber**: Mengambil data dari 5 portal berita populer di Lampung:
    -   Detik Lampung
    -   RMOL Lampung
    -   Antara News Lampung
    -   Lampost
    -   Radar Lampung
-   **Filter Fleksibel**: Pengguna dapat menentukan rentang tanggal dan jumlah maksimum artikel yang akan di-scrape per portal.
-   **Klasifikasi Otomatis**: Memanfaatkan model SVM (Support Vector Machine) yang telah dilatih untuk memisahkan berita ekonomi dari kategori lainnya.
-   **Antarmuka Web Modern**: Tampilan yang ramah pengguna dan responsif dibangun dengan Flask dan Bootstrap.
-   **Logika Scraper yang Dioptimalkan**: Menggunakan satu *instance* Selenium WebDriver untuk semua parser, sehingga proses scraping berjalan lebih cepat dan efisien.

## Teknologi yang Digunakan

-   **Backend**: Python, Flask
-   **Web Scraping**: Selenium, BeautifulSoup4
-   **Data Processing**: Pandas
-   **Machine Learning**: Scikit-learn, Joblib
-   **Frontend**: HTML, Bootstrap 5, Jinja2

---

## Struktur Proyek

Proyek ini disusun dengan struktur yang modular untuk kemudahan pemeliharaan:

/scrapingBeritaEkonomi/
├── static/
│   └── css/
│       └── style.css         # File styling untuk antarmuka
├── templates/
│   └── index.html            # Template HTML untuk halaman utama
├── app.py                    # File utama aplikasi Flask (entry point)
├── scraper_all.py            # Logika utama untuk orkestrasi scraper & klasifikasi
├── parser_detik.py           # Parser spesifik untuk Detik Lampung
├── parser_rmol.py            # Parser spesifik untuk RMOL Lampung
├── parsersAntara.py          # Parser spesifik untuk Antara News
├── lampost_parser.py         # Parser spesifik untuk Lampost
├── parser_radarlampung.py    # Parser spesifik untuk Radar Lampung
├── model_berita_svm2.pkl     # File model Machine Learning
├── requirements.txt          # Daftar dependensi Python
└── README.md                 # Dokumentasi ini

---

## Panduan Instalasi dan Penggunaan

### Prasyarat

-   Python 3.8 atau lebih baru
-   PIP & Venv (biasanya sudah termasuk dalam instalasi Python)
-   Browser Google Chrome (terinstal di sistem Anda)

### Langkah-langkah Instalasi

1.  **Clone atau Unduh Proyek**
    * Jika menggunakan Git, clone repositori ini. Jika tidak, cukup pastikan semua file proyek berada dalam satu folder utama.

2.  **Buka Terminal**
    * Buka terminal atau Command Prompt dan navigasikan ke direktori utama proyek (`/scrapingBeritaEkonomi/`).

3.  **Buat dan Aktifkan Lingkungan Virtual**
    * Ini sangat disarankan untuk menjaga dependensi proyek tetap terisolasi.
    ```bash
    # Buat lingkungan virtual
    python -m venv .venv

    # Aktifkan di Windows
    .venv\Scripts\activate

    # Aktifkan di macOS/Linux
    source .venv/bin/activate
    ```

4.  **Instal Dependensi**
    * Pastikan lingkungan virtual Anda aktif, lalu jalankan perintah berikut untuk menginstal semua pustaka yang dibutuhkan:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Pastikan Model Ada**
    * Letakkan file model `model_berita_svm2.pkl` di direktori utama proyek. Tanpa file ini, fitur klasifikasi tidak akan berjalan.

### Menjalankan Aplikasi

1.  **Mulai Server Flask**
    * Dari direktori utama proyek (dengan lingkungan virtual aktif), jalankan perintah:
    ```bash
    python app.py
    ```

2.  **Buka di Browser**
    * Buka browser web Anda dan akses alamat berikut:
    ```
    [http://127.0.0.1:5000](http://127.0.0.1:5000)
    ```
    * Aplikasi sekarang siap digunakan. Pilih rentang tanggal, tentukan jumlah artikel, dan klik "Jalankan".