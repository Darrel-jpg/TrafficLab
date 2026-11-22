# TrafficLab — Simulasi dan Analisis Pengaturan Lampu Lalu Lintas

Aplikasi web interaktif untuk pemodelan, simulasi, dan analisis komparatif pengaturan lampu lalu lintas pada persimpangan jalan empat arah. Aplikasi ini menggunakan **Python Flask** sebagai backend, **SimPy** sebagai mesin *Discrete Event Simulation* (DES) utama, serta **HTML5 Canvas** dan **Chart.js** untuk animasi 2D dan visualisasi data live.

---

## 1. Latar Belakang dan Tujuan Proyek

Aplikasi ini dikembangkan untuk tugas mata kuliah **Pemodelan dan Simulasi**. Fokus penelitian dan eksperimen adalah membandingkan dua metode pengendalian lampu lalu lintas:

1. **Fixed-Time Traffic Signal (Waktu Tetap)**: Lampu lalu lintas beroperasi berdasarkan siklus waktu tetap yang telah ditentukan sebelumnya, tanpa mempertimbangkan kondisi kepadatan antrean kendaraan saat itu.
2. **Adaptive Traffic Signal (Responsif Antrean)**: Pemilihan fase dan durasi lampu hijau ditentukan secara dinamis berdasarkan akumulasi panjang antrean kendaraan pada masing-masing sumbu, dilengkapi dengan batasan minimum/maksimum serta mekanisme *anti-starvation*.

**Tujuan utama:** Mengetahui bagaimana kedua metode memengaruhi waktu tunggu rata-rata, panjang antrean berbobot waktu, antrean puncak, dan throughput pada berbagai kondisi volume lalu lintas.

---

## 2. Fitur Utama

- **Mesin DES Murni (SimPy)**: Virtual time, antrean, pergantian fase sinyal, dan pelepasan kendaraan dikelola secara stokastik oleh SimPy di backend, bukan sekadar animasi timer JavaScript.
- **Visualisasi Animasi 2D Interaktif**: Persimpangan 4 arah tampak atas dengan marka jalan, lampu lalu lintas bercahaya, antrean teratur, serta kendaraan motor dan mobil yang melintas mulus.
- **Panel Kontrol Interaktif**: Pilihan metode (*Fixed-Time* vs *Adaptive*), 4 skenario default (*Normal*, *Padat NS*, *Padat EW*, *Jam Sibuk*, dan *Kustom*), pengaturan rasio motor/mobil, seed acak, durasi simulasi, serta kontrol laju kecepatan animasi (1x, 2x, 5x, 10x).
- **Dashboard Statistik Live**: Kartu KPI diperbarui secara real-time dari snapshot SimPy tanpa angka fiktif:
  - Rata-rata waktu tunggu (detik)
  - Panjang antrean rata-rata berbobot waktu (*time-weighted average queue*)
  - Antrean maksimum jaringan
  - Total kendaraan datang, terlayani, dan tersisa
  - Throughput persimpangan (kendaraan/menit)
- **Grafik Live SimPy**: Dinamika panjang antrean sumbu NS vs sumbu EW seiring waktu virtual.
- **Batch Experiment Runner**: Eksperimen komparatif Monte Carlo otomatis dengan metode *Common Random Numbers* (CRN) untuk perbandingan yang adil pada seed kedatangan yang sama. Menyajikan ringkasan eksekutif, 4 grafik perbandingan, tabel statistik (Mean ± Standar Deviasi), dan fitur ekspor data ke CSV.
- **Desain Modern Light Mode**: Antarmuka bersih, ramah untuk presentasi akademik, dengan palet warna terinspirasi dari lalu lintas dan jalan aspal berdaya kontras tinggi.

---

## 3. Teknologi yang Digunakan

- **Backend**: Python 3.10+ / Python 3.14, Flask
- **Simulation Engine**: SimPy 4.1.2
- **Testing**: Pytest 9.2.0
- **Frontend**: HTML5, CSS3 Modern, Vanilla JavaScript (ES6+)
- **Canvas 2D**: HTML5 Canvas API (60 FPS render loop)
- **Visualisasi Data**: Chart.js 4.4.1

---

## 4. Struktur Direktori Proyek

