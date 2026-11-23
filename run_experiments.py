"""
Script CLI untuk Menjalankan Eksperimen Komparatif (Fixed-Time vs Adaptive)
dan Menyimpan Hasil ke CSV untuk Bahan Laporan Pemodelan & Simulasi.

Jalankan dengan perintah:
    python run_experiments.py
"""
import csv
import os
from simulation.experiments import run_batch_experiment

def main():
    print("=" * 80)
    print("TrafficLab - Menjalankan Batch Eksperimen Monte Carlo (CRN)")
    print("Membandingkan: Fixed-Time vs Adaptive Traffic Signal")
    print("=" * 80)
    print("Sedang memproses simulasi 10 replikasi per skenario...")

    res = run_batch_experiment(replications=10, duration=1800.0)

    print("\n" + "=" * 80)
    print("RINGKASAN TEMUAN EKSEKUTIF")
    print("=" * 80)
    for bullet in res.get("executive_summary", []):
        print(f" • {bullet}")

    print("\n" + "=" * 80)
    print("TABEL HASIL PERBANDINGAN (Mean ± Std Dev)")
    print("=" * 80)
    header = f"{'Skenario':<12} | {'Tunggu Fixed':<18} | {'Tunggu Adaptive':<18} | {'Efisiensi':<10} | {'Pemenang':<10}"
    print(header)
    print("-" * len(header))

    table = res.get("comparison_table", [])
    csv_rows = []

    for row in table:
        sc = row.get("scenario_name", "")
        wf = row.get("fixed_wait", "")
        wa = row.get("adaptive_wait", "")
        eff = row.get("wait_diff", "")
        win = row.get("best_method", "")
        print(f"{sc:<12} | {wf:<18} | {wa:<18} | {eff:<10} | {win:<10}")

        csv_rows.append({
            "Skenario": sc,
            "Waktu Tunggu Fixed": wf,
            "Waktu Tunggu Adaptive": wa,
            "Efisiensi Waktu Tunggu": eff,
            "Antrean Rata-rata Fixed": row.get("fixed_queue", ""),
            "Antrean Rata-rata Adaptive": row.get("adaptive_queue", ""),
            "Efisiensi Antrean": row.get("queue_diff", ""),
            "Throughput Fixed": row.get("fixed_tp", ""),
            "Throughput Adaptive": row.get("adaptive_tp", ""),
            "Metode Pemenang": win
        })

    # Ekspor ke file CSV
    csv_filename = "laporan_eksperimen.csv"
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    print("\n" + "=" * 80)
    print(f"Data lengkap telah diekspor ke file: {os.path.abspath(csv_filename)}")
    print("File CSV ini dapat langsung dibuka di Excel atau disalin ke dokumen laporan Word Anda.")
    print("=" * 80)

if __name__ == "__main__":
    main()