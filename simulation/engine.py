"""
Mesin Utama Discrete Event Simulation (DES) berbasis SimPy.
Mengelola virtual time, proses kedatangan kendaraan, antrean,
pengontrol lampu lalu lintas, dan pergerakan kendaraan melewati persimpangan.
"""
import uuid
import random
import simpy
from typing import Dict, List, Optional, Any

from config import (
    DEFAULT_SIMULATION_DURATION,
    DEFAULT_RANDOM_SEED,
    DEFAULT_VEHICLE_MIX,
    VEHICLE_SERVICE_TIME
)
from simulation.vehicle import Vehicle
from simulation.arrivals import ArrivalGenerator
from simulation.traffic_signal import TrafficSignal
from simulation.controllers.fixed_time import FixedTimeController
from simulation.controllers.adaptive import AdaptiveController
from simulation.metrics import MetricsTracker

class SimulationEngine:
    """
    Mesin simulasi lalu lintas diskrit berbasis SimPy.
    """
    def __init__(
        self,
        simulation_id: Optional[str] = None,
        method: str = "fixed_time",
        scenario_name: str = "normal",
        arrival_rates: Optional[Dict[str, float]] = None,
        duration: float = DEFAULT_SIMULATION_DURATION,
        seed: int = DEFAULT_RANDOM_SEED,
        motor_ratio: float = DEFAULT_VEHICLE_MIX["motor_ratio"],
        controller_config: Optional[Dict[str, Any]] = None
    ):
        self.id = simulation_id or str(uuid.uuid4())[:8]
        self.method = method.lower()
        self.scenario_name = scenario_name
        self.max_duration = float(duration)
        self.seed = int(seed)
        self.motor_ratio = float(motor_ratio)
        self.controller_config = controller_config or {}

        # Default arrival rates jika tidak diberikan
        default_rates = {"N": 8.0, "S": 8.0, "E": 8.0, "W": 8.0}
        self.arrival_rates = arrival_rates or default_rates

        # Inisialisasi SimPy Environment dan PRNG
        self.env = simpy.Environment()
        self.rng = random.Random(self.seed)

        # Status Sinyal & Antrean Pendekat
        self.signal = TrafficSignal(initial_time=0.0)
        self.queues: Dict[str, List[Vehicle]] = {
            "N": [], "S": [], "E": [], "W": []
        }
        self.crossing_vehicles: List[Vehicle] = []

        # Pelacak Metrik
        self.metrics = MetricsTracker()

        # Status Simulasi: "ready", "running", "paused", "finished"
        self.status = "ready"

        # SimPy Events untuk sinkronisasi proses server pendekat
        self.phase_event = self.env.event()
        self.arrival_events: Dict[str, simpy.Event] = {
            "N": self.env.event(),
            "S": self.env.event(),
            "E": self.env.event(),
            "W": self.env.event()
        }

        # Setup Controller
        if self.method == "adaptive":
            self.controller = AdaptiveController(self.controller_config)
        else:
            self.controller = FixedTimeController(self.controller_config)

        # Setup Komponen Proses SimPy
        self._setup_processes()

    def _setup_processes(self):
        """Mendaftarkan proses-proses SimPy ke environment."""
        # 1. Generator kedatangan kendaraan untuk 4 arah
        self.generators = {}
        for app in ("N", "S", "E", "W"):
            rate = float(self.arrival_rates.get(app, 8.0))
            self.generators[app] = ArrivalGenerator(
                env=self.env,
                approach=app,
                rate_per_min=rate,
                motor_ratio=self.motor_ratio,
                rng=self.rng,
                on_arrival_callback=self.on_vehicle_arrived
            )

        # 2. Proses Controller Lampu Lalu Lintas
        self.controller_process = self.env.process(
            self.controller.run_controller_process(self)
        )

        # 3. Proses Server Pendekat (pelayanan kendaraan per arah)
        self.approach_processes = {}
        for app in ("N", "S", "E", "W"):
            self.approach_processes[app] = self.env.process(
                self._approach_server(app)
            )

        # 4. Proses pencatatan berkala untuk riwayat grafik
        self.sampler_process = self.env.process(self._periodic_sampler())

    def on_vehicle_arrived(self, vehicle: Vehicle):
        """Callback ketika kendaraan baru tiba dari generator."""
        app = vehicle.approach
        vehicle.queue_index = len(self.queues[app])
        self.queues[app].append(vehicle)

        # Catat metrik
        self.metrics.record_arrival(vehicle, self.env.now)
        self._notify_queue_changed()

        # Picu event kedatangan agar server pendekat bangun jika sedang tidur
        if not self.arrival_events[app].triggered:
            self.arrival_events[app].succeed()
        self.arrival_events[app] = self.env.event()

    def on_phase_changed(self, new_phase: str):
        """Callback ketika fase lampu lalu lintas berganti."""
        self._notify_queue_changed()

        # Picu event fase agar server pendekat bereaksi terhadap perubahan lampu
        if not self.phase_event.triggered:
            self.phase_event.succeed()
        self.phase_event = self.env.event()

    def _notify_queue_changed(self):
        """Memperbarui status antrean ke metrics tracker."""
        current_lengths = {app: len(self.queues[app]) for app in ("N", "S", "E", "W")}
        self.metrics.update_queue_state(current_lengths, self.env.now)

    def _approach_server(self, approach: str):
        """
        Proses pelayanan kendaraan di garis henti suatu pendekat.
        Kendaraan HANYA boleh mulai melintasi saat lampu hijau.
        Kendaraan yang sudah mulai melintas akan menyelesaikan lintasannya.
        """
        while True:
            # Jika lampu tidak hijau atau antrean kosong, tunggu perubahan fase atau kendaraan baru
            if not self.signal.is_green_for(approach) or len(self.queues[approach]) == 0:
                yield self.phase_event | self.arrival_events[approach]
                continue

            # Lampu hijau dan ada kendaraan dalam antrean
            vehicle = self.queues[approach].pop(0)
            
            # Perbarui queue_index kendaraan di belakangnya
            for idx, v in enumerate(self.queues[approach]):
                v.queue_index = idx

            self._notify_queue_changed()

            # Kendaraan mulai melintasi persimpangan
            vehicle.start_crossing(self.env.now)
            self.crossing_vehicles.append(vehicle)

            # Jalankan proses melintasi persimpangan secara independen
            self.env.process(self._vehicle_crossing(vehicle))

            # Headway pelepasan kendaraan berikutnya di lajur ini (saturation flow)
            # Motor lebih rapat (1.2 detik), mobil butuh jarak aman (2.0 detik)
            dispatch_headway = 1.2 if vehicle.type == "motor" else 2.0
            yield self.env.timeout(dispatch_headway)

    def _vehicle_crossing(self, vehicle: Vehicle):
        """
        Proses kendaraan melintasi kotak persimpangan hingga keluar.
        """
        yield self.env.timeout(vehicle.crossing_duration)
        vehicle.finish_crossing(self.env.now)

        if vehicle in self.crossing_vehicles:
            self.crossing_vehicles.remove(vehicle)

        self.metrics.record_served(vehicle, self.env.now)

    def _periodic_sampler(self):
        """Mencatat titik riwayat berkala untuk grafik setiap 2 detik virtual."""
        while True:
            self.metrics.sample_history_point(self.env.now)
            yield self.env.timeout(2.0)

    def advance(self, delta_seconds: float) -> Dict[str, Any]:
        """
        Memajukan waktu virtual SimPy sebesar delta_seconds.
        """
        if self.status == "finished":
            return self.get_state()

        self.status = "running"
        target_time = min(self.max_duration, self.env.now + float(delta_seconds))

        if target_time > self.env.now:
            self.env.run(until=target_time)

        if self.env.now >= self.max_duration:
            self.status = "finished"

        return self.get_state()

    def run_until_completion(self) -> Dict[str, Any]:
        """
        Menjalankan simulasi langsung sampai durasi selesai (mode cepat untuk batch eksperimen).
        """
        self.status = "running"
        self.env.run(until=self.max_duration)
        self.status = "finished"
        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """
        Mengambil snapshot state lengkap untuk dikirim ke frontend.
        """
        current_time = self.env.now
        
        # Kirim maksimal 20 kendaraan terdepan per lajur antrean untuk efisiensi transfer
        queue_snapshot = {}
        for app in ("N", "S", "E", "W"):
            queue_snapshot[app] = [
                v.to_dict(current_time) for v in self.queues[app][:20]
            ]

        crossing_snapshot = [
            v.to_dict(current_time) for v in self.crossing_vehicles
        ]

        # Ambil sampel terakhir untuk data time-series
        recent_history = self.metrics.history[-40:] if self.metrics.history else []

        return {
            "simulation_id": self.id,
            "status": self.status,
            "method": self.method,
            "scenario": self.scenario_name,
            "simulation_time": round(current_time, 2),
            "max_duration": self.max_duration,
            "active_phase": self.signal.active_phase,
            "signal_states": dict(self.signal.states),
            "queues": {app: len(self.queues[app]) for app in ("N", "S", "E", "W")},
            "queue_vehicles": queue_snapshot,
            "crossing_vehicles": crossing_snapshot,
            "metrics": self.metrics.get_summary(current_time),
            "history": recent_history
        }
