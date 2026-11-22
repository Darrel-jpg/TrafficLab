"""
Konfigurasi Terpusat untuk TrafficLab - Simulasi Lalu Lintas.
Menyimpan parameter default simulasi, skenario, lampu lalu lintas, dan karakteristik kendaraan.
"""

from typing import Dict, Any

# Pengaturan Umum Aplikasi
APP_NAME = "TrafficLab — Simulasi dan Analisis Lalu Lintas"
DEFAULT_SIMULATION_DURATION = 1800.0  # 30 menit virtual dalam detik
DEFAULT_RANDOM_SEED = 42

# Skenario Default (satuan: kendaraan / menit / arah)
DEFAULT_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "normal": {
        "id": "normal",
        "name": "Normal",
        "description": "Volume kendaraan relatif seimbang di semua arah.",
        "rates": {"N": 8.0, "S": 8.0, "E": 8.0, "W": 8.0}
    },
    "padat_ns": {
        "id": "padat_ns",
        "name": "Padat NS",
        "description": "Sumbu Utara–Selatan lebih padat dibanding Timur–Barat.",
        "rates": {"N": 14.0, "S": 14.0, "E": 5.0, "W": 5.0}
    },
    "padat_ew": {
        "id": "padat_ew",
        "name": "Padat EW",
        "description": "Sumbu Timur–Barat lebih padat dibanding Utara–Selatan.",
        "rates": {"N": 5.0, "S": 5.0, "E": 14.0, "W": 14.0}
    },
    "jam_sibuk": {
        "id": "jam_sibuk",
        "name": "Jam Sibuk",
        "description": "Semua arah mengalami peningkatan volume kendaraan tinggi.",
        "rates": {"N": 12.0, "S": 12.0, "E": 12.0, "W": 12.0}
    }
}

# Komposisi Kendaraan Default
DEFAULT_VEHICLE_MIX = {
    "motor_ratio": 0.70,  # 70% motor
    "mobil_ratio": 0.30   # 30% mobil
}

# Waktu Servis / Lintasan Kendaraan Melewati Persimpangan (detik)
# Motor lebih lincah dan cepat keluar simpang dibanding mobil
VEHICLE_SERVICE_TIME = {
    "motor": 1.5,
    "mobil": 2.5
}

# Panjang dan Spasi Kendaraan (untuk representasi antrean visual)
VEHICLE_LENGTHS = {
    "motor": 18,  # piksel
    "mobil": 34   # piksel
}
VEHICLE_GAP = 6   # piksel antar kendaraan dalam antrean

# Konfigurasi Lampu Lalu Lintas Fixed-Time
FIXED_TIME_CONFIG = {
    "green_ns": 30.0,
    "yellow_ns": 3.0,
    "all_red_1": 1.0,
    "green_ew": 30.0,
    "yellow_ew": 3.0,
    "all_red_2": 1.0
}

# Konfigurasi Lampu Lalu Lintas Adaptive
ADAPTIVE_CONFIG = {
    "min_green": 15.0,
    "max_green": 45.0,
    "seconds_per_vehicle": 1.5,
    "max_red_time": 60.0,       # Batas anti-starvation (detik)
    "yellow_duration": 3.0,
    "all_red_duration": 1.0
}

# Konfigurasi Eksperimen Batch
EXPERIMENT_CONFIG = {
    "default_replications": 10,
    "min_replications": 1,
    "max_replications": 30,
    "default_duration": 1800.0
}
