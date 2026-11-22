"""
Pengontrol Lampu Lalu Lintas Fixed-Time (Waktu Tetap).
Mempertahankan durasi hijau, kuning, dan all-red yang tetap
terlepas dari kepadatan antrean kendaraan.
"""
import simpy
from simulation.controllers.base_controller import BaseController
from config import FIXED_TIME_CONFIG

class FixedTimeController(BaseController):
    """
    Pengontrol waktu tetap dengan siklus berurutan:
    1. NS Green (30s)
    2. NS Yellow (3s)
    3. All-Red 1 (1s)
    4. EW Green (30s)
    5. EW Yellow (3s)
    6. All-Red 2 (1s)
    """
    def __init__(self, config: dict = None):
        super().__init__("fixed_time")
        cfg = config or {}
        self.green_ns = float(cfg.get("green_ns", FIXED_TIME_CONFIG["green_ns"]))
        self.yellow_ns = float(cfg.get("yellow_ns", FIXED_TIME_CONFIG["yellow_ns"]))
        self.all_red_1 = float(cfg.get("all_red_1", FIXED_TIME_CONFIG["all_red_1"]))
        self.green_ew = float(cfg.get("green_ew", FIXED_TIME_CONFIG["green_ew"]))
        self.yellow_ew = float(cfg.get("yellow_ew", FIXED_TIME_CONFIG["yellow_ew"]))
        self.all_red_2 = float(cfg.get("all_red_2", FIXED_TIME_CONFIG["all_red_2"]))

    def run_controller_process(self, engine):
        """
        Proses SimPy yang mengatur transisi fase fixed-time secara kontinu.
        """
        env = engine.env
        signal = engine.signal

        while True:
            # 1. Fase Hijau NS
            signal.set_phase("NS", env.now)
            engine.on_phase_changed("NS")
            yield env.timeout(self.green_ns)

            # 2. Fase Kuning NS
            signal.set_phase("YELLOW_NS", env.now)
            engine.on_phase_changed("YELLOW_NS")
            yield env.timeout(self.yellow_ns)

            # 3. Fase All-Red 1 (Pembersihan simpang sebelum EW hijau)
            signal.set_phase("ALL_RED_1", env.now)
            engine.on_phase_changed("ALL_RED_1")
            yield env.timeout(self.all_red_1)

            # 4. Fase Hijau EW
            signal.set_phase("EW", env.now)
            engine.on_phase_changed("EW")
            yield env.timeout(self.green_ew)

            # 5. Fase Kuning EW
            signal.set_phase("YELLOW_EW", env.now)
            engine.on_phase_changed("YELLOW_EW")
            yield env.timeout(self.yellow_ew)

            # 6. Fase All-Red 2 (Pembersihan simpang sebelum NS hijau)
            signal.set_phase("ALL_RED_2", env.now)
            engine.on_phase_changed("ALL_RED_2")
            yield env.timeout(self.all_red_2)