```text
Simulasi Lalu Lintas/
├── app.py                     # Entry point server web Flask
├── config.py                  # Konfigurasi parameter terpusat & skenario
├── README.md                  # Dokumentasi teknis lengkap
├── simulation/                # Modul inti simulasi SimPy (DES)
│   ├── __init__.py
│   ├── engine.py              # SimulationEngine (orkestrasi SimPy DES)
│   ├── vehicle.py             # Model kendaraan (Motor & Mobil)
│   ├── arrivals.py            # Generator kedatangan Poisson/Eksponensial
│   ├── traffic_signal.py      # Pengelola sinyal & penegak invariant keselamatan
│   ├── metrics.py             # Pelacak metrik tanpa bias & time-weighted average
│   ├── experiments.py         # Eksekutor batch eksperimen Monte Carlo & CRN
│   └── controllers/           # Algoritma pengatur lampu lalu lintas
│       ├── __init__.py
│       ├── base_controller.py
│       ├── fixed_time.py      # Siklus waktu tetap
│       └── adaptive.py        # Pengendali adaptif berbasis antrean
├── routes/
│   ├── __init__.py
│   └── api.py                 # Endpoint REST API JSON
├── templates/
│   └── index.html             # Halaman antarmuka web utama
├── static/
│   ├── css/
│   │   └── style.css          # Desain light mode modern & responsif
│   └── js/
│       ├── api.js             # HTTP client untuk backend
│       ├── simulation-renderer.js # Renderer 2D Canvas persimpangan & kendaraan
│       ├── charts.js          # Pengelola grafik Chart.js (live & eksperimen)
│       ├── dashboard.js       # Kontrol simulasi, KPI live, & eksperimen
│       └── app.js             # Inisialisasi aplikasi
```

---

## 5. Model Simulasi dan Algoritma

### 5.1 Paradigma Discrete Event Simulation (SimPy)

Sistem dimodelkan menggunakan waktu diskrit virtual SimPy (`env.now`). Kedatangan kendaraan pada setiap pendekat (Utara, Selatan, Timur, Barat) bersifat stokastik mengikuti proses Poisson, dibangkitkan dari distribusi eksponensial waktu antar-kedatangan:

$$\Delta t_{kedatangan} \sim \text{Exp}\left(\lambda = \frac{\text{rate}}{60}\right)$$

Untuk menjaga perbandingan yang adil (*fair comparison*) antara Fixed-Time dan Adaptive, sistem menggunakan teknik **Common Random Numbers (CRN)**. Dengan seed yang sama, kedua metode dihadapkan pada urutan, waktu tiba, dan tipe kendaraan yang persis identik.

### 5.2 Algoritma Pengaturan Lampu

#### A. Fixed-Time Signal
Beroperasi dengan siklus fase tetap:
1. Hijau NS (30 detik)
2. Kuning NS (3 detik)
3. All-Red 1 (1 detik)
4. Hijau EW (30 detik)
5. Kuning EW (3 detik)
6. All-Red 2 (1 detik)
7. Ulangi siklus secara berkala.

#### B. Adaptive Signal Berbasis Antrean
1. **Perhitungan Antrean Gabungan**:
   $$Q_{NS} = Q_N + Q_S, \quad Q_{EW} = Q_E + Q_W$$
2. **Aturan Anti-Starvation**: Jika antrean pada suatu sumbu telah menunggu dalam status merah melebihi ambang batas $T_{max\_red} = 60$ detik dan terdapat kendaraan mengantre, sumbu tersebut diprioritaskan pada siklus keputusan berikutnya.
3. **Pemilihan Sumbu**:
   - Jika hanya satu sumbu yang memiliki antrean, pilih sumbu tersebut.
   - Jika kedua sumbu memiliki antrean, pilih sumbu dengan antrean gabungan lebih besar.
   - Jika jumlah antrean seimbang, gunakan pergantian bergantian (*alternation/tie-break*).
   - Jika kedua antrean kosong, gunakan pergantian bergantian.
4. **Perhitungan Durasi Hijau**:
   $$\text{green\_duration} = \text{clamp}(\text{min\_green} + 1.5 \times Q_{\text{terpilih}}, \ 15\text{s}, \ 45\text{s})$$
5. **Early Green Termination**: Setelah melayani durasi minimal $\text{min\_green} = 15$ detik, jika antrean sumbu aktif telah kosong sementara sumbu lawan memiliki kendaraan menunggu, fase hijau dihentikan lebih awal untuk beralih ke kuning dan all-red.
6. **Keselamatan Simpang (Invariant)**: Fase NS dan EW **tidak pernah** hijau bersamaan. Setiap pergantian fase wajib melalui kuning (3s) dan all-red (1s).

---

## 6. Definisi Indikator Kinerja (KPI)

