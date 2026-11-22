"""
Kelas dasar abstrak untuk pengontrol lampu lalu lintas.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseController(ABC):
    """
    Kelas abstrak untuk pengontrol lampu lalu lintas di persimpangan.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run_controller_process(self, engine):
        """
        Proses generator SimPy yang mengendalikan siklus lampu lalu lintas
        pada SimulationEngine.
        """
        pass
