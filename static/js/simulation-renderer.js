class SimulationRenderer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');

    // Dimensi Logis Canvas (kotak 800x800)
    this.canvas.width = 800;
    this.canvas.height = 800;
    this.width = 800;
    this.height = 800;
    this.cx = 400;
    this.cy = 400;

    // Lebar Jalan & Lajur
    this.roadWidth = 190;   // Lebar jalan total
    this.laneWidth = 95;    // Lebar per lajur

    this.renderState = null;
    this.animationFrameId = null;

    // Variabel Interpolasi Waktu Virtual 60 FPS
    this.lastBackendSimTime = 0.0;
    this.lastBackendReceivedTimestamp = performance.now();
    this.speedMultiplier = 2.0;

    // Memori posisi antrean (animasi lerp maju)
    this.queuedPositions = new Map();

    // Memori kendaraan yang melintas (terus berjalan sampai tuntas keluar kanvas)
    this.activeCrossingVehicles = new Map();

    // Peta model kendaraan beragam sesuai ilustrasi
    this.vehicleModels = ['taxi', 'sedan_blue', 'truck_red', 'hatch_teal', 'coupe_pink', 'car_green'];

    this._startLoop();
  }

  clearVehicles() {
    this.activeCrossingVehicles.clear();
    this.queuedPositions.clear();
  }

  updateState(state, speedMultiplier = 2.0) {
    this.renderState = state;
    if (state) {
      this.lastBackendSimTime = state.simulation_time || 0.0;
      this.lastBackendReceivedTimestamp = performance.now();
      this.speedMultiplier = speedMultiplier;

      // Daftar kendaraan melintas baru ke activeCrossingVehicles
      const crossing = state.crossing_vehicles || [];
      crossing.forEach(veh => {
        if (!this.activeCrossingVehicles.has(veh.id)) {
          const model = this._getVehicleModel(veh.id, veh.type);
          const vLen = model === 'truck_red' ? 62 : (veh.type === 'motor' ? 22 : 44);
          const vWidth = veh.type === 'motor' ? 14 : 25;
          const speed = veh.type === 'motor' ? 160.0 : 135.0;

          this.activeCrossingVehicles.set(veh.id, {
            id: veh.id,
            type: veh.type,
            approach: veh.approach,
            model: model,
            vLen: vLen,
            vWidth: vWidth,
            startSimTime: veh.service_start_time !== undefined && veh.service_start_time !== null
              ? veh.service_start_time
              : (state.simulation_time || 0.0),
            speed: speed
          });
        }
      });
    }
  }

  _getInterpolatedSimTime() {
    if (!this.renderState) return 0.0;
    if (this.renderState.status === 'paused' || this.renderState.status === 'finished') {
      return this.lastBackendSimTime;
    }
    const elapsedRealSeconds = (performance.now() - this.lastBackendReceivedTimestamp) / 1000.0;
    return this.lastBackendSimTime + (elapsedRealSeconds * this.speedMultiplier);
  }

  _startLoop() {
    const loop = () => {
      this._render();
      this.animationFrameId = requestAnimationFrame(loop);
    };
    this.animationFrameId = requestAnimationFrame(loop);
  }

  _getVehicleModel(id, type) {
    if (type === 'motor') return 'motor';
    let hash = 0;
    for (let i = 0; i < id.length; i++) {
      hash = (hash << 5) - hash + id.charCodeAt(i);
      hash |= 0;
    }
    const idx = Math.abs(hash) % this.vehicleModels.length;
    return this.vehicleModels[idx];
  }

  _render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // Gambar Trotoar & Lahan 4 Sudut
    this._drawLandscape(ctx);

    // Gambar Jalan, Garis Pembatas, dan Zebra Cross
    this._drawRoadNetwork(ctx);

    // Gambar Lampu Lalu Lintas di 4 Sudut Persimpangan
    this._drawTrafficSignals(ctx);

    // Gambar Kendaraan
    if (this.renderState) {
      const currentSimTime = this._getInterpolatedSimTime();
      this._drawVehicles(ctx, currentSimTime);
      this._drawQueueBadges(ctx);
    }
  }

  // LANSKAP & 4 SUDUT KOTA (Taman, Rumah/Atap, Pohon)
  _drawLandscape(ctx) {
    const rw2 = this.roadWidth / 2;
    const cornerSize = this.cx - rw2;

    // Dasar Trotoar Abu-abu Muda
    ctx.fillStyle = '#dbe1e8';
    ctx.fillRect(0, 0, this.width, this.height);

    // 4 Sudut Taman Hijau
    this._drawCornerPark(ctx, 0, 0, cornerSize, cornerSize, 'NW');
    this._drawCornerPark(ctx, this.cx + rw2, 0, cornerSize, cornerSize, 'NE');
    this._drawCornerPark(ctx, 0, this.cy + rw2, cornerSize, cornerSize, 'SW');
    this._drawCornerPark(ctx, this.cx + rw2, this.cy + rw2, cornerSize, cornerSize, 'SE');

    // Sudut NW (Kiri Atas)
    this._drawHouseRoofTopLeft(ctx, 16, 16, cornerSize - 32);

    // Sudut NE (Kanan Atas)
    this._drawHouseRoofTopRight(ctx, this.cx + rw2 + 16, 16, cornerSize - 32);

    // Sudut SW (Kiri Bawah)
    this._drawBuildingBottomLeft(ctx, 16, this.cy + rw2 + 16, cornerSize - 32);

    // Sudut SE (Kanan Bawah)
    this._drawBuildingBottomRight(ctx, this.cx + rw2 + 16, this.cy + rw2 + 16, cornerSize - 32);
  }

  _drawCornerPark(ctx, x, y, w, h, corner) {
    const curbR = 26;
    ctx.save();
    ctx.fillStyle = '#48bb78';

    ctx.beginPath();
    if (corner === 'NW') {
      ctx.moveTo(x + 10, y + 10);
      ctx.lineTo(x + w - 8, y + 10);
      ctx.lineTo(x + w - 8, y + h - curbR - 8);
      ctx.arcTo(x + w - 8, y + h - 8, x + w - curbR - 8, y + h - 8, curbR);
      ctx.lineTo(x + 10, y + h - 8);
    } else if (corner === 'NE') {
      ctx.moveTo(x + 8, y + 10);
      ctx.lineTo(x + w - 10, y + 10);
      ctx.lineTo(x + w - 10, y + h - 8);
      ctx.lineTo(x + curbR + 8, y + h - 8);
      ctx.arcTo(x + 8, y + h - 8, x + 8, y + h - curbR - 8, curbR);
    } else if (corner === 'SW') {
      ctx.moveTo(x + 10, y + 8);
      ctx.lineTo(x + w - curbR - 8, y + 8);
      ctx.arcTo(x + w - 8, y + 8, x + w - 8, y + curbR + 8, curbR);
      ctx.lineTo(x + w - 8, y + h - 10);
      ctx.lineTo(x + 10, y + h - 10);
    } else if (corner === 'SE') {
      ctx.moveTo(x + curbR + 8, y + 8);
      ctx.lineTo(x + w - 10, y + 8);
      ctx.lineTo(x + w - 10, y + h - 10);
      ctx.lineTo(x + 8, y + h - 10);
      ctx.lineTo(x + 8, y + curbR + 8);
      ctx.arcTo(x + 8, y + 8, x + curbR + 8, y + 8, curbR);
    }
    ctx.closePath();
    ctx.fill();

    ctx.strokeStyle = '#38a169';
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.restore();
  }

  _drawHouseRoofTopLeft(ctx, x, y, size) {
    ctx.fillStyle = '#e05638';
    ctx.fillRect(x + 12, y + 12, size - 80, size - 110);

    ctx.fillStyle = '#f07153';
    ctx.beginPath();
    ctx.moveTo(x + 12, y + 12);
    ctx.lineTo(x + 12 + (size - 80) / 2, y + 12 + (size - 110) / 2);
    ctx.lineTo(x + size - 68, y + 12);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = '#c53b1e';
    ctx.beginPath();
    ctx.moveTo(x + 12, y + size - 98);
    ctx.lineTo(x + 12 + (size - 80) / 2, y + 12 + (size - 110) / 2);
    ctx.lineTo(x + size - 68, y + size - 98);
    ctx.closePath();
    ctx.fill();

    ctx.fillStyle = '#b45309';
    ctx.fillRect(x + 14, y + size - 75, 45, 38);
    ctx.fillRect(x + 65, y + size - 75, 45, 38);

    this._drawPuffyTree(ctx, x + size - 35, y + 35, 22);
    this._drawPuffyTree(ctx, x + size - 35, y + 85, 20);
    this._drawPuffyTree(ctx, x + size - 35, y + 135, 24);
    this._drawPuffyTree(ctx, x + size - 60, y + size - 45, 22);
    this._drawPuffyTree(ctx, x + 135, y + size - 45, 18);
  }

  _drawHouseRoofTopRight(ctx, x, y, size) {
    ctx.fillStyle = '#8d6e63';
    ctx.fillRect(x + 70, y + 12, size - 70, size - 140);
    ctx.fillStyle = '#a1887f';
    ctx.fillRect(x + 70, y + 12, (size - 70) / 2, size - 140);

    ctx.fillStyle = '#cfd8dc';
    const hx = x + 120, hy = y + size - 110, hw = 80, hh = 80;
    ctx.fillRect(hx, hy, hw, hh);
    ctx.fillStyle = '#b0bec5';
    ctx.beginPath();
    ctx.moveTo(hx, hy);
    ctx.lineTo(hx + hw / 2, hy + hh / 2);
    ctx.lineTo(hx, hy + hh);
    ctx.closePath();
    ctx.fill();

    this._drawPuffyTree(ctx, x + 35, y + 35, 24);
    this._drawPuffyTree(ctx, x + 35, y + 90, 22);
    this._drawPuffyTree(ctx, x + 35, y + 145, 20);
    this._drawPuffyTree(ctx, x + 85, y + size - 45, 24);
  }

  _drawBuildingBottomLeft(ctx, x, y, size) {
    ctx.fillStyle = '#64748b';
    ctx.fillRect(x + 12, y + 80, size - 70, size - 95);
    ctx.fillStyle = '#475569';
    ctx.fillRect(x + 28, y + 96, size - 102, size - 127);
    ctx.fillStyle = '#334155';
    ctx.fillRect(x + 50, y + 115, size - 146, size - 165);

    ctx.fillStyle = '#94a3b8';
    ctx.fillRect(x + 12, y + 16, 75, 50);

    this._drawPuffyTree(ctx, x + 115, y + 35, 18);
    this._drawPuffyTree(ctx, x + 160, y + 42, 22);
    this._drawPuffyTree(ctx, x + size - 40, y + 60, 26);
    this._drawPuffyTree(ctx, x + size - 35, y + 120, 22);
  }

  _drawBuildingBottomRight(ctx, x, y, size) {
    ctx.fillStyle = '#64748b';
    ctx.fillRect(x + 60, y + 60, size - 60, size - 80);
    ctx.fillStyle = '#475569';
    ctx.fillRect(x + 80, y + 80, size - 100, size - 120);
    ctx.fillStyle = '#cbd5e1';
    ctx.fillRect(x + 110, y + 110, size - 160, size - 180);

    this._drawPuffyTree(ctx, x + 30, y + 35, 22);
    this._drawPuffyTree(ctx, x + 80, y + 30, 20);
    this._drawPuffyTree(ctx, x + 130, y + 30, 20);
    this._drawPuffyTree(ctx, x + 180, y + 30, 20);
    this._drawPuffyTree(ctx, x + 35, y + 85, 24);
    this._drawPuffyTree(ctx, x + 35, y + 140, 26);
  }

  _drawPuffyTree(ctx, x, y, r) {
    ctx.save();
    ctx.fillStyle = 'rgba(0, 0, 0, 0.15)';
    ctx.beginPath();
    ctx.arc(x + 3, y + 4, r, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#2d6a4f';
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#40916c';
    ctx.beginPath();
    ctx.arc(x - 2, y - 2, r * 0.85, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#52b788';
    ctx.beginPath();
    ctx.arc(x - 4, y - 4, r * 0.6, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  /* =========================================================================
     2. JALAN RAYA, MARKA JALAN, DAN ZEBRA CROSSING
     ========================================================================= */
  _drawRoadNetwork(ctx) {
    const cx = this.cx;
    const cy = this.cy;
    const rw2 = this.roadWidth / 2;

    ctx.fillStyle = '#7a8288';
    ctx.fillRect(cx - rw2, 0, this.roadWidth, this.height);
    ctx.fillRect(0, cy - rw2, this.width, this.roadWidth);
    ctx.fillRect(cx - rw2, cy - rw2, this.roadWidth, this.roadWidth);

    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 4;
    const curbR = 26;

    ctx.beginPath();
    ctx.moveTo(0, cy - rw2);
    ctx.lineTo(cx - rw2 - curbR, cy - rw2);
    ctx.arcTo(cx - rw2, cy - rw2, cx - rw2, cy - rw2 - curbR, curbR);
    ctx.lineTo(cx - rw2, 0);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx + rw2, 0);
    ctx.lineTo(cx + rw2, cy - rw2 - curbR);
    ctx.arcTo(cx + rw2, cy - rw2, cx + rw2 + curbR, cy - rw2, curbR);
    ctx.lineTo(this.width, cy - rw2);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, cy + rw2);
    ctx.lineTo(cx - rw2 - curbR, cy + rw2);
    ctx.arcTo(cx - rw2, cy + rw2, cx - rw2, cy + rw2 + curbR, curbR);
    ctx.lineTo(cx - rw2, this.height);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx + rw2, this.height);
    ctx.lineTo(cx + rw2, cy + rw2 + curbR);
    ctx.arcTo(cx + rw2, cy + rw2, cx + rw2 + curbR, cy + rw2, curbR);
    ctx.lineTo(this.width, cy + rw2);
    ctx.stroke();

    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 5;
    ctx.setLineDash([18, 16]);

    ctx.beginPath();
    ctx.moveTo(cx, 0); ctx.lineTo(cx, cy - rw2 - 50);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx, cy + rw2 + 50); ctx.lineTo(cx, this.height);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, cy); ctx.lineTo(cx - rw2 - 50, cy);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx + rw2 + 50, cy); ctx.lineTo(this.width, cy);
    ctx.stroke();

    ctx.setLineDash([]);

    // Zebra Crosswalks Tebal
    this._drawZebraCrossing(ctx, cx - rw2 + 6, cy - rw2 - 42, this.roadWidth - 12, 38, 'H');
    this._drawZebraCrossing(ctx, cx - rw2 + 6, cy + rw2 + 4, this.roadWidth - 12, 38, 'H');
    this._drawZebraCrossing(ctx, cx - rw2 - 42, cy - rw2 + 6, 38, this.roadWidth - 12, 'V');
    this._drawZebraCrossing(ctx, cx + rw2 + 4, cy - rw2 + 6, 38, this.roadWidth - 12, 'V');
  }

  _drawZebraCrossing(ctx, x, y, w, h, dir) {
    ctx.fillStyle = '#ffffff';
    const numBars = 9;

    if (dir === 'H') {
      const barW = (w - (numBars - 1) * 6) / numBars;
      for (let i = 0; i < numBars; i++) {
        ctx.fillRect(x + i * (barW + 6), y, barW, h);
      }
    } else {
      const barH = (h - (numBars - 1) * 6) / numBars;
      for (let i = 0; i < numBars; i++) {
        ctx.fillRect(x, y + i * (barH + 6), w, barH);
      }
    }
  }

