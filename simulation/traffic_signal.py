from typing import Dict, Any

class TrafficSignal:
    def __init__(self, initial_time: float = 0.0):
        self.active_phase = "ALL_RED_1"
        self.phase_start_time = initial_time
        
        # Status lampu masing-masing arah: "green", "yellow", "red"
        self.states: Dict[str, str] = {
            "N": "red",
            "S": "red",
            "E": "red",
            "W": "red"
        }
        
        # Waktu mulai merah untuk masing-masing sumbu
        self.red_start_times: Dict[str, float] = {
            "NS": initial_time,
            "EW": initial_time
        }

    def set_phase(self, phase: str, current_time: float):
        self.active_phase = phase
        self.phase_start_time = current_time

        if phase == "NS":
            self.states["N"] = "green"
            self.states["S"] = "green"
            self.states["E"] = "red"
            self.states["W"] = "red"
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

        self._verify_invariants()

    def _verify_invariants(self):
        ns_green = self.states["N"] == "green" or self.states["S"] == "green"
        ew_green = self.states["E"] == "green" or self.states["W"] == "green"
        if ns_green and ew_green:
            raise RuntimeError("INVARIANT VIOLATION: NS dan EW hijau secara bersamaan!")

    def is_green_for(self, approach: str) -> bool:
        return self.states.get(approach) == "green"

    def get_red_waiting_time(self, axis: str, current_time: float) -> float:
        start = self.red_start_times.get(axis, current_time)
        return max(0.0, current_time - start)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_phase": self.active_phase,
            "phase_start_time": round(self.phase_start_time, 2),
            "states": dict(self.states)
        }