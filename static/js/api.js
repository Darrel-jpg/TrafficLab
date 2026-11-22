/**
 * Modul Komunikasi API REST untuk TrafficLab.
 */
const TrafficLabAPI = {
  /**
   * Mengambil konfigurasi default backend dan daftar skenario.
   */
  async getConfig() {
    const res = await fetch('/api/config');
    if (!res.ok) throw new Error('Gagal mengambil konfigurasi backend.');
    return await res.json();
  },

  /**
   * Membuat sesi simulasi baru.
   */
  async createSimulation(params) {
    const res = await fetch('/api/simulations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Gagal membuat sesi simulasi.');
    }
    return await res.json();
  },

  /**
   * Memajukan waktu virtual SimPy sebesar delta detik.
   */
  async advanceSimulation(simulationId, deltaSeconds = 1.0) {
    const res = await fetch(`/api/simulations/${simulationId}/advance`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta_seconds: deltaSeconds })
    });
    if (!res.ok) throw new Error('Gagal memajukan waktu simulasi.');
    return await res.json();
  },

  /**
   * Mengambil snapshot state simulasi terkini.
   */
  async getState(simulationId) {
    const res = await fetch(`/api/simulations/${simulationId}/state`);
    if (!res.ok) throw new Error('Gagal mengambil snapshot simulasi.');
    return await res.json();
  },

  /**
   * Mereset sesi simulasi.
   */
  async resetSimulation(simulationId) {
    const res = await fetch(`/api/simulations/${simulationId}/reset`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error('Gagal mereset simulasi.');
    return await res.json();
  },

  /**
   * Menjalankan batch eksperimen monte carlo.
   */
  async runExperiments(params) {
    const res = await fetch('/api/experiments/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Gagal menjalankan batch eksperimen.');
    }
    return await res.json();
  }
};