// LAMPU LALU LINTAS
  _drawTrafficSignals(ctx) {
    const states = this.renderState ? this.renderState.signal_states : { N: 'red', S: 'red', E: 'red', W: 'red' };
    const cx = this.cx;
    const cy = this.cy;
    const rw2 = this.roadWidth / 2;

    this._drawLightPole(ctx, cx - rw2 - 16, cy - rw2 - 55, states.N, 'V');
    this._drawLightPole(ctx, cx + rw2 + 16, cy + rw2 + 55, states.S, 'V');
    this._drawLightPole(ctx, cx - rw2 - 55, cy + rw2 + 16, states.W, 'H');
    this._drawLightPole(ctx, cx + rw2 + 55, cy - rw2 - 16, states.E, 'H');
  }

  _drawLightPole(ctx, x, y, activeColor, orientation) {
    const isVert = orientation === 'V';
    const bw = isVert ? 16 : 44;
    const bh = isVert ? 44 : 16;
    const r = 4.5;

    ctx.save();
    ctx.fillStyle = '#1e293b';
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.roundRect(x - bw / 2, y - bh / 2, bw, bh, 5);
    ctx.fill();
    ctx.stroke();

    const colors = ['red', 'yellow', 'green'];
    const positions = isVert
      ? [{ cx: x, cy: y - 13 }, { cx: x, cy: y }, { cx: x, cy: y + 13 }]
      : [{ cx: x - 13, cy: y }, { cx: x, cy: y }, { cx: x + 13, cy: y }];

    positions.forEach((pos, i) => {
      const col = colors[i];
      const isActive = activeColor === col;

      ctx.beginPath();
      ctx.arc(pos.cx, pos.cy, r, 0, Math.PI * 2);

      if (isActive) {
        if (col === 'red') {
          ctx.fillStyle = '#ef4444';
          ctx.shadowColor = '#ef4444';
        } else if (col === 'yellow') {
          ctx.fillStyle = '#f59e0b';
          ctx.shadowColor = '#f59e0b';
        } else {
          ctx.fillStyle = '#10b981';
          ctx.shadowColor = '#10b981';
        }
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;
      } else {
        ctx.fillStyle = '#334155';
        ctx.fill();
      }
    });

    ctx.restore();
  }

// KENDARAAN
  _drawVehicles(ctx, currentSimTime) {
    const queues = this.renderState.queue_vehicles || {};
    const cx = this.cx;
    const cy = this.cy;

    // Gambar Kendaraan yang sedang melintas
    const finishedIds = [];
    this.activeCrossingVehicles.forEach((veh, id) => {
      const elapsedSim = Math.max(0.0, currentSimTime - veh.startSimTime);
      const dist = veh.speed * elapsedSim;
      let x = 0, y = 0, heading = 0, isOffScreen = false;

      if (veh.approach === 'N') {
        x = cx - 48;
        y = 257 + dist;
        heading = Math.PI / 2;
        if (y > 880) isOffScreen = true;
      } else if (veh.approach === 'S') {
        x = cx + 48;
        y = 543 - dist;
        heading = -Math.PI / 2;
        if (y < -80) isOffScreen = true;
      } else if (veh.approach === 'W') {
        x = 257 + dist;
        y = cy + 48;
        heading = 0;
        if (x > 880) isOffScreen = true;
      } else if (veh.approach === 'E') {
        x = 543 - dist;
        y = cy - 48;
        heading = Math.PI;
        if (x < -80) isOffScreen = true;
      }

      if (isOffScreen) {
        finishedIds.push(id);
      } else {
        this._drawDetailedVehicle(ctx, x, y, veh.vLen, veh.vWidth, veh.model, heading);
      }
    });

    finishedIds.forEach(id => this.activeCrossingVehicles.delete(id));

    // Gambar Kendaraan dalam antrean di 4 pendekat
    const activeQueueIds = new Set();
    ['N', 'S', 'E', 'W'].forEach(app => {
      const vList = queues[app] || [];
      let targetOffset = 0;

      vList.forEach((veh) => {
        activeQueueIds.add(veh.id);
        const model = this._getVehicleModel(veh.id, veh.type);
        const vLen = model === 'truck_red' ? 62 : (veh.type === 'motor' ? 22 : 44);
        const vWidth = veh.type === 'motor' ? 14 : 25;
        const gap = 8;

        const prevOffset = this.queuedPositions.has(veh.id)
          ? this.queuedPositions.get(veh.id)
          : targetOffset + 35;

        const smoothOffset = prevOffset + (targetOffset - prevOffset) * 0.14;
        this.queuedPositions.set(veh.id, smoothOffset);

        this._renderQueuedVehicle(ctx, veh, app, smoothOffset, vLen, vWidth, model);
        targetOffset += vLen + gap;
      });
    });

    // Bersihkan cache posisi antrean yang sudah keluar
    for (const id of this.queuedPositions.keys()) {
      if (!activeQueueIds.has(id)) {
        this.queuedPositions.delete(id);
      }
    }
  }

  _renderQueuedVehicle(ctx, veh, approach, offset, vLen, vWidth, model) {
    const cx = this.cx;
    const cy = this.cy;
    const rw2 = this.roadWidth / 2;
    const stopDistance = 48;

    let x = 0, y = 0, heading = 0;

    if (approach === 'N') {
      x = cx - 48;
      y = (cy - rw2 - stopDistance) - offset - (vLen / 2);
      heading = Math.PI / 2;
    } else if (approach === 'S') {
      x = cx + 48;
      y = (cy + rw2 + stopDistance) + offset + (vLen / 2);
      heading = -Math.PI / 2;
    } else if (approach === 'W') {
      x = (cx - rw2 - stopDistance) - offset - (vLen / 2);
      y = cy + 48;
      heading = 0;
    } else if (approach === 'E') {
      x = (cx + rw2 + stopDistance) + offset + (vLen / 2);
      y = cy - 48;
      heading = Math.PI;
    }

    this._drawDetailedVehicle(ctx, x, y, vLen, vWidth, model, heading);
  }

  _drawDetailedVehicle(ctx, x, y, len, width, model, heading) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(heading);

    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.beginPath();
    ctx.roundRect(-len / 2 + 2, -width / 2 + 3, len, width, 6);
    ctx.fill();

    if (model === 'motor') {
      ctx.fillStyle = '#ea580c';
      ctx.beginPath();
      ctx.roundRect(-len / 2, -width / 2 + 2, len, width - 4, 4);
      ctx.fill();

      ctx.fillStyle = '#0f172a';
      ctx.fillRect(len / 2 - 4, -width / 2 + 1, 3, width - 2);

      ctx.fillStyle = '#f8fafc';
      ctx.beginPath();
      ctx.arc(0, 0, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = '#cbd5e1';
      ctx.stroke();

      ctx.fillStyle = '#fef08a';
      ctx.fillRect(len / 2 - 2, -2, 2, 4);
    } else if (model === 'truck_red') {
      const cabLen = 18;
      const boxLen = len - cabLen - 3;

      ctx.fillStyle = '#dc2626';
      ctx.beginPath();
      ctx.roundRect(-len / 2, -width / 2, boxLen, width, 3);
      ctx.fill();

      ctx.fillStyle = '#1e293b';
      ctx.fillRect(-len / 2 + boxLen, -width / 2 + 4, 3, width - 8);

      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.roundRect(len / 2 - cabLen, -width / 2, cabLen, width, [0, 8, 8, 0]);
      ctx.fill();

      ctx.fillStyle = '#1e293b';
      ctx.beginPath();
      ctx.roundRect(len / 2 - 12, -width / 2 + 3, 5, width - 6, 2);
      ctx.fill();

      ctx.fillStyle = '#dc2626';
      ctx.fillRect(len / 2 - 10, -width / 2 - 3, 3, 3);
      ctx.fillRect(len / 2 - 10, width / 2, 3, 3);

    } else {
      let bodyColor = '#facc15';
      let roofColor = '#eab308';
      let isTaxi = false;

      if (model === 'taxi') {
        bodyColor = '#facc15';
        roofColor = '#eab308';
        isTaxi = true;
      } else if (model === 'sedan_blue') {
        bodyColor = '#38bdf8';
        roofColor = '#0284c7';
      } else if (model === 'hatch_teal') {
        bodyColor = '#2dd4bf';
        roofColor = '#0d9488';
      } else if (model === 'coupe_pink') {
        bodyColor = '#f43f5e';
        roofColor = '#e11d48';
      } else if (model === 'car_green') {
        bodyColor = '#84cc16';
        roofColor = '#65a30d';
      }

      ctx.fillStyle = bodyColor;
      ctx.beginPath();
      ctx.roundRect(-len / 2, -width / 2, len, width, 8);
      ctx.fill();

      ctx.fillStyle = '#1e293b';
      ctx.beginPath();
      ctx.roundRect(len / 2 - 14, -width / 2 + 3, 6, width - 6, 3);
      ctx.fill();

      ctx.fillStyle = '#1e293b';
      ctx.beginPath();
      ctx.roundRect(-len / 2 + 7, -width / 2 + 3, 4, width - 6, 2);
      ctx.fill();

      ctx.fillStyle = '#0f172a';
      ctx.fillRect(-len / 2 + 13, -width / 2 + 2, len - 27, 2);
      ctx.fillRect(-len / 2 + 13, width / 2 - 4, len - 27, 2);

      ctx.fillStyle = roofColor;
      ctx.beginPath();
      ctx.roundRect(-len / 2 + 12, -width / 2 + 4, len - 25, width - 8, 4);
      ctx.fill();

      ctx.fillStyle = bodyColor;
      ctx.beginPath();
      ctx.roundRect(len / 2 - 13, -width / 2 - 3, 3, 3, 1);
      ctx.roundRect(len / 2 - 13, width / 2, 3, 3, 1);
      ctx.fill();

      if (isTaxi) {
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 7px "DM Sans", -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('TAXI', -1, 0);
      }
    }

    ctx.restore();
  }

