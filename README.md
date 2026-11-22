# TrafficLab — Simulasi dan Analisis Pengaturan Lampu Lalu Lintas

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

## Metode Simulasi

### Discrete Event Simulation dengan SimPy

Simulasi menggunakan waktu virtual SimPy (`env.now`). Kedatangan kendaraan pada setiap pendekat (Utara, Selatan, Timur, dan Barat) dimodelkan sebagai proses stokastik Poisson. Waktu antar-kedatangan dibangkitkan dari distribusi eksponensial:

$$
\Delta t_{\text{kedatangan}} \sim \operatorname{Exp}\left(\lambda = \frac{\text{rate}}{60}\right)
$$

`rate` dinyatakan dalam kendaraan per menit untuk setiap arah.

Untuk membandingkan Fixed-Time dan Adaptive secara lebih adil, eksperimen menggunakan **Common Random Numbers (CRN)**. Dengan *random seed* yang sama, pasangan eksperimen menggunakan pola kedatangan dan karakteristik kendaraan acak yang sama sehingga perbedaan hasil dapat dianalisis berdasarkan metode pengendalian yang diuji.

### Fixed-Time Traffic Signal

Metode Fixed-Time menggunakan urutan fase berulang berikut:

| Urutan | Fase | Durasi |
|---|---|---:|
| 1 | Hijau NS | 30 detik |
| 2 | Kuning NS | 3 detik |
| 3 | All-red | 1 detik |
| 4 | Hijau EW | 30 detik |
| 5 | Kuning EW | 3 detik |
| 6 | All-red | 1 detik |

Setelah urutan selesai, siklus kembali ke fase hijau NS.

### Adaptive Traffic Signal

Pengendali Adaptive menentukan fase berdasarkan jumlah kendaraan yang mengantre pada dua sumbu:

$$
Q_{NS} = Q_N + Q_S, \qquad Q_{EW} = Q_E + Q_W
$$

Aturan pengendali:

1. **Anti-starvation:** jika suatu sumbu memiliki kendaraan yang mengantre dan telah menunggu dalam status merah lebih dari 60 detik, sumbu tersebut diprioritaskan pada keputusan fase berikutnya.
2. **Pemilihan fase:** jika hanya satu sumbu yang memiliki antrean, sumbu tersebut dipilih. Jika keduanya memiliki antrean, sumbu dengan antrean gabungan lebih besar dipilih. Jika jumlah antrean sama atau keduanya kosong, sistem menggunakan pergantian bergantian sebagai *tie-break*.
3. **Durasi hijau:** durasi dihitung berdasarkan antrean sumbu terpilih dan dibatasi antara 15 hingga 45 detik:

   \[
   G = \operatorname{clamp}(15 + 1.5Q_{\text{terpilih}}, 15, 45)
   \]

4. **Pengakhiran hijau lebih awal:** setelah durasi hijau minimum 15 detik terpenuhi, fase dapat diakhiri lebih awal jika antrean sumbu aktif kosong sementara sumbu lawan memiliki antrean.
5. **Keselamatan persimpangan:** fase NS dan EW tidak boleh mendapatkan lampu hijau secara bersamaan. Pergantian fase selalu melewati lampu kuning selama 3 detik dan *all-red* selama 1 detik.

## Indikator Kinerja

TrafficLab menggunakan indikator berikut untuk mengevaluasi hasil simulasi:

1. **Rata-rata waktu tunggu kendaraan (detik).** Waktu tunggu kendaraan yang telah dilayani dihitung dari waktu kedatangan sampai mulai dilayani. Untuk kendaraan yang masih mengantre pada akhir simulasi, waktu tunggu dihitung sampai waktu akhir simulasi.

   \[
   \bar{W} = \frac{\sum w_i + \sum w_j}{N_{\text{total datang}}}
   \]

2. **Rata-rata panjang antrean berbobot waktu (kendaraan).** Dihitung berdasarkan luas di bawah kurva panjang antrean terhadap waktu simulasi:

   \[
   \bar{Q} = \frac{1}{T}\int_0^T Q(t)\,dt
   = \frac{\sum Q_k\Delta t_k}{T}
   \]

