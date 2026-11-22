/**
 * Modul Dashboard & Kontrol Interaksi untuk TrafficLab.
 * Mengelola state mesin simulasi, pemajuan waktu virtual,
 * pembaruan KPI live, dan eksekusi batch eksperimen.
 */

class DashboardController {
  constructor(renderer, chartsManager) {
    this.renderer = renderer;
    this.charts = chartsManager;

    // State Simulasi
    this.simulationId = null;
    this.status = 'ready'; // ready, running, paused, finished
    this.speedMultiplier = 2.0;
    this.advanceIntervalId = null;
    this.isAdvancing = false;

    // Cache Konfigurasi
    this.appConfig = null;
    this.lastExperimentResults = null;

    this._bindElements();
    this._attachEventListeners();
  }

  _bindElements() {
    // Form & Tombol
    this.methodInput = document.getElementById('input-method');
    this.btnMethodFixed = document.getElementById('btn-method-fixed');
    this.btnMethodAdaptive = document.getElementById('btn-method-adaptive');
    this.methodHint = document.getElementById('method-hint');

    this.scenarioSelect = document.getElementById('input-scenario');
    this.scenarioChips = document.querySelectorAll('.chip-btn');

    this.rateN = document.getElementById('rate-n');
    this.rateS = document.getElementById('rate-s');
    this.rateE = document.getElementById('rate-e');
    this.rateW = document.getElementById('rate-w');

    this.btnStart = document.getElementById('btn-start');
    this.btnPause = document.getElementById('btn-pause');
    this.btnResume = document.getElementById('btn-resume');
    this.btnReset = document.getElementById('btn-reset');
    this.speedButtons = document.querySelectorAll('.speed-btn');

    // Indikator & Jam
    this.globalStatusDot = document.getElementById('global-status-dot');
    this.globalStatusText = document.getElementById('global-status-text');
    this.clockDisplay = document.getElementById('clock-display');
    this.clockMax = document.getElementById('clock-max');
    this.phaseBadge = document.getElementById('badge-active-phase');

    // KPI Cards
    this.kpiWaitTime = document.getElementById('kpi-wait-time');
    this.kpiAvgQueue = document.getElementById('kpi-avg-queue');
    this.kpiMaxQueue = document.getElementById('kpi-max-queue');
    this.kpiServed = document.getElementById('kpi-served');
    this.kpiArrived = document.getElementById('kpi-arrived');
    this.kpiThroughput = document.getElementById('kpi-throughput');

    // Eksperimen Elements
    this.btnRunExp = document.getElementById('btn-run-experiments');
    this.expProgressContainer = document.getElementById('exp-progress-container');
    this.expProgressFill = document.getElementById('exp-progress-fill');
    this.expProgressPercent = document.getElementById('exp-progress-percent');
    this.expSummaryContainer = document.getElementById('exp-summary-container');
    this.executiveSummaryList = document.getElementById('executive-summary-list');
    this.expChartsContainer = document.getElementById('exp-charts-container');
    this.expTableContainer = document.getElementById('exp-table-container');
    this.expTableBody = document.getElementById('experiment-table-body');
    this.btnExportCsv = document.getElementById('btn-export-csv');
  }

