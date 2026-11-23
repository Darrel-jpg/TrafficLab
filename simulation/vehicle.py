from typing import Optional, Dict, Any

class Vehicle:
    def __init__(
        self,
        vehicle_id: str,
        vehicle_type: str,
        approach: str,
        arrival_time: float,
        crossing_duration: float
    ):
        self.id = vehicle_id
        self.type = vehicle_type  # "motor" atau "mobil"
        self.approach = approach  # "N", "S", "E", "W"
        self.arrival_time = arrival_time
        self.crossing_duration = crossing_duration
        self.state = "queue"
        self.service_start_time: Optional[float] = None
        self.finish_time: Optional[float] = None
        self.queue_index: int = 0  # Posisi urutan dalam antrean (0 = paling depan)

    def start_crossing(self, current_time: float):
        self.state = "crossing"
        self.service_start_time = current_time

    def finish_crossing(self, current_time: float):
        self.state = "served"
        self.finish_time = current_time

    def get_waiting_time(self, current_time: float) -> float:
        """
        Menghitung waktu tunggu kendaraan.
        Jika sudah dilayani: service_start_time - arrival_time
        Jika masih di antrean: current_time - arrival_time
        """
        if self.service_start_time is not None:
            return max(0.0, self.service_start_time - self.arrival_time)
        return max(0.0, current_time - self.arrival_time)

    def get_cross_progress(self, current_time: float) -> float:
        if self.state == "queue":
            return 0.0
        if self.state == "served":
            return 1.0
        if self.service_start_time is None or self.crossing_duration <= 0:
            return 0.0
        elapsed = current_time - self.service_start_time
        return min(1.0, max(0.0, elapsed / self.crossing_duration))

    def to_dict(self, current_time: float) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "approach": self.approach,
            "arrival_time": round(self.arrival_time, 2),
            "service_start_time": round(self.service_start_time, 2) if self.service_start_time is not None else None,
            "state": self.state,
            "queue_index": self.queue_index,
            "crossing_duration": round(self.crossing_duration, 2),
            "cross_progress": round(self.get_cross_progress(current_time), 3),
            "waiting_time": round(self.get_waiting_time(current_time), 2)
        }