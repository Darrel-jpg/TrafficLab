"""
Modul Eksperimen Batch untuk evaluasi komparatif Fixed-Time vs Adaptive.
Menjalankan multiple replications dengan Common Random Numbers (CRN),
menghitung mean dan standar deviasi, serta menyusun analisis perbandingan.
"""
import math
from typing import Dict, List, Any, Optional
from config import DEFAULT_SCENARIOS, EXPERIMENT_CONFIG
from simulation.engine import SimulationEngine

def calculate_mean_and_std(values: List[float]) -> Dict[str, float]:
    """Menghitung rata-rata (mean) dan standar deviasi sampel."""
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "std": 0.0}
    mean = sum(values) / n
    if n == 1:
        return {"mean": round(mean, 2), "std": 0.0}
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    return {"mean": round(mean, 2), "std": round(std, 2)}

def run_batch_experiment(
    selected_scenarios: Optional[List[str]] = None,
    methods: Optional[List[str]] = None,
    replications: int = EXPERIMENT_CONFIG["default_replications"],
    duration: float = EXPERIMENT_CONFIG["default_duration"],
    base_seed: int = 100,
    custom_scenarios_dict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Menjalankan batch eksperimen monte carlo perbandingan metode.
    Menggunakan Common Random Numbers (CRN) di setiap pasangan replikasi.
    """
    scenarios_pool = custom_scenarios_dict or DEFAULT_SCENARIOS
    scenarios_to_run = selected_scenarios or list(scenarios_pool.keys())
    methods_to_run = methods or ["fixed_time", "adaptive"]

    replications = max(1, min(int(replications), EXPERIMENT_CONFIG["max_replications"]))
    duration = float(duration)

    results: Dict[str, Any] = {
        "metadata": {
            "replications": replications,
            "duration": duration,
            "total_runs": len(scenarios_to_run) * len(methods_to_run) * replications
        },
        "scenarios_results": {},
        "comparison_table": [],
        "executive_summary": []
    }

    # Format data untuk grafik perbandingan
    # charts: { avg_wait: {scenario: {fixed_time: X, adaptive: Y}}, ... }
    chart_data = {
        "avg_waiting_time": {"labels": [], "fixed_time": [], "adaptive": []},
        "time_weighted_avg_queue": {"labels": [], "fixed_time": [], "adaptive": []},
        "max_queue": {"labels": [], "fixed_time": [], "adaptive": []},
        "throughput": {"labels": [], "fixed_time": [], "adaptive": []}
    }

    for sc_id in scenarios_to_run:
        sc_info = scenarios_pool.get(sc_id)
        if not sc_info:
            continue

        sc_name = sc_info.get("name", sc_id)
        sc_rates = sc_info.get("rates", {"N": 8, "S": 8, "E": 8, "W": 8})

        method_runs: Dict[str, Dict[str, List[float]]] = {
            m: {
                "avg_waiting_time": [],
                "time_weighted_avg_queue": [],
                "max_queue": [],
                "throughput": [],
                "total_served": [],
                "total_arrived": []
            }
            for m in methods_to_run
        }

        # Jalankan replikasi dengan Common Random Numbers
        for rep in range(replications):
            rep_seed = base_seed + (rep * 137)

            for method in methods_to_run:
                engine = SimulationEngine(
                    method=method,
                    scenario_name=sc_name,
                    arrival_rates=sc_rates,
                    duration=duration,
                    seed=rep_seed
                )
                engine.run_until_completion()
                metrics = engine.metrics.get_summary(duration)

                method_runs[method]["avg_waiting_time"].append(metrics["avg_waiting_time"])
                method_runs[method]["time_weighted_avg_queue"].append(metrics["time_weighted_avg_queue"])
                method_runs[method]["max_queue"].append(metrics["max_total_queue"])
                method_runs[method]["throughput"].append(metrics["throughput"])
                method_runs[method]["total_served"].append(metrics["total_served"])
                method_runs[method]["total_arrived"].append(metrics["total_arrived"])

        # Agregasikan mean & std dev untuk tiap metode
        scenario_summary: Dict[str, Any] = {}
        for method in methods_to_run:
            scenario_summary[method] = {
                metric_name: calculate_mean_and_std(values)
                for metric_name, values in method_runs[method].items()
            }

        # Hitung perbandingan dan delta persentase jika kedua metode diuji
        diff_info = {}
        if "fixed_time" in scenario_summary and "adaptive" in scenario_summary:
            ft_wait = scenario_summary["fixed_time"]["avg_waiting_time"]["mean"]
            ad_wait = scenario_summary["adaptive"]["avg_waiting_time"]["mean"]
            wait_diff_pct = round(((ft_wait - ad_wait) / max(ft_wait, 1e-6)) * 100, 1)

            ft_q = scenario_summary["fixed_time"]["time_weighted_avg_queue"]["mean"]
            ad_q = scenario_summary["adaptive"]["time_weighted_avg_queue"]["mean"]
            q_diff_pct = round(((ft_q - ad_q) / max(ft_q, 1e-6)) * 100, 1)

            ft_tp = scenario_summary["fixed_time"]["throughput"]["mean"]
            ad_tp = scenario_summary["adaptive"]["throughput"]["mean"]
            tp_diff_pct = round(((ad_tp - ft_tp) / max(ft_tp, 1e-6)) * 100, 1)

            diff_info = {
                "wait_diff_pct": wait_diff_pct,  # Positif berarti Adaptive lebih cepat/baik
                "queue_diff_pct": q_diff_pct,    # Positif berarti Adaptive antreannya lebih pendek
                "throughput_diff_pct": tp_diff_pct # Positif berarti throughput Adaptive lebih tinggi
            }

            # Masukkan ke chart_data
            chart_data["avg_waiting_time"]["labels"].append(sc_name)
            chart_data["avg_waiting_time"]["fixed_time"].append(ft_wait)
            chart_data["avg_waiting_time"]["adaptive"].append(ad_wait)

            chart_data["time_weighted_avg_queue"]["labels"].append(sc_name)
            chart_data["time_weighted_avg_queue"]["fixed_time"].append(ft_q)
            chart_data["time_weighted_avg_queue"]["adaptive"].append(ad_q)

            chart_data["max_queue"]["labels"].append(sc_name)
            chart_data["max_queue"]["fixed_time"].append(scenario_summary["fixed_time"]["max_queue"]["mean"])
            chart_data["max_queue"]["adaptive"].append(scenario_summary["adaptive"]["max_queue"]["mean"])

            chart_data["throughput"]["labels"].append(sc_name)
            chart_data["throughput"]["fixed_time"].append(ft_tp)
            chart_data["throughput"]["adaptive"].append(ad_tp)

            # Buat teks narasi analisis skenario
            if wait_diff_pct > 0:
                summary_text = (
                    f"Pada skenario '{sc_name}', metode Adaptive menghasilkan performa lebih baik "
                    f"dengan menurunkan waktu tunggu sebesar {abs(wait_diff_pct)}% "
                    f"dan memangkas antrean rata-rata sebesar {abs(q_diff_pct)}% dibandingkan Fixed-Time."
                )
            elif wait_diff_pct < -2.0:
                summary_text = (
                    f"Pada skenario '{sc_name}', metode Fixed-Time menunjukkan waktu tunggu lebih rendah "
                    f"sebesar {abs(wait_diff_pct)}% dibandingkan Adaptive."
                )
            else:
                summary_text = (
                    f"Pada skenario '{sc_name}', kedua metode memberikan performa yang hampir setara "
                    f"(selisih waktu tunggu {abs(wait_diff_pct)}%)."
                )
            results["executive_summary"].append(summary_text)

        results["scenarios_results"][sc_id] = {
            "name": sc_name,
            "metrics": scenario_summary,
            "comparison": diff_info
        }

        # Masukkan ke tabel perbandingan datar (mudah dirender di HTML)
        results["comparison_table"].append({
            "scenario_id": sc_id,
            "scenario_name": sc_name,
            "fixed_wait": f"{scenario_summary.get('fixed_time', {}).get('avg_waiting_time', {}).get('mean', 0.0)} ± {scenario_summary.get('fixed_time', {}).get('avg_waiting_time', {}).get('std', 0.0)} s",
            "adaptive_wait": f"{scenario_summary.get('adaptive', {}).get('avg_waiting_time', {}).get('mean', 0.0)} ± {scenario_summary.get('adaptive', {}).get('avg_waiting_time', {}).get('std', 0.0)} s",
            "wait_diff": f"{diff_info.get('wait_diff_pct', 0.0):+0.1f}%",
            "fixed_queue": f"{scenario_summary.get('fixed_time', {}).get('time_weighted_avg_queue', {}).get('mean', 0.0)} ± {scenario_summary.get('fixed_time', {}).get('time_weighted_avg_queue', {}).get('std', 0.0)} kend",
            "adaptive_queue": f"{scenario_summary.get('adaptive', {}).get('time_weighted_avg_queue', {}).get('mean', 0.0)} ± {scenario_summary.get('adaptive', {}).get('time_weighted_avg_queue', {}).get('std', 0.0)} kend",
            "queue_diff": f"{diff_info.get('queue_diff_pct', 0.0):+0.1f}%",
            "fixed_tp": f"{scenario_summary.get('fixed_time', {}).get('throughput', {}).get('mean', 0.0)} kend/m",
            "adaptive_tp": f"{scenario_summary.get('adaptive', {}).get('throughput', {}).get('mean', 0.0)} kend/m",
            "best_method": "Adaptive" if diff_info.get("wait_diff_pct", 0) > 0 else ("Fixed-Time" if diff_info.get("wait_diff_pct", 0) < -2 else "Setara")
        })

    results["charts"] = chart_data
    return results
