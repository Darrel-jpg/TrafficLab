/**
 * Modul Manajemen Grafik Chart.js untuk TrafficLab.
 * Menangani grafik live antrean terhadap waktu dan grafik perbandingan hasil eksperimen.
 */

class ChartsManager {
  constructor() {
    this.liveChart = null;
    this.expCharts = {
      waiting: null,
      queue: null,
      maxQueue: null,
      throughput: null
    };

    this._initLiveChart();
  }

  _initLiveChart() {
    const canvas = document.getElementById('live-queue-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    const ctx = canvas.getContext('2d');
    this.liveChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Sumbu NS (Utara-Selatan)',
            borderColor: '#0284c7',
            backgroundColor: 'rgba(2, 132, 199, 0.08)',
            borderWidth: 2,
            tension: 0.3,
            fill: true,
            pointRadius: 1,
            data: []
          },
          {
            label: 'Sumbu EW (Timur-Barat)',
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            borderWidth: 2,
            tension: 0.3,
            fill: true,
            pointRadius: 1,
            data: []
          },
          {
            label: 'Total Antrean',
            borderColor: '#8b5cf6',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            borderDash: [4, 4],
            tension: 0.3,
            pointRadius: 0,
            data: []
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        scales: {
          x: {
            title: { display: true, text: 'Waktu Virtual (detik)', font: { size: 11, family: 'DM Sans' } },
            grid: { color: '#f1f5f9' }
          },
          y: {
            beginAtZero: true,
            title: { display: true, text: 'Jumlah Kendaraan', font: { size: 11, family: 'DM Sans' } },
            grid: { color: '#f1f5f9' }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  }

  updateLiveChart(history) {
    if (!this.liveChart || !history || history.length === 0) return;

    const labels = history.map(p => `${p.time}s`);
    const dataNS = history.map(p => p.queue_ns);
    const dataEW = history.map(p => p.queue_ew);
    const dataTot = history.map(p => p.queue_total);

    this.liveChart.data.labels = labels;
    this.liveChart.data.datasets[0].data = dataNS;
    this.liveChart.data.datasets[1].data = dataEW;
    this.liveChart.data.datasets[2].data = dataTot;
    this.liveChart.update();
  }

  resetLiveChart() {
    if (!this.liveChart) return;
    this.liveChart.data.labels = [];
    this.liveChart.data.datasets.forEach(ds => ds.data = []);
    this.liveChart.update();
  }

  renderExperimentCharts(chartsData) {
    if (typeof Chart === 'undefined' || !chartsData) return;

    // 1. Chart Rata-rata Waktu Tunggu
    this._renderBarComparison(
      'chart-exp-waiting',
      'waiting',
      'Waktu Tunggu (detik)',
      chartsData.avg_waiting_time
    );

    // 2. Chart Rata-rata Panjang Antrean Berbobot Waktu
    this._renderBarComparison(
      'chart-exp-queue',
      'queue',
      'Antrean Rata-rata (kendaraan)',
      chartsData.time_weighted_avg_queue
    );

    // 3. Chart Antrean Maksimum
    this._renderBarComparison(
      'chart-exp-max-queue',
      'maxQueue',
      'Antrean Puncak (kendaraan)',
      chartsData.max_queue
    );

    // 4. Chart Throughput
    this._renderBarComparison(
      'chart-exp-throughput',
      'throughput',
      'Throughput (kendaraan/menit)',
      chartsData.throughput
    );
  }

  _renderBarComparison(canvasId, chartKey, yAxisLabel, metricData) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !metricData) return;

    if (this.expCharts[chartKey]) {
      this.expCharts[chartKey].destroy();
    }

    const ctx = canvas.getContext('2d');
    this.expCharts[chartKey] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: metricData.labels,
        datasets: [
          {
            label: 'Fixed-Time (Waktu Tetap)',
            backgroundColor: '#f59e0b',
            borderRadius: 6,
            data: metricData.fixed_time
          },
          {
            label: 'Adaptive (Responsif Antrean)',
            backgroundColor: '#0284c7',
            borderRadius: 6,
            data: metricData.adaptive
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            title: { display: true, text: yAxisLabel, font: { size: 11, family: 'DM Sans' } },
            grid: { color: '#f1f5f9' }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { font: { size: 11, family: 'DM Sans', weight: 600 } }
          }
        }
      }
    });
  }
}
