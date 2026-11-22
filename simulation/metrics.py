"""
Pelacak dan penghitung metrik kinerja simulasi lalu lintas.
Menghitung rata-rata waktu tunggu tanpa bias, panjang antrean berbobot waktu,
throughput, dan riwayat deret waktu untuk visualisasi grafik.
"""
from typing import Dict, List, Any
from simulation.vehicle import Vehicle

class MetricsTracker:
    """
    Menghitung semua indikator output yang dipersyaratkan:
    - Rata-rata waktu tunggu kendaraan (termasuk yang masih antre)
    - Waktu tunggu rata-rata per pendekat (N, S, E, W)
    - Panjang antrean maksimum (per arah dan total jaringan)
    - Rata-rata panjang antrean berbobot waktu (time-weighted average)
    - Total kendaraan datang, terlayani, dan tersisa
    - Throughput (kendaraan/menit)
    - Riwayat data time-series untuk grafik
    """
    def __init__(self):
        # Koleksi kendaraan
        self.all_vehicles: List[Vehicle] = []
        self.vehicles_by_approach: Dict[str, List[Vehicle]] = {
            "N": [], "S": [], "E": [], "W": []
        }
        self.served_vehicles: List[Vehicle] = []

        # Rekor antrean maksimum
        self.max_queue: Dict[str, int] = {"N": 0, "S": 0, "E": 0, "W": 0}
        self.max_total_queue: int = 0

        # Variabel untuk time-weighted average queue
        self.last_update_time: float = 0.0
        self.queue_area: Dict[str, float] = {"N": 0.0, "S": 0.0, "E": 0.0, "W": 0.0}
        self.total_queue_area: float = 0.0
        
        # Panjang antrean saat ini
        self.current_queues: Dict[str, int] = {"N": 0, "S": 0, "E": 0, "W": 0}

        # Riwayat deret waktu untuk grafik (diperbarui berkala)
        self.history: List[Dict[str, Any]] = []
        self.last_history_sample_time: float = -1.0

    def record_arrival(self, vehicle: Vehicle, current_time: float):
        """Mencatat kendaraan baru yang tiba."""
        self.all_vehicles.append(vehicle)
        self.vehicles_by_approach[vehicle.approach].append(vehicle)

    def record_served(self, vehicle: Vehicle, current_time: float):
        """Mencatat kendaraan yang telah selesai melintasi persimpangan."""
        self.served_vehicles.append(vehicle)

    def update_queue_state(self, queues: Dict[str, int], current_time: float):
        """
        Memperbarui status antrean dan mengintegrasikan area di bawah kurva antrean
        untuk menghitung time-weighted average queue length secara matematis.
        """
        dt = current_time - self.last_update_time
        if dt > 0:
            for approach in ("N", "S", "E", "W"):
                self.queue_area[approach] += self.current_queues[approach] * dt
            current_total = sum(self.current_queues.values())
            self.total_queue_area += current_total * dt
            self.last_update_time = current_time

        # Perbarui nilai antrean sekarang
        for approach in ("N", "S", "E", "W"):
            q_len = queues.get(approach, 0)
            self.current_queues[approach] = q_len
            if q_len > self.max_queue[approach]:
                self.max_queue[approach] = q_len

        total_q = sum(self.current_queues.values())
        if total_q > self.max_total_queue:
            self.max_total_queue = total_q

    def sample_history_point(self, current_time: float):
        """
        Menyimpan snapshot data deret waktu untuk grafik jika interval mencukupi (misal setiap 2 detik).
        """
        # Hindari sampel ganda pada waktu yang persis sama
        if current_time - self.last_history_sample_time < 1.0:
            return

        self.last_history_sample_time = current_time
        
        q_ns = self.current_queues["N"] + self.current_queues["S"]
        q_ew = self.current_queues["E"] + self.current_queues["W"]
        total_q = q_ns + q_ew

        point = {
            "time": round(current_time, 1),
            "queue_ns": q_ns,
            "queue_ew": q_ew,
            "queue_total": total_q,
            "arrived": len(self.all_vehicles),
            "served": len(self.served_vehicles)
        }
        self.history.append(point)

    def get_summary(self, current_time: float) -> Dict[str, Any]:
        """
        Menghasilkan ringkasan metrik lengkap berdasarkan waktu simulasi virtual saat ini.
        """
        # Pastikan integrasi area antrean diperbarui hingga waktu saat ini
        self.update_queue_state(self.current_queues, current_time)

        total_arrived = len(self.all_vehicles)
        total_served = len(self.served_vehicles)
        
        # Kendaraan tersisa = kendaraan yang masih antre atau sedang menyeberang
        vehicles_remaining = total_arrived - total_served

        # Rata-rata waktu tunggu kendaraan keseluruhan (seluruh kendaraan yang datang)
        # Kendaraan dilayani: service_start_time - arrival_time
        # Kendaraan mengantre: current_time - arrival_time
        if total_arrived > 0:
            total_waiting_time = sum(v.get_waiting_time(current_time) for v in self.all_vehicles)
            avg_waiting_time = total_waiting_time / total_arrived
        else:
            avg_waiting_time = 0.0

        # Waktu tunggu per arah
        waiting_by_approach = {}
        for app in ("N", "S", "E", "W"):
            app_vehicles = self.vehicles_by_approach[app]
            if app_vehicles:
                app_total_wait = sum(v.get_waiting_time(current_time) for v in app_vehicles)
                waiting_by_approach[app] = round(app_total_wait / len(app_vehicles), 2)
            else:
                waiting_by_approach[app] = 0.0

        # Time-weighted average queue
        effective_time = max(current_time, 1e-5)
        avg_queue_by_approach = {
            app: round(self.queue_area[app] / effective_time, 2)
            for app in ("N", "S", "E", "W")
        }
        time_weighted_avg_queue = round(self.total_queue_area / effective_time, 2)

        # Throughput: kendaraan terlayani per menit virtual
        sim_minutes = current_time / 60.0
        throughput = round(total_served / sim_minutes, 2) if sim_minutes > 0 else 0.0

        return {
            "simulation_time": round(current_time, 2),
            "total_arrived": total_arrived,
            "total_served": total_served,
            "vehicles_remaining": vehicles_remaining,
            "avg_waiting_time": round(avg_waiting_time, 2),
            "waiting_by_approach": waiting_by_approach,
            "max_queue": dict(self.max_queue),
            "max_total_queue": self.max_total_queue,
            "time_weighted_avg_queue": time_weighted_avg_queue,
            "avg_queue_by_approach": avg_queue_by_approach,
            "throughput": throughput,
            "current_queues": dict(self.current_queues)
        }