  _attachEventListeners() {
    // 1. Toggle Segmented Method (Fixed-Time vs Adaptive)
    if (this.btnMethodFixed && this.btnMethodAdaptive) {
      this.btnMethodFixed.addEventListener('click', () => {
        this.btnMethodFixed.classList.add('active');
        this.btnMethodAdaptive.classList.remove('active');
        this.methodInput.value = 'fixed_time';
        this.methodHint.textContent = 'Durasi hijau tetap (30s) per sumbu secara bergantian.';
      });

      this.btnMethodAdaptive.addEventListener('click', () => {
        this.btnMethodAdaptive.classList.add('active');
        this.btnMethodFixed.classList.remove('active');
        this.methodInput.value = 'adaptive';
        this.methodHint.textContent = 'Durasi hijau adaptif menyesuaikan antrean dengan aturan anti-starvation.';
      });
    }

    // 2. Scenario Chips
    this.scenarioChips.forEach(chip => {
      chip.addEventListener('click', () => {
        this.scenarioChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const sc = chip.dataset.scenario;
        this.scenarioSelect.value = sc;
        this._updateScenarioInputs();
      });
    });

    // 3. Speed buttons
    this.speedButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        this.speedButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.speedMultiplier = parseFloat(btn.dataset.speed || 1.0);
        this.renderer.speedMultiplier = this.speedMultiplier;
        if (this.status === 'running') {
          this._restartAdvanceLoop();
        }
      });
    });

    // 4. Tombol Aksi Simulasi
    this.btnStart.addEventListener('click', () => this.startSimulation());
    this.btnPause.addEventListener('click', () => this.pauseSimulation());
    this.btnResume.addEventListener('click', () => this.resumeSimulation());
    this.btnReset.addEventListener('click', () => this.resetSimulation());

    // 5. Tombol Eksperimen
    if (this.btnRunExp) {
      this.btnRunExp.addEventListener('click', () => this.runExperiments());
    }
    if (this.btnExportCsv) {
      this.btnExportCsv.addEventListener('click', () => this.exportCsv());
    }
  }

  async init() {
    try {
      this.appConfig = await TrafficLabAPI.getConfig();
      this._updateScenarioInputs();
      await this._createInitialSimulation();
    } catch (err) {
      console.error('Inisialisasi aplikasi gagal:', err);
    }
  }

  _updateScenarioInputs() {
    const scId = this.scenarioSelect.value;
    if (!this.appConfig || !this.appConfig.scenarios) return;

    if (scId === 'kustom') return;

    const sc = this.appConfig.scenarios[scId];
    if (sc && sc.rates) {
      this.rateN.value = sc.rates.N;
      this.rateS.value = sc.rates.S;
      this.rateE.value = sc.rates.E;
      this.rateW.value = sc.rates.W;
    }
  }

  _collectConfigParams() {
    const method = this.methodInput.value;
    const scenario = this.scenarioSelect.value;
    const duration = 1800; // 30 menit virtual default optimal
    const seed = 42;       // Seed acak default
    const motorRatio = 0.70; // 70% motor default optimal

    const rates = {
      N: parseFloat(this.rateN.value) || 8.0,
      S: parseFloat(this.rateS.value) || 8.0,
      E: parseFloat(this.rateE.value) || 8.0,
      W: parseFloat(this.rateW.value) || 8.0
    };

    return {
      method,
      scenario,
      duration,
      seed,
      motor_ratio: motorRatio,
      rates,
      controller_config: {}
    };
  }

  async _createInitialSimulation() {
    const params = this._collectConfigParams();
    const res = await TrafficLabAPI.createSimulation(params);
    this.simulationId = res.simulation_id;
    this._handleStateUpdate(res.state);
  }

  async startSimulation() {
    this._stopAdvanceLoop();
    if (this.renderer && typeof this.renderer.clearVehicles === 'function') {
      this.renderer.clearVehicles();
    }
    const params = this._collectConfigParams();
    const res = await TrafficLabAPI.createSimulation(params);
    this.simulationId = res.simulation_id;
    this.status = 'running';

    this._updateControlsUI();
    this.charts.resetLiveChart();
    this._handleStateUpdate(res.state);
    this._startAdvanceLoop();
  }

  pauseSimulation() {
    this.status = 'paused';
    this._stopAdvanceLoop();
    this._updateControlsUI();
  }

  resumeSimulation() {
    this.status = 'running';
    this._updateControlsUI();
    this._startAdvanceLoop();
  }

  async resetSimulation() {
    this._stopAdvanceLoop();
    if (this.renderer && typeof this.renderer.clearVehicles === 'function') {
      this.renderer.clearVehicles();
    }
    if (this.simulationId) {
      const res = await TrafficLabAPI.resetSimulation(this.simulationId);
      this.status = 'ready';
      this._updateControlsUI();
      this.charts.resetLiveChart();
      this._handleStateUpdate(res.state);
    } else {
      await this._createInitialSimulation();
    }
  }

  _startAdvanceLoop() {
    if (this.advanceIntervalId) clearInterval(this.advanceIntervalId);

    const pollIntervalMs = 200;
    this.advanceIntervalId = setInterval(async () => {
      if (this.isAdvancing || this.status !== 'running') return;
      this.isAdvancing = true;

      try {
        const deltaVirtual = (pollIntervalMs / 1000.0) * this.speedMultiplier;
        const state = await TrafficLabAPI.advanceSimulation(this.simulationId, deltaVirtual);
        this._handleStateUpdate(state);

        if (state.status === 'finished') {
          this.status = 'finished';
          this._stopAdvanceLoop();
          this._updateControlsUI();
        }
      } catch (err) {
        console.error('Error saat advance simulation:', err);
      } finally {
        this.isAdvancing = false;
      }
    }, pollIntervalMs);
  }

  _stopAdvanceLoop() {
    if (this.advanceIntervalId) {
      clearInterval(this.advanceIntervalId);
      this.advanceIntervalId = null;
    }
  }

  _restartAdvanceLoop() {
    this._stopAdvanceLoop();
    this._startAdvanceLoop();
  }

  _handleStateUpdate(state) {
    if (!state) return;

    // 1. Update Renderer Canvas dengan Speed Multiplier untuk Interpolasi Halus 60 FPS
    this.renderer.updateState(state, this.speedMultiplier);

    // 2. Update Live Charts
    if (state.history) {
      this.charts.updateLiveChart(state.history);
    }

    // 3. Update Jam Simulasi
    const simTime = state.simulation_time || 0.0;
    const maxDur = state.max_duration || 1800.0;
    this.clockDisplay.textContent = this._formatTime(simTime);
    this.clockMax.textContent = this._formatTime(maxDur);

    // 4. Update Badge Fase
    const phaseNames = {
      NS: 'Fase NS: HIJAU',
      YELLOW_NS: 'Fase NS: KUNING',
      ALL_RED_1: 'All-Red (Clearance)',
      EW: 'Fase EW: HIJAU',
      YELLOW_EW: 'Fase EW: KUNING',
      ALL_RED_2: 'All-Red (Clearance)'
    };
    this.phaseBadge.textContent = phaseNames[state.active_phase] || `Fase: ${state.active_phase}`;

    // 5. Update KPI Cards
    const m = state.metrics || {};
    this.kpiWaitTime.textContent = (m.avg_waiting_time || 0.0).toFixed(2);
    this.kpiAvgQueue.textContent = (m.time_weighted_avg_queue || 0.0).toFixed(2);
    this.kpiMaxQueue.textContent = m.max_total_queue || 0;
    this.kpiServed.textContent = m.total_served || 0;
    this.kpiArrived.textContent = m.total_arrived || 0;
    this.kpiThroughput.textContent = (m.throughput || 0.0).toFixed(2);
  }

  _formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    const mStr = String(mins).padStart(2, '0');
    const sStr = String(secs).padStart(4, '0');
    return `${mStr}:${sStr}`;
  }

  _updateControlsUI() {
    this.globalStatusDot.className = `status-pulse ${this.status}`;
    const statusLabels = {
      ready: 'Siap',
      running: 'Berjalan',
      paused: 'Dijeda',
      finished: 'Selesai'
    };
    this.globalStatusText.textContent = statusLabels[this.status] || 'Siap';

    if (this.status === 'running') {
      this.btnStart.style.display = 'none';
      this.btnPause.style.display = 'inline-flex';
      this.btnPause.disabled = false;
      this.btnResume.style.display = 'none';
      this.btnReset.disabled = false;
    } else if (this.status === 'paused') {
      this.btnStart.style.display = 'none';
      this.btnPause.style.display = 'none';
      this.btnResume.style.display = 'inline-flex';
      this.btnReset.disabled = false;
    } else {
      this.btnStart.style.display = 'inline-flex';
      this.btnPause.style.display = 'none';
      this.btnResume.style.display = 'none';
      this.btnReset.disabled = false;
    }
  }

  /* =========================================================================
     Batch Experiments Handling
     ========================================================================= */
  async runExperiments() {
    const checkedScenarios = Array.from(
      document.querySelectorAll('input[name="exp-scenario"]:checked')
    ).map(el => el.value);

    if (checkedScenarios.length === 0) {
      alert('Pilih minimal 1 skenario untuk eksperimen.');
      return;
    }

    const reps = parseInt(document.getElementById('exp-replications').value, 10) || 10;
    const dur = parseFloat(document.getElementById('exp-duration').value) || 1800;

    this.btnRunExp.disabled = true;
    this.expProgressContainer.style.display = 'flex';
    this.expProgressFill.style.width = '35%';
    this.expProgressPercent.textContent = 'Memproses...';

    try {
      const results = await TrafficLabAPI.runExperiments({
        scenarios: checkedScenarios,
        methods: ['fixed_time', 'adaptive'],
        replications: reps,
        duration: dur,
        seed: 100
      });

      this.expProgressFill.style.width = '100%';
      this.expProgressPercent.textContent = 'Selesai';
      this.lastExperimentResults = results;

      setTimeout(() => {
        this.expProgressContainer.style.display = 'none';
        this.btnRunExp.disabled = false;
        this._renderExperimentResults(results);
      }, 350);

    } catch (err) {
      this.expProgressContainer.style.display = 'none';
      this.btnRunExp.disabled = false;
      alert(`Gagal: ${err.message}`);
    }
  }

  _renderExperimentResults(results) {
    this.expSummaryContainer.style.display = 'block';
    this.executiveSummaryList.innerHTML = '';
    (results.executive_summary || []).forEach(text => {
      const p = document.createElement('p');
      p.innerHTML = `• ${text}`;
      this.executiveSummaryList.appendChild(p);
    });

    this.expChartsContainer.style.display = 'grid';
    this.charts.renderExperimentCharts(results.charts);

    this.expTableContainer.style.display = 'block';
    this.expTableBody.innerHTML = '';
    (results.comparison_table || []).forEach(row => {
      const tr = document.createElement('tr');
      const badgeClass = row.best_method === 'Adaptive'
        ? 'adaptive'
        : (row.best_method === 'Fixed-Time' ? 'fixed' : 'equal');

      tr.innerHTML = `
        <td><strong>${row.scenario_name}</strong></td>
        <td>${row.fixed_wait}</td>
        <td>${row.adaptive_wait}</td>
        <td><strong style="color: ${parseFloat(row.wait_diff) > 0 ? '#16a34a' : '#d97706'}">${row.wait_diff}</strong></td>
        <td>${row.fixed_queue}</td>
        <td>${row.adaptive_queue}</td>
        <td><strong style="color: ${parseFloat(row.queue_diff) > 0 ? '#16a34a' : '#d97706'}">${row.queue_diff}</strong></td>
        <td>${row.adaptive_tp}</td>
        <td><span class="badge-tag ${badgeClass}">${row.best_method}</span></td>
      `;
      this.expTableBody.appendChild(tr);
    });
  }

  exportCsv() {
    if (!this.lastExperimentResults || !this.lastExperimentResults.comparison_table) {
      alert('Belum ada data eksperimen untuk diekspor.');
      return;
    }

    const rows = this.lastExperimentResults.comparison_table;
    let csv = 'Skenario,Waktu Tunggu Fixed-Time,Waktu Tunggu Adaptive,Efisiensi Tunggu (%),Antrean Fixed-Time,Antrean Adaptive,Efisiensi Antrean (%),Throughput Adaptive,Metode Terbaik\n';

    rows.forEach(r => {
      csv += `"${r.scenario_name}","${r.fixed_wait}","${r.adaptive_wait}","${r.wait_diff}","${r.fixed_queue}","${r.adaptive_queue}","${r.queue_diff}","${r.adaptive_tp}","${r.best_method}"\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `TrafficLab_Hasil_Eksperimen_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }
}
