document.addEventListener('DOMContentLoaded', () => {
  // Inisialisasi Modul Renderer & Chart
  const renderer = new SimulationRenderer('traffic-canvas');
  const charts = new ChartsManager();

  // Inisialisasi Dashboard Controller
  const dashboard = new DashboardController(renderer, charts);
  dashboard.init();
});
