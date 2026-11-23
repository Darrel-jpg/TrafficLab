# TrafficLab — Simulasi dan Analisis Pengaturan Lampu Lalu Lintas

**TrafficLab** adalah aplikasi web interaktif berbasis sains simulasi (*Discrete Event Simulation* / DES) untuk memodelkan, memvisualisasikan, dan menganalisis kinerja algoritma pengaturan lampu lalu lintas pada persimpangan jalan empat arah (**Utara, Selatan, Barat, dan Timur**)

---

## Fitur Utama

- **Mesin DES Berbasis SimPy:** Waktu virtual, pembangkitan kendaraan stokastik, perubahan fase lampu, dan clearance simpang sepenuhnya dikelola oleh SimPy di backend. Animasi di browser menggunakan interpolasi 60 FPS untuk rendering yang halus.
- **Visualisasi Persimpangan 2D Modern:** Pemandangan atas (*top-down view*) persimpangan 4 arah dengan jalan aspal, zebra cross, rambu lampu lalu lintas di 4 sudut, dan beragam model kendaraan (taksi, sedan, truk, hatchback, serta sepeda motor).
- **Penempatan Informasi Antrean Bersih:** Keterangan jumlah antrean (`Utara`, `Selatan`, `Barat`, `Timur`) ditempatkan di trotoar sebelah kiri jalan masing-masing arah sehingga tidak menutupi kendaraan yang sedang mengantre.
- **Dua Metode Pengaturan Sinyal:**
  - **Fixed-Time Controller:** Siklus waktu tetap (30 detik hijau, 3 detik kuning, 1 detik *all-red clearance* per sumbu).
  - **Adaptive Controller:** Durasi hijau fleksibel (15–45 detik) yang memprioritaskan sumbu dengan antrean terpanjang, dilengkapi mekanisme *anti-starvation* (maksimal 60 detik menunggu merah).
- **Empat Skenario Kepadatan Arus:** Tersedia skenario bawaan (*Normal*, *Padat NS*, *Padat EW*, dan *Jam Sibuk*) serta input volume kustom per pendekat.
- **Metrik Performa & KPI Real-Time:** Menghitung waktu tunggu rata-rata (*unbiased*, mencakup kendaraan yang belum terlayani saat simulasi berakhir), panjang antrean rata-rata berbobot waktu ($\int Q(t)dt / T$), antrean maksimum, dan *throughput*.
- **Grafik Antrean Waktu Nyata:** Grafik garis interaktif bertenaga Chart.js yang memantau dinamika fluktuasi antrean pada sumbu NS, EW, dan Total.
- **Script Batch Eksperimen Monte Carlo:** Script mandiri (`run_experiments.py`) untuk menjalankan pengujian komparatif berulang dengan teknik *Common Random Numbers* (CRN) dan mengekspor hasilnya langsung ke file **`laporan_eksperimen.csv`** untuk keperluan penyusunan makalah/laporan.

---

## Struktur Folder Proyek

```text
TrafficLab/
├── app.py                  # Server web Flask utama
├── config.py               # Konfigurasi parameter simulasi & skenario default
├── run_experiments.py      # Script CLI untuk menjalankan batch eksperimen ke CSV
├── icon/                   # Folder aset ikon website
│   └── traffic-light.png   # Ikon lampu lalu lintas untuk logo & favicon
├── routes/
│   ├── __init__.py
│   └── api.py              # Endpoint REST API (/api/simulations, /api/config)
├── simulation/             # Modul Discrete Event Simulation (SimPy)
│   ├── __init__.py
│   ├── engine.py           # Orkestrator simulasi SimPy & proses antrean
│   ├── traffic_signal.py   # State machine lampu lalu lintas & safety lock
│   ├── vehicle.py          # Representasi data kendaraan (motor & mobil)
│   ├── arrivals.py         # Generator kedatangan Poisson (distribusi eksponensial)
│   ├── metrics.py          # Pencatat & kalkulator statistik antrean/waktu tunggu
│   ├── experiments.py      # Runner Monte Carlo komparatif Fixed-Time vs Adaptive
│   └── controllers/        # Logika pengendali sinyal lalu lintas
│       ├── __init__.py
│       ├── base_controller.py
│       ├── fixed_time.py
│       └── adaptive.py
├── templates/
│   └── index.html          # Halaman dashboard web simulasi (Single-Page)
└── static/
    ├── css/
    │   └── style.css       # Desain antarmuka modern light mode (DM Sans)
    └── js/
        ├── api.js          # REST API client wrapper
        ├── simulation-renderer.js  # Engine canvas 2D & animasi kendaraan 60 FPS
        ├── charts.js       # Manajer grafik Chart.js untuk antrean real-time
        ├── dashboard.js    # Kontrol UI, polling state, & pembaruan KPI
        └── app.js          # Inisialisasi awal aplikasi web
```

