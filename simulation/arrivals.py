import random
import simpy
from typing import Callable, Any
from simulation.vehicle import Vehicle
from config import VEHICLE_SERVICE_TIME

class ArrivalGenerator:
    def __init__(
        self,
        env: simpy.Environment,
        approach: str,
        rate_per_min: float,
        motor_ratio: float,
        rng: random.Random,
        on_arrival_callback: Callable[[Vehicle], Any]
    ):
        self.env = env
        self.approach = approach
        self.rate_per_min = rate_per_min
        self.motor_ratio = motor_ratio
        self.rng = rng
        self.on_arrival_callback = on_arrival_callback
        self.vehicle_counter = 0
        self.process = self.env.process(self._run())

    def _run(self):
        # Loop proses SimPy untuk kedatangan kendaraan
        while True:
            # Jika arrival rate <= 0, tidak ada kendaraan yang datang
            if self.rate_per_min <= 0:
                yield self.env.timeout(3600)
                continue

            rate_per_sec = self.rate_per_min / 60.0
            inter_arrival = self.rng.expovariate(rate_per_sec)
            
            yield self.env.timeout(inter_arrival)
            
            # Buat kendaraan baru
            self.vehicle_counter += 1
            v_id = f"{self.approach}-{self.vehicle_counter}"
            
            # Tentukan tipe kendaraan (motor vs mobil)
            is_motor = self.rng.random() < self.motor_ratio
            v_type = "motor" if is_motor else "mobil"
            
            # Crossing service time
            service_duration = VEHICLE_SERVICE_TIME.get(v_type, 2.0)
            
            vehicle = Vehicle(
                vehicle_id=v_id,
                vehicle_type=v_type,
                approach=self.approach,
                arrival_time=self.env.now,
                crossing_duration=service_duration
            )
            
            self.on_arrival_callback(vehicle)