# TrafficLab - Simulasi dan Analisis Pengaturan Lampu Lalu Lintas

TrafficLab adalah aplikasi web interaktif untuk memodelkan, menjalankan, dan membandingkan strategi pengaturan lampu lalu lintas pada persimpangan empat arah. Proyek ini dikembangkan sebagai tugas mata kuliah **Pemodelan dan Simulasi**.

Aplikasi menggunakan **Python dan Flask** sebagai backend, **SimPy** sebagai mesin *Discrete Event Simulation* (DES), serta **HTML5 Canvas** dan **Chart.js** untuk menampilkan animasi kendaraan dan hasil analisis melalui dashboard.

## Fitur

- **Simulasi berbasis SimPy:** waktu virtual dan kejadian simulasi dijalankan oleh backend menggunakan SimPy. Animasi di browser hanya menampilkan keadaan simulasi, bukan menjadi sumber waktu simulasi.
- **Animasi persimpangan 2D:** tampilan persimpangan empat arah dari atas, dilengkapi marka jalan, lampu lalu lintas, antrean, serta kendaraan motor dan mobil.
- **Kontrol simulasi:** pemilihan metode Fixed-Time atau Adaptive, pemilihan skenario, pengaturan rasio motor dan mobil, *random seed*, durasi simulasi, serta kontrol kecepatan animasi.
- **Dashboard statistik:** menampilkan rata-rata waktu tunggu, rata-rata panjang antrean berbobot waktu, antrean maksimum, jumlah kendaraan datang/terlayani/tersisa, dan *throughput*.
- **Grafik secara langsung:** menampilkan perubahan panjang antrean pada sumbu NS dan EW terhadap waktu simulasi.
- **Eksperimen batch:** menjalankan eksperimen komparatif berulang dengan pendekatan Monte Carlo dan *Common Random Numbers* (CRN), lalu menyajikan ringkasan, grafik perbandingan, statistik rata-rata dan standar deviasi, serta ekspor hasil ke CSV.
- **Antarmuka light mode:** dashboard dengan warna yang terinspirasi dari elemen lalu lintas agar informasi simulasi mudah dibedakan.

## Struktur Proyek

```text
TrafficLab/
├── app.py                         # Entry point aplikasi Flask
├── config.py                      # Konfigurasi parameter dan skenario
├── requirements.txt               # Dependensi Python
├── README.md                      # Dokumentasi proyek
├── simulation/                    # Mesin simulasi SimPy (DES)
│   ├── __init__.py
│   ├── engine.py                  # Orkestrasi simulasi
│   ├── vehicle.py                 # Model kendaraan motor dan mobil
│   ├── arrivals.py                # Generator kedatangan Poisson/eksponensial
│   ├── traffic_signal.py          # Pengelolaan fase dan sinyal lalu lintas
│   ├── metrics.py                 # Pengumpulan dan perhitungan metrik
│   ├── experiments.py              # Eksperimen Monte Carlo dan CRN
│   └── controllers/               # Algoritma pengendali lampu lalu lintas
│       ├── __init__.py
│       ├── base_controller.py
│       ├── fixed_time.py
│       └── adaptive.py
├── routes/
│   ├── __init__.py
│   └── api.py                     # REST API berbasis JSON
├── templates/
│   └── index.html                 # Halaman utama
├── static/
│   ├── css/
│   │   └── style.css              # Styling dashboard
│   └── js/
│       ├── api.js                 # Komunikasi frontend dengan API
│       ├── simulation-renderer.js # Renderer persimpangan dan kendaraan
│       ├── charts.js              # Grafik live dan hasil eksperimen
│       ├── dashboard.js           # Kontrol dan statistik dashboard
│       └── app.js                 # Inisialisasi frontend
```

## Instalasi dan Menjalankan Aplikasi

### 1. Clone repository

```bash
git clone <URL-REPOSITORY>
cd TrafficLab
```

Ganti `<URL-REPOSITORY>` dengan URL repository GitHub milikmu.

### 2. Buat dan aktifkan virtual environment

**Windows (PowerShell):**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Jalankan aplikasi

```bash
python app.py
```

### 4. Buka aplikasi di browser

Akses alamat berikut:

```text
http://127.0.0.1:5000
```

> **Catatan:** Perintah di atas mengasumsikan aplikasi Flask berjalan pada alamat lokal dan port `5000`.

**TrafficLab** — Proyek akademik mata kuliah Pemodelan dan Simulasi.