// BADGE ANTREAN (DIPOSISIKAN DI KIRI SEHINGGA TIDAK MENUTUPI ANTREAN)
  _drawQueueBadges(ctx) {
    const queues = this.renderState.queues || { N: 0, S: 0, E: 0, W: 0 };
    const cx = this.cx;
    const cy = this.cy;
    const rw2 = this.roadWidth / 2;

    // Utara
    this._drawBadgePill(ctx, `Utara: ${queues.N} kend`, cx - rw2 - 55, cy - rw2 - 110, '#0284c7');

    // Selatan
    this._drawBadgePill(ctx, `Selatan: ${queues.S} kend`, cx - rw2 + 250, cy + rw2 + 110, '#4338ca');

    // Barat
    this._drawBadgePill(ctx, `Barat: ${queues.W} kend`, cx - rw2 - 140, cy - rw2 + 210, '#475569');

    // Timur
    this._drawBadgePill(ctx, `Timur: ${queues.E} kend`, cx + rw2 + 140, cy + rw2 - 209, '#b45309');
  }

  _drawBadgePill(ctx, text, x, y, borderColor) {
    ctx.save();
    ctx.font = 'bold 11px "DM Sans", -apple-system, sans-serif';
    const textWidth = ctx.measureText(text).width;
    const pad = 10;
    const h = 22;

    ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
    ctx.strokeStyle = borderColor;
    ctx.lineWidth = 2;
    ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
    ctx.shadowBlur = 6;
    ctx.beginPath();
    ctx.roundRect(x - textWidth / 2 - pad, y - h / 2, textWidth + pad * 2, h, 11);
    ctx.fill();
    ctx.shadowBlur = 0;
    ctx.stroke();

    ctx.fillStyle = '#0f172a';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x, y);
    ctx.restore();
  }
}