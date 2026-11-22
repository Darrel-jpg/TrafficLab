"""
Modul pengelolaan sinyal/lampu lalu lintas dan penegakan invariant keselamatan.
"""
from typing import Dict, Any

class TrafficSignal:
    """
    Mengelola status lampu lalu lintas untuk 4 pendekatan (N, S, E, W).
    Menjamin bahwa fase NS dan EW tidak pernah hijau bersamaan (keselamatan lalu lintas).
    """
    def __init__(self, initial_time: float = 0.0):
        # Fase aktif: "NS", "YELLOW_NS", "ALL_RED_1", "EW", "YELLOW_EW", "ALL_RED_2"
        self.active_phase = "ALL_RED_1"
        self.phase_start_time = initial_time
        
        # Status lampu masing-masing arah: "green", "yellow", "red"
        self.states: Dict[str, str] = {
            "N": "red",
            "S": "red",
            "E": "red",
            "W": "red"
        }
        
        # Waktu mulai merah untuk masing-masing sumbu (digunakan untuk aturan anti-starvation)
        self.red_start_times: Dict[str, float] = {
            "NS": initial_time,
            "EW": initial_time
        }

    def set_phase(self, phase: str, current_time: float):
        """
        Mengubah fase lampu lalu lintas dengan validasi invariant ketat.
        """
        self.active_phase = phase
        self.phase_start_time = current_time

        if phase == "NS":
            self.states["N"] = "green"
            self.states["S"] = "green"
            self.states["E"] = "red"
            self.states["W"] = "red"
            # Sumbu EW berada di lampu merah sejak sekarang jika belum tercatat
            # Sumbu NS sedang hijau, red_start_times['NS'] akan diperbarui saat selesai hijau
        elif phase == "YELLOW_NS":
            self.states["N"] = "yellow"
            self.states["S"] = "yellow"
            self.states["E"] = "red"
            self.states["W"] = "red"
        elif phase in ("ALL_RED_1", "ALL_RED_2"):
            self.states["N"] = "red"
            self.states["S"] = "red"
            self.states["E"] = "red"
            self.states["W"] = "red"
            if phase == "ALL_RED_1":
                # NS baru saja selesai kuning dan masuk merah penuh
                self.red_start_times["NS"] = current_time
            elif phase == "ALL_RED_2":
                # EW baru saja selesai kuning dan masuk merah penuh
                self.red_start_times["EW"] = current_time
        elif phase == "EW":
            self.states["N"] = "red"
            self.states["S"] = "red"
            self.states["E"] = "green"
            self.states["W"] = "green"
        elif phase == "YELLOW_EW":
            self.states["N"] = "red"
            self.states["S"] = "red"
            self.states["E"] = "yellow"
            self.states["W"] = "yellow"
        else:
            raise ValueError(f"Fase sinyal tidak valid: {phase}")

        # Invariant check: NS and EW cannot both be green!
        self._verify_invariants()

    def _verify_invariants(self):
        """Verifikasi bahwa tidak ada konflik fase berbahaya."""
        ns_green = self.states["N"] == "green" or self.states["S"] == "green"
        ew_green = self.states["E"] == "green" or self.states["W"] == "green"
        if ns_green and ew_green:
            raise RuntimeError("INVARIANT VIOLATION: NS dan EW hijau secara bersamaan!")

    def is_green_for(self, approach: str) -> bool:
        """Memeriksa apakah pendekatan tertentu sedang berlampu hijau."""
        return self.states.get(approach) == "green"

    def get_red_waiting_time(self, axis: str, current_time: float) -> float:
        """
        Mengembalikan durasi sumbu (NS atau EW) telah menunggu dalam status merah.
        Digunakan oleh pengendali adaptif untuk aturan anti-starvation.
        """
        start = self.red_start_times.get(axis, current_time)
        return max(0.0, current_time - start)

    def to_dict(self) -> Dict[str, Any]:
        """Serialisasi untuk API snapshot."""
        return {
            "active_phase": self.active_phase,
            "phase_start_time": round(self.phase_start_time, 2),
            "states": dict(self.states)
        }