1. **Rata-rata Waktu Tunggu Kendaraan (detik)**:
   Dihitung tanpa bias atas seluruh kendaraan yang tiba:
   - Kendaraan yang sudah dilayani: $w_i = t_{\text{mulai\_servis}} - t_{\text{tiba}}$
   - Kendaraan yang masih mengantre pada akhir simulasi: $w_j = t_{\text{akhir}} - t_{\text{tiba}}$
   $$\bar{W} = \frac{\sum w_i + \sum w_j}{N_{\text{total\_datang}}}$$
2. **Panjang Antrean Rata-rata Berbobot Waktu (kendaraan)**:
   Dihitung secara integral kontinyu terhadap waktu:
   $$\bar{Q} = \frac{1}{T} \int_0^T Q(t) \, dt = \frac{\sum Q_k \cdot \Delta t_k}{T}$$
3. **Panjang Antrean Maksimum (kendaraan)**: Puncak antrean terpanjang yang pernah tercapai pada suatu pendekat dan jaringan.
4. **Total Kendaraan Datang, Terlayani, dan Tersisa**: Mematuhi hukum konservasi:
   $$N_{\text{datang}} = N_{\text{terlayani}} + N_{\text{tersisa}}$$
5. **Throughput (kendaraan/menit)**:
   $$\text{Throughput} = \frac{N_{\text{terlayani}}}{\text{menit virtual}}$$

---

## 7. Skenario Eksperimen Default

Nilai berikut adalah parameter awal ilustratif untuk eksperimen akademis:

| Skenario | Utara (N) | Selatan (S) | Timur (E) | Barat (W) | Karakteristik |
|---|:---:|:---:|:---:|:---:|---|
| **Normal** | 8 | 8 | 8 | 8 | Volume seimbang di semua arah |
| **Padat NS** | 14 | 14 | 5 | 5 | Koridor Utara–Selatan padat |
| **Padat EW** | 5 | 5 | 14 | 14 | Koridor Timur–Barat padat |
| **Jam Sibuk** | 12 | 12 | 12 | 12 | Beban tinggi di seluruh penjuru |

*Catatan: Angka di atas dinyatakan dalam kendaraan/menit/arah dan dapat diatur secara manual oleh pengguna.*

---

## 8. Panduan Menjalankan Aplikasi (Tanpa Virtual Environment)

### Persyaratan Sistem
- Python 3.10 atau versi lebih baru (termasuk Python 3.14).
- Peramban web modern (Google Chrome, Microsoft Edge, Mozilla Firefox, dsb).

### Langkah Menjalankan Langsung:

1. Buka terminal (PowerShell atau Command Prompt) pada direktori proyek:
   ```powershell
   cd "c:\Users\darre\Documents\Coding\Pemodelan dan Simulasi\Simulasi Lalu Lintas"
   ```

2. Instal dependensi langsung ke Python sistem:
   ```powershell
   pip install -r requirements.txt
   ```

3. Jalankan aplikasi web:
   ```powershell
   python app.py
   ```

4. Buka peramban dan akses alamat:
   ```text
   http://127.0.0.1:5000
   ```

---

## 9. Menjalankan Pengujian Otomatis (Unit & Integration Tests)

Seluruh logika model, invariant sinyal, perhitungan metrik, dan endpoint API telah dilengkapi dengan pengujian otomatis menggunakan **pytest**.

Untuk menjalankan seluruh rangkaian tes:

```powershell
pytest tests/ -v
```

Hasil pengujian mencakup:
- Verifikasi keselamatan lampu (fase hijau tidak pernah bertabrakan).
- Batas durasi hijau minimum dan maksimum pengendali adaptif.
- Mekanisme anti-starvation pada sumbu yang mengalami waktu tunggu merah lama.
- Perhitungan waktu tunggu tanpa bias (menyertakan kendaraan yang belum terlayani).
- Perhitungan panjang antrean rata-rata berbobot waktu (*time-weighted average*).
- Reproduktibilitas random seed dan kesesuaian Common Random Numbers.
- Hukum konservasi kendaraan ($N_{\text{datang}} = N_{\text{terlayani}} + N_{\text{tersisa}}$).
- Pengujian siklus hidup API (create, advance, state, reset, experiments).

---

## 10. Catatan dan Keterbatasan Model

- Model ini merupakan representasi terabstraksi untuk kebutuhan analisis komparatif dalam perkuliahan Pemodelan dan Simulasi, bukan replika mikrosimulasi lalu lintas perkotaan skala penuh.
- Kendaraan hanya bergerak lurus; manuver belok kiri, belok kanan, putar balik (*U-turn*), dan pejalan kaki diabstraksikan tidak dimodelkan.
- Sesi simulasi disimpan dalam memori RAM backend server. Jika server di-restart, sesi aktif akan direset kembali ke kondisi awal.
