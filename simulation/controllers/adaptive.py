"""
Pengontrol Lampu Lalu Lintas Adaptive (Adaptif berbasis panjang antrean).
Menyesuaikan pilihan fase dan durasi hijau secara dinamis berdasarkan kondisi antrean
dengan perlindungan anti-starvation dan batas minimum/maksimum durasi hijau.
"""
import simpy
from simulation.controllers.base_controller import BaseController
from config import ADAPTIVE_CONFIG

class AdaptiveController(BaseController):
    """
    Pengontrol adaptif berbasis antrean:
    - Menghitung Q_NS = Q_N + Q_S dan Q_EW = Q_E + Q_W
    - Menerapkan aturan anti-starvation jika sumbu menunggu > max_red_time
    - Menghitung durasi hijau = clamp(min_green + seconds_per_vehicle * queue, min_green, max_green)
    - Mendukung early green termination jika antrean sumbu aktif habis setelah min_green
    - Wajib melalui fase kuning dan all-red pada setiap perpindahan fase.
    """
    def __init__(self, config: dict = None):
        super().__init__("adaptive")
        cfg = config or {}
        self.min_green = float(cfg.get("min_green", ADAPTIVE_CONFIG["min_green"]))
        self.max_green = float(cfg.get("max_green", ADAPTIVE_CONFIG["max_green"]))
        self.seconds_per_vehicle = float(cfg.get("seconds_per_vehicle", ADAPTIVE_CONFIG["seconds_per_vehicle"]))
        self.max_red_time = float(cfg.get("max_red_time", ADAPTIVE_CONFIG["max_red_time"]))
        self.yellow_duration = float(cfg.get("yellow_duration", ADAPTIVE_CONFIG["yellow_duration"]))
        self.all_red_duration = float(cfg.get("all_red_duration", ADAPTIVE_CONFIG["all_red_duration"]))
        
        # Sumbu terakhir yang mendapatkan fase hijau
        self.last_green_axis = "EW"  # Supaya pertama kali cenderung memilih NS jika imbang

    def decide_next_axis(self, engine) -> str:
        """
        Menentukan sumbu berikutnya ('NS' atau 'EW') yang berhak mendapatkan lampu hijau.
        Menerapkan prioritas anti-starvation dan perbandingan antrean gabungan.
        """
        now = engine.env.now
        signal = engine.signal
        q_n = len(engine.queues["N"])
        q_s = len(engine.queues["S"])
        q_e = len(engine.queues["E"])
        q_w = len(engine.queues["W"])

        q_ns = q_n + q_s
        q_ew = q_e + q_w

        red_wait_ns = signal.get_red_waiting_time("NS", now)
        red_wait_ew = signal.get_red_waiting_time("EW", now)

        starved_ns = (q_ns > 0) and (red_wait_ns >= self.max_red_time)
        starved_ew = (q_ew > 0) and (red_wait_ew >= self.max_red_time)

        # 1. Aturan Anti-Starvation: Prioritaskan sumbu yang menunggu melebihi batas
        if starved_ns and not starved_ew:
            return "NS"
        if starved_ew and not starved_ns:
            return "EW"
        if starved_ns and starved_ew:
            # Keduanya starved: pilih yang waktu tunggu merahnya paling lama
            return "NS" if red_wait_ns >= red_wait_ew else "EW"

        # 2. Pemilihan berbasis antrean
        if q_ns > 0 and q_ew == 0:
            return "NS"
        if q_ew > 0 and q_ns == 0:
            return "EW"
        if q_ns > 0 and q_ew > 0:
            if q_ns > q_ew:
                return "NS"
            elif q_ew > q_ns:
                return "EW"
            else:
                # Jumlah antrean sama -> pergantian bergantian (tie-break/alternation)
                return "EW" if self.last_green_axis == "NS" else "NS"

        # 3. Keduanya kosong -> pergantian bergantian agar adil
        return "EW" if self.last_green_axis == "NS" else "NS"

    def calculate_green_duration(self, queue_count: int) -> float:
        """
        Menghitung durasi lampu hijau berdasarkan jumlah antrean sumbu terpilih.
        green_duration = clamp(min_green + seconds_per_vehicle * queue, min_green, max_green)
        """
        calculated = self.min_green + (self.seconds_per_vehicle * queue_count)
        return max(self.min_green, min(self.max_green, calculated))

    def run_controller_process(self, engine):
        """
        Proses SimPy yang mengatur siklus lampu adaptif.
        """
        env = engine.env
        signal = engine.signal

        while True:
            # 1. Tentukan sumbu yang akan hijau berikutnya
            next_axis = self.decide_next_axis(engine)
            self.last_green_axis = next_axis

            # Hitung antrean sumbu terpilih pada saat keputusan dibuat
            if next_axis == "NS":
                selected_queue = len(engine.queues["N"]) + len(engine.queues["S"])
            else:
                selected_queue = len(engine.queues["E"]) + len(engine.queues["W"])

            # Hitung target durasi hijau
            target_green = self.calculate_green_duration(selected_queue)

            # 2. Nyalakan Hijau pada sumbu terpilih
            signal.set_phase(next_axis, env.now)
            engine.on_phase_changed(next_axis)

            # Layani minimal min_green terlebih dahulu
            yield env.timeout(self.min_green)
            remaining_green = target_green - self.min_green

            # 3. Waktu sisa hijau dengan pemeriksaan early termination setiap 1.0 detik
            # Jika antrean sumbu aktif sudah habis dan sumbu seberang punya antrean, hentikan hijau lebih awal
            step = 1.0
            while remaining_green > 0:
                dt = min(step, remaining_green)
                yield env.timeout(dt)
                remaining_green -= dt

                # Cek early green termination
                if next_axis == "NS":
                    current_active_q = len(engine.queues["N"]) + len(engine.queues["S"])
                    opposing_q = len(engine.queues["E"]) + len(engine.queues["W"])
                else:
                    current_active_q = len(engine.queues["E"]) + len(engine.queues["W"])
                    opposing_q = len(engine.queues["N"]) + len(engine.queues["S"])

                if current_active_q == 0 and opposing_q > 0:
                    # Antrean aktif kosong sementara sumbu lawan menunggu -> akhiri hijau
                    break

            # 4. Fase Kuning
            yellow_phase = "YELLOW_NS" if next_axis == "NS" else "YELLOW_EW"
            signal.set_phase(yellow_phase, env.now)
            engine.on_phase_changed(yellow_phase)
            yield env.timeout(self.yellow_duration)

            # 5. Fase All-Red (Pembersihan simpang)
            all_red_phase = "ALL_RED_1" if next_axis == "NS" else "ALL_RED_2"
            signal.set_phase(all_red_phase, env.now)
            engine.on_phase_changed(all_red_phase)
            yield env.timeout(self.all_red_duration)