3. **Panjang antrean maksimum (kendaraan).** Menunjukkan nilai puncak antrean selama simulasi.
4. **Jumlah kendaraan datang, terlayani, dan tersisa.** Perhitungan mengikuti prinsip konservasi kendaraan:

   \[
   N_{\text{datang}} = N_{\text{terlayani}} + N_{\text{tersisa}}
   \]

5. **Throughput (kendaraan/menit).** Jumlah kendaraan yang berhasil dilayani dibagi durasi simulasi dalam menit:

   \[
   \text{Throughput} = \frac{N_{\text{terlayani}}}{T_{\text{menit}}}
   \]

## Skenario Eksperimen

Aplikasi menyediakan empat skenario bawaan dan opsi konfigurasi kustom. Nilai skenario bawaan merupakan parameter awal untuk eksperimen akademis, bukan data hasil pengukuran lapangan.

| Skenario | Utara (N) | Selatan (S) | Timur (E) | Barat (W) | Karakteristik |
|---|---:|---:|---:|---:|---|
| **Normal** | 8 | 8 | 8 | 8 | Volume seimbang di semua arah |
| **Padat NS** | 14 | 14 | 5 | 5 | Koridor Utara–Selatan lebih padat |
| **Padat EW** | 5 | 5 | 14 | 14 | Koridor Timur–Barat lebih padat |
| **Jam Sibuk** | 12 | 12 | 12 | 12 | Volume tinggi di seluruh arah |

Semua nilai pada tabel dinyatakan dalam **kendaraan/menit/arah** dan dapat disesuaikan melalui konfigurasi simulasi.

## Teknologi

| Bagian | Teknologi |
|---|---|
| Bahasa backend | Python 3.10 atau lebih baru |
| Web framework | Flask |
| Mesin simulasi DES | SimPy 4.1.2 |
| Frontend | HTML5, CSS3, Vanilla JavaScript (ES6+) |
| Animasi 2D | HTML5 Canvas API |
| Grafik | Chart.js 4.4.1 |
| Pengujian | pytest 9.2.0 |

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

### 3. Instal dependensi

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Jalankan aplikasi

```bash
python app.py
```

### 5. Buka aplikasi di browser

Akses alamat berikut:

```text
http://127.0.0.1:5000
```

> **Catatan:** Perintah di atas mengasumsikan aplikasi Flask berjalan pada alamat lokal dan port `5000`.

## Menjalankan Pengujian

Jalankan unit test dan integration test menggunakan:

```bash
pytest tests/ -v
```

Pengujian mencakup beberapa aspek berikut:

- Memastikan fase NS dan EW tidak pernah hijau secara bersamaan.
- Memastikan durasi hijau Adaptive berada dalam batas minimum dan maksimum.
- Memeriksa mekanisme *anti-starvation*.
- Memeriksa perhitungan waktu tunggu, termasuk kendaraan yang belum dilayani pada akhir simulasi.
- Memeriksa perhitungan rata-rata panjang antrean berbobot waktu.
- Memeriksa reproduktibilitas *random seed* dan penggunaan CRN.
- Memeriksa konservasi jumlah kendaraan: kendaraan datang = kendaraan terlayani + kendaraan tersisa.
- Memeriksa siklus hidup API, termasuk pembuatan sesi, pemajuan simulasi, pengambilan status, reset, dan eksperimen.

## Batasan Model

- Model merupakan abstraksi untuk keperluan pembelajaran dan analisis komparatif, bukan mikrosimulasi lalu lintas perkotaan skala penuh.
- Kendaraan hanya dimodelkan bergerak lurus. Belok kiri, belok kanan, putar balik (*U-turn*), dan pergerakan pejalan kaki tidak dimodelkan.
- Sesi simulasi disimpan di memori backend. Jika server dihentikan atau dijalankan ulang, sesi yang sedang aktif akan kembali ke kondisi awal.
- Parameter skenario merupakan nilai eksperimen yang dapat diubah. Hasil simulasi tidak dapat langsung dianggap sebagai rekomendasi pengaturan lampu lalu lintas untuk persimpangan nyata tanpa kalibrasi dan validasi menggunakan data lapangan.

---

**TrafficLab** — Proyek akademik mata kuliah Pemodelan dan Simulasi.