---

## Kebutuhan Sistem & Dependensi

- **Python:** Versi 3.10 atau yang lebih baru (diuji pada Python 3.14).
- **Paket Python:**
  - `Flask`
  - `simpy`

Instalasi dependensi dapat dilakukan langsung melalui terminal:

```powershell
pip install flask simpy
```

---

## Panduan Menjalankan Aplikasi

### 1. Menjalankan Website Simulasi Interaktif

Jalankan perintah berikut di folder proyek:

```powershell
python app.py
```

Setelah server aktif, buka peramban (*browser*) dan akses alamat:
👉 **`http://127.0.0.1:5000`**

**Kontrol pada Dashboard:**
- Pilih metode pengaturan lampu: **Fixed-Time** atau **Adaptive**.
- Pilih skenario lalu lintas atau atur volume arus kendaraan per arah.
- Atur kecepatan simulasi (**1x**, **2x**, **5x**, atau **10x**).
- Klik tombol **Mulai Simulasi** untuk menjalankan persimpangan, **Jeda** untuk menghentikan sementara, atau **Reset** untuk mengulang dari awal.

---

### 2. Mengambil Data Perbandingan untuk Makalah / Laporan

Jika Anda memerlukan tabel statistik komparatif dan data kuantitatif untuk dokumen laporan tugas kuliah, jalankan:

```powershell
python run_experiments.py
```

Script akan memproses batch simulasi Monte Carlo 10 replikasi per skenario dengan *Common Random Numbers* (CRN), lalu:
1. Menampilkan ringkasan eksekutif temuan analisis di terminal.
2. Menampilkan tabel perbandingan performa (*Mean ± Standar Deviasi*).
3. Otomatis mengekspor data lengkap ke file **`laporan_eksperimen.csv`** yang dapat langsung dibuka di Excel atau disalin ke dokumen Word.

---

## Logika & Metodologi Model

### 1. Proses Kedatangan Kendaraan
Kedatangan kendaraan pada masing-masing pendekat dimodelkan sebagai **Proses Poisson** stokastik. Waktu antar-kedatangan (*inter-arrival time*) dibangkitkan dari distribusi eksponensial menggunakan generator acak terisolasi (`random.Random(seed)`):

$$\Delta t \sim \mathrm{Exp}\left(\lambda = \frac{\text{volume}}{60}\right)$$

### 2. Pengendali Fixed-Time
Menggunakan siklus berulang yang kaku:
- Hijau NS: 30 detik
- Kuning NS: 3 detik
- All-Red (fase aman): 1 detik
- Hijau EW: 30 detik
- Kuning EW: 3 detik
- All-Red (fase aman): 1 detik

### 3. Pengendali Adaptive
- Memeriksa panjang antrean aktual pada sumbu NS dan EW.
- Memberikan lampu hijau ke sumbu dengan antrean terpanjang.
- Durasi hijau dibatasi antara batas minimum (15 detik) hingga batas maksimum (45 detik).
- **Fitur Anti-Starvation:** Jika suatu sumbu telah menunggu lampu merah selama $\ge 60$ detik, sumbu tersebut otomatis diprioritaskan pada fase berikutnya untuk mencegah kendaraan terabaikan.
- **Early Termination:** Jika antrean pada sumbu hijau telah habis terlayani, lampu hijau dapat diakhiri lebih awal untuk memberikan jalan ke arah lain yang membutuhkan.

---

**TrafficLab** — Proyek Akademik Mata Kuliah Pemodelan dan Simulasi.
