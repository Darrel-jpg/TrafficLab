/**
 * TrafficLab — Entry Point Aplikasi Web.
 * Menginisialisasi modul renderer, chart, dashboard, dan navigasi tab switcher.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Inisialisasi Modul Renderer & Chart
  const renderer = new SimulationRenderer('traffic-canvas');
  const charts = new ChartsManager();

  // 2. Inisialisasi Dashboard Controller
  const dashboard = new DashboardController(renderer, charts);
  dashboard.init();

  // 3. Setup Navigasi Switcher (Simulasi 2D vs Eksperimen)
  const switchButtons = document.querySelectorAll('.switch-btn');
  const viewPanels = document.querySelectorAll('.view-panel');

  switchButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.tab;

      switchButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      viewPanels.forEach(panel => {
        if (panel.id === targetId) {
          panel.classList.add('active');
        } else {
          panel.classList.remove('active');
        }
      });

      // Resize chart eksperimen saat tab diaktifkan
      if (targetId === 'view-experiments' && charts.expCharts.waiting) {
        Object.values(charts.expCharts).forEach(c => {
          if (c) c.resize();
        });
      }
    });
  });

  console.log('TrafficLab UI modern berhasil dimuat.');
});
