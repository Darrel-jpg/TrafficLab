"""
REST API Blueprint untuk TrafficLab.
Menangani manajemen sesi simulasi, pemajuan waktu virtual (advance),
pengambilan snapshot state, reset, dan eksekusi batch eksperimen.
"""
from flask import Blueprint, jsonify, request
from typing import Dict, Any

from config import (
    APP_NAME,
    DEFAULT_SCENARIOS,
    DEFAULT_SIMULATION_DURATION,
    DEFAULT_RANDOM_SEED,
    DEFAULT_VEHICLE_MIX,
    FIXED_TIME_CONFIG,
    ADAPTIVE_CONFIG,
    EXPERIMENT_CONFIG
)
from simulation.engine import SimulationEngine
from simulation.experiments import run_batch_experiment

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Penyimpanan sesi simulasi dalam memori backend
ACTIVE_SIMULATIONS: Dict[str, SimulationEngine] = {}
SIMULATION_CONFIGS: Dict[str, Dict[str, Any]] = {}

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Pemeriksaan status kesehatan backend."""
    return jsonify({
        "status": "ok",
        "app": APP_NAME,
        "active_sessions": len(ACTIVE_SIMULATIONS),
        "version": "1.0.0"
    }), 200

@api_bp.route("/config", methods=["GET"])
def get_config():
    """Mengambil konfigurasi default, skenario, dan batasan parameter."""
    return jsonify({
        "app_name": APP_NAME,
        "default_duration": DEFAULT_SIMULATION_DURATION,
        "default_seed": DEFAULT_RANDOM_SEED,
        "default_vehicle_mix": DEFAULT_VEHICLE_MIX,
        "scenarios": DEFAULT_SCENARIOS,
        "fixed_time_config": FIXED_TIME_CONFIG,
        "adaptive_config": ADAPTIVE_CONFIG,
        "experiment_config": EXPERIMENT_CONFIG
    }), 200

@api_bp.route("/simulations", methods=["POST"])
def create_simulation():
    """Membuat sesi simulasi baru berbasis parameter yang dikirim frontend."""
    data = request.get_json(silent=True) or {}

    method = data.get("method", "fixed_time").lower()
    if method not in ("fixed_time", "adaptive"):
        method = "fixed_time"

    scenario_name = data.get("scenario", "normal")
    duration = float(data.get("duration", DEFAULT_SIMULATION_DURATION))
    seed = int(data.get("seed", DEFAULT_RANDOM_SEED))
    motor_ratio = float(data.get("motor_ratio", DEFAULT_VEHICLE_MIX["motor_ratio"]))

    # Arrival rates (N, S, E, W)
    rates_data = data.get("rates", {})
    scenario_info = DEFAULT_SCENARIOS.get(scenario_name)
    default_rates = scenario_info["rates"] if scenario_info else {"N": 8.0, "S": 8.0, "E": 8.0, "W": 8.0}
    
    arrival_rates = {
        app: max(0.0, float(rates_data.get(app, default_rates.get(app, 8.0))))
        for app in ("N", "S", "E", "W")
    }

    controller_config = data.get("controller_config", {})

    engine = SimulationEngine(
        method=method,
        scenario_name=scenario_name,
        arrival_rates=arrival_rates,
        duration=duration,
        seed=seed,
        motor_ratio=motor_ratio,
        controller_config=controller_config
    )

    ACTIVE_SIMULATIONS[engine.id] = engine
    SIMULATION_CONFIGS[engine.id] = {
        "method": method,
        "scenario": scenario_name,
        "rates": arrival_rates,
        "duration": duration,
        "seed": seed,
        "motor_ratio": motor_ratio,
        "controller_config": controller_config
    }

    return jsonify({
        "message": "Sesi simulasi berhasil dibuat.",
        "simulation_id": engine.id,
        "state": engine.get_state()
    }), 201

@api_bp.route("/simulations/<simulation_id>/advance", methods=["POST"])
def advance_simulation(simulation_id: str):
    """Memajukan waktu virtual SimPy sebesar delta detik."""
    engine = ACTIVE_SIMULATIONS.get(simulation_id)
    if not engine:
        return jsonify({"error": f"Sesi simulasi '{simulation_id}' tidak ditemukan."}), 404

    data = request.get_json(silent=True) or {}
    delta = float(data.get("delta_seconds", 1.0))
    if delta <= 0:
        delta = 1.0

    state = engine.advance(delta)
    return jsonify(state), 200

@api_bp.route("/simulations/<simulation_id>/state", methods=["GET"])
def get_simulation_state(simulation_id: str):
    """Mengambil snapshot state simulasi saat ini."""
    engine = ACTIVE_SIMULATIONS.get(simulation_id)
    if not engine:
        return jsonify({"error": f"Sesi simulasi '{simulation_id}' tidak ditemukan."}), 404

    return jsonify(engine.get_state()), 200

@api_bp.route("/simulations/<simulation_id>/reset", methods=["POST"])
def reset_simulation(simulation_id: str):
    """Mereset sesi simulasi ke kondisi awal dengan konfigurasi yang sama."""
    config = SIMULATION_CONFIGS.get(simulation_id)
    if not config:
        return jsonify({"error": f"Konfigurasi sesi '{simulation_id}' tidak ditemukan."}), 404

    new_engine = SimulationEngine(
        simulation_id=simulation_id,
        method=config["method"],
        scenario_name=config["scenario"],
        arrival_rates=config["rates"],
        duration=config["duration"],
        seed=config["seed"],
        motor_ratio=config["motor_ratio"],
        controller_config=config["controller_config"]
    )
    ACTIVE_SIMULATIONS[simulation_id] = new_engine

    return jsonify({
        "message": "Sesi simulasi berhasil direset.",
        "simulation_id": simulation_id,
        "state": new_engine.get_state()
    }), 200

@api_bp.route("/experiments/run", methods=["POST"])
def run_experiments():
    """Menjalankan batch eksperimen perbandingan skenario dan metode."""
    data = request.get_json(silent=True) or {}

    selected_scenarios = data.get("scenarios")
    methods = data.get("methods")
    replications = int(data.get("replications", EXPERIMENT_CONFIG["default_replications"]))
    duration = float(data.get("duration", EXPERIMENT_CONFIG["default_duration"]))
    base_seed = int(data.get("seed", DEFAULT_RANDOM_SEED))

    results = run_batch_experiment(
        selected_scenarios=selected_scenarios,
        methods=methods,
        replications=replications,
        duration=duration,
        base_seed=base_seed
    )

    return jsonify(results), 200
