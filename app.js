/* ==========================================================================
   ARTEMIS NORTH: Interactive Lunar Arctic vs. South Pole Trade-Study Engine
   100% Empirical NASA LRO LOLA, Mazarico Illumination & Diviner PRP V2.0
   Zero Synthetic Data | Hardware-Accelerated TypedArray Raster Solver
   ========================================================================== */

(function () {
  "use strict";

  const I18N = {
    en: {
      kicker: "#30DAYMAPCHALLENGE DAY 11: ARCTIC | PLANETARY GIS",
      app_title: "ARTEMIS NORTH: The Lunar Arctic Trade-Study Atlas",
      mode_north: "Lunar Arctic (80°N-90°N)",
      mode_dual: "Dual-Pole Trade Study",
      mode_south: "Artemis South (80°S-90°S)",
      sec_layers: "NASA LRO Scientific Layers",
      lyr_comp: "Artemis Suitability + Hillshade",
      lyr_comp_sub: "Live HLS landing zones & PSR cold traps",
      lyr_elev: "LOLA Laser Altimetry DEM",
      lyr_elev_sub: "80m native polar stereographic elevation",
      lyr_sun: "Solar Power Continuity",
      lyr_sun_sub: "Mazarico 18.6-yr nutation visibility",
      lyr_temp: "Diviner Cryogenic Cold Traps",
      lyr_temp_sub: "Annual max & winter surface temp",
      lyr_ice: "Water-Ice Permafrost Depth",
      lyr_ice_sub: "Diviner Level-5 sublimation stability",
      lyr_earth: "Direct-to-Earth (DTE) Comms",
      lyr_earth_sub: "Near-side link vs. Far-side quiet zone",
      sec_sun: "360° Polar Horizon Sun (1.54° Tilt)",
      btn_lunar_day: "Lunar Day",
      sec_solver: "Artemis HLS Mission Solver",
      pre_dte: "Artemis III (DTE)",
      pre_nrho: "Gateway NRHO Relay",
      pre_isru: "ISRU Ice Outpost",
      pre_radio: "Far-Side Radio Array",
      sl_sun: "Min Solar Illumination",
      sl_slope: "Max Lander Slope (80m)",
      sl_psr: "Max Rover Sortie to PSR",
      sl_earth: "Min Direct-to-Earth Vis",
      sl_earth_quiet: "Max Earth Interference",
      sec_overlays: "Cartographic Overlays",
      ov_grat: "Polar Graticule",
      ov_iau: "IAU Craters",
      ov_cands: "Base Candidates",
      ov_prof: "Rover Profile",
      loading_msg: "Decoding NASA LRO LOLA & Diviner Polar Grids...",
      badge_north: "Lunar Arctic (80°N - 90°N)",
      badge_south: "Lunar South Pole (80°S - 90°S)",
      sec_trade: "Arctic vs. South Pole Telemetry",
      vs_viable_lbl: "Viable HLS Area",
      vs_psr_lbl: "PSR Cold Traps",
      kpi_coldest: "Coldest Spot (Arctic)",
      kpi_peak_sun: "Arctic Peak Sun (60m)",
      kpi_peary_sub: "Peary / Whipple Crest",
      kpi_surf_ice: "Arctic Surface Frost",
      kpi_surf_sub: "Diviner 0.0m H2O Stable",
      kpi_spa: "South Relief Advantage",
      kpi_spa_sub: "SPA Basin Rim Uplift",
      sec_probe: "Orbital Pixel Telemetry",
      sec_cands: "Top Artemis North Candidates",
      sec_cands_south: "Top Artemis South Benchmarks",
      sec_sources: "Empirical NASA PDS Sources",
      viable_prefix: "Viable HLS Zone",
      near_side: "0° Near Side (Earth)",
      far_side: "180° Far Side",
      sources_copy:
        '100% real orbital measurements: LOLA 80m Polar DEM (<a href="https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/" target="_blank" rel="noopener">Smith et al., 2010</a>), 60m/120m Polar Illumination &amp; PSRs (<a href="https://pgda.gsfc.nasa.gov/products/69" target="_blank" rel="noopener">Mazarico et al., 2011</a>), Diviner Level-5 Polar Resource Products (<a href="https://pds-geosciences.wustl.edu/missions/lro/diviner.htm" target="_blank" rel="noopener">Paige et al., 2010</a>), and official <a href="https://planetarynames.wr.usgs.gov/" target="_blank" rel="noopener">IAU / USGS</a> nomenclature. Built by <a href="https://sounny.com" target="_blank" rel="noopener">Dr. Anwar Sounny-Slitine</a>.'
    },
    fr: {
      kicker: "#30DAYMAPCHALLENGE JOUR 11 : ARCTIQUE | SIG PLANETAIRE",
      app_title: "ARTEMIS NORD : Atlas Comparatif de l'Arctique Lunaire",
      mode_north: "Arctique Lunaire (80°N-90°N)",
      mode_dual: "Comparaison Bipolaire",
      mode_south: "Pole Sud Artemis (80°S-90°S)",
      sec_layers: "Couches Scientifiques NASA LRO",
      lyr_comp: "Admissibilite Artemis + Relief",
      lyr_comp_sub: "Zones d'alunissage HLS et pieges froids PSR",
      lyr_elev: "Altimetrie Laser LOLA (MNT)",
      lyr_elev_sub: "Topographie stereographique polaire 80m",
      lyr_sun: "Continuite Solaire",
      lyr_sun_sub: "Visibilite solaire sur 18,6 ans (Mazarico)",
      lyr_temp: "Pieges Cryogeniques Diviner",
      lyr_temp_sub: "Temperature max annuelle et hivernale",
      lyr_ice: "Profondeur du Pergelisol d'Eau",
      lyr_ice_sub: "Stabilite thermique Diviner Niveau-5",
      lyr_earth: "Visibilite Directe Terre (DTE)",
      lyr_earth_sub: "Face visible vs zone radio-silencieuse",
      sec_sun: "Soleil Polaire sur 360° (Inclinaison 1,54°)",
      btn_lunar_day: "Jour Lunaire",
      sec_solver: "Solveur de Contraintes Artemis HLS",
      pre_dte: "Artemis III (DTE)",
      pre_nrho: "Relais Gateway NRHO",
      pre_isru: "Avant-Poste Glace ISRU",
      pre_radio: "Radio-Observatoire Face Cachee",
      sl_sun: "Ensoleillement Minimal",
      sl_slope: "Pente Max Alunisseur (80m)",
      sl_psr: "Distance Max Rover au PSR",
      sl_earth: "Visibilite Terre Minimale",
      sl_earth_quiet: "Interference Terre Max",
      sec_overlays: "Habillage Cartographique",
      ov_grat: "Graticule Polaire",
      ov_iau: "Crateres UAI",
      ov_cands: "Sites Candidats",
      ov_prof: "Profil Rover",
      loading_msg: "Decodage des grilles polaires NASA LRO LOLA et Diviner...",
      badge_north: "Arctique Lunaire (80°N - 90°N)",
      badge_south: "Pole Sud Lunaire (80°S - 90°S)",
      sec_trade: "Telemetrie Arctique vs Pole Sud",
      vs_viable_lbl: "Surface HLS Viable",
      vs_psr_lbl: "Pieges Froids PSR",
      kpi_coldest: "Point le Plus Froid (Nord)",
      kpi_peak_sun: "Pic Solaire Nord (60m)",
      kpi_peary_sub: "Crete Peary / Whipple",
      kpi_surf_ice: "Givre de Surface Nord",
      kpi_surf_sub: "Glace stable a 0,0m (Diviner)",
      kpi_spa: "Amplitude Relief Sud",
      kpi_spa_sub: "Rebord du Bassin SPA",
      sec_probe: "Telemetrie Orbitale du Pixel",
      sec_cands: "Top Sites Candidats Artemis Nord",
      sec_cands_south: "Sites de Reference Artemis Sud",
      sec_sources: "Sources Empiriques NASA PDS",
      viable_prefix: "Zone HLS Viable",
      near_side: "0° Face Visible (Terre)",
      far_side: "180° Face Cachee",
      sources_copy:
        'Mesures orbitales 100% reelles : MNT Polaire LOLA 80m (<a href="https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/IMG/" target="_blank" rel="noopener">Smith et al., 2010</a>), Illumination Polaire 60m/120m et PSR (<a href="https://pgda.gsfc.nasa.gov/products/69" target="_blank" rel="noopener">Mazarico et al., 2011</a>), Produits Polaires Diviner Niveau-5 (<a href="https://pds-geosciences.wustl.edu/missions/lro/diviner.htm" target="_blank" rel="noopener">Paige et al., 2010</a>) et nomenclature officielle <a href="https://planetarynames.wr.usgs.gov/" target="_blank" rel="noopener">UAI / USGS</a>. Concu par <a href="https://sounny.com" target="_blank" rel="noopener">Dr. Anwar Sounny-Slitine</a>.'
    }
  };

  const PRESETS = {
    "artemis-dte": { minSun: 65, maxSlope: 10.0, maxPsr: 5.0, earthVal: 35, radioQuiet: false },
    "gateway-nrho": { minSun: 65, maxSlope: 10.0, maxPsr: 5.0, earthVal: 0, radioQuiet: false },
    "isru-ice": { minSun: 55, maxSlope: 12.0, maxPsr: 2.0, earthVal: 0, radioQuiet: false },
    "farside-radio": { minSun: 50, maxSlope: 10.0, maxPsr: 25.0, earthVal: 0, radioQuiet: true }
  };

  const state = {
    lang: localStorage.getItem("sounny_lang") === "fr" ? "fr" : "en",
    mode: "dual", // 'north' | 'dual' | 'south'
    layer: "composite", // 'composite' | 'elevation' | 'solar' | 'thermal' | 'ice' | 'earth'
    sunAzDeg: 135,
    playingSun: false,
    preset: "artemis-dte",
    minSun: 65,
    maxSlope: 10.0,
    maxPsr: 5.0,
    earthVal: 35,
    radioQuiet: false,
    overlays: { graticule: true, craters: true, candidates: true, transect: true },
    candTab: "north",
    selectedCandId: null,
    zoom: 1.0,
    panX: 0.0, // normalized grid pixels offset
    panY: 0.0,
    drawingTransect: false,
    drawStart: null,
    activeTransect: null,
    meta: null,
    poles: { north: null, south: null }
  };

  let N = 1024;
  let HALF_EXTENT = 304000.0;
  let CELL_RES = 593.75;
  let R_MOON = 1737400.0;
  let RHO_80 = 304177.0;

  /* ---------------- Coordinate Math ---------------- */
  function latLonToXY(lat, lon, pole) {
    const lonRad = (lon * Math.PI) / 180.0;
    if (pole === "north") {
      const rho = 2.0 * R_MOON * Math.tan(((90.0 - lat) * Math.PI) / 360.0);
      return { x: rho * Math.sin(lonRad), y: -rho * Math.cos(lonRad) };
    } else {
      const rho = 2.0 * R_MOON * Math.tan(((90.0 + lat) * Math.PI) / 360.0);
      return { x: rho * Math.sin(lonRad), y: +rho * Math.cos(lonRad) };
    }
  }

  function xyToLatLon(x, y, pole) {
    const rho = Math.hypot(x, y);
    const dlat = (2.0 * Math.atan(rho / (2.0 * R_MOON)) * 180.0) / Math.PI;
    if (pole === "north") {
      return { lat: 90.0 - dlat, lon: (Math.atan2(x, -y) * 180.0) / Math.PI };
    } else {
      return { lat: -90.0 + dlat, lon: (Math.atan2(x, +y) * 180.0) / Math.PI };
    }
  }

  function xyToGrid(x, y) {
    return {
      col: (x + HALF_EXTENT) / CELL_RES,
      row: (HALF_EXTENT - y) / CELL_RES
    };
  }

  function gridToXY(col, row) {
    return {
      x: -HALF_EXTENT + col * CELL_RES,
      y: HALF_EXTENT - row * CELL_RES
    };
  }

  /* ---------------- Color Ramps (Perceptual & High Contrast) ---------------- */
  function lerpStops(t, stops) {
    if (t <= stops[0][0]) return stops[0];
    const last = stops[stops.length - 1];
    if (t >= last[0]) return last;
    for (let i = 0; i < stops.length - 1; i++) {
      const a = stops[i], b = stops[i + 1];
      if (t >= a[0] && t <= b[0]) {
        const f = (t - a[0]) / (b[0] - a[0]);
        return [
          t,
          (a[1] + (b[1] - a[1]) * f) | 0,
          (a[2] + (b[2] - a[2]) * f) | 0,
          (a[3] + (b[3] - a[3]) * f) | 0
        ];
      }
    }
    return last;
  }

  const ELEV_STOPS = [
    [-4500, 14, 34, 68],
    [-2500, 26, 68, 108],
    [-800, 56, 98, 122],
    [600, 118, 136, 148],
    [2200, 178, 168, 152],
    [4200, 222, 198, 164],
    [6800, 250, 244, 232]
  ];

  const SUN_STOPS = [
    [0, 6, 8, 16],
    [12, 22, 24, 68],
    [32, 74, 34, 128],
    [52, 168, 56, 110],
    [68, 235, 122, 42],
    [80, 252, 204, 58],
    [90, 255, 252, 212]
  ];

  const TEMP_STOPS = [
    [22, 34, 238, 255],
    [45, 42, 148, 248],
    [80, 72, 68, 196],
    [110, 136, 42, 148],
    [160, 204, 68, 82],
    [210, 245, 148, 46],
    [255, 254, 232, 138]
  ];

  const EARTH_STOPS = [
    [0, 10, 14, 24],
    [5, 18, 42, 68],
    [25, 22, 96, 128],
    [45, 24, 158, 142],
    [65, 68, 212, 148],
    [88, 212, 248, 172]
  ];

  // Pre-build 256-entry LUTs for blazing-fast inner pixel loops
  const LUT_ELEV = new Uint8Array(256 * 3);
  const LUT_SUN = new Uint8Array(256 * 3);
  const LUT_TEMP = new Uint8Array(256 * 3);
  const LUT_EARTH = new Uint8Array(256 * 3);

  (function initLUTs() {
    for (let i = 0; i < 256; i++) {
      const ev = -4500 + (i / 255) * (6800 - -4500);
      const ce = lerpStops(ev, ELEV_STOPS);
      LUT_ELEV[i * 3] = ce[1]; LUT_ELEV[i * 3 + 1] = ce[2]; LUT_ELEV[i * 3 + 2] = ce[3];

      const sv = (i / 255) * 90.0;
      const cs = lerpStops(sv, SUN_STOPS);
      LUT_SUN[i * 3] = cs[1]; LUT_SUN[i * 3 + 1] = cs[2]; LUT_SUN[i * 3 + 2] = cs[3];

      const tv = 22.0 + (i / 255) * (255.0 - 22.0);
      const ct = lerpStops(tv, TEMP_STOPS);
      LUT_TEMP[i * 3] = ct[1]; LUT_TEMP[i * 3 + 1] = ct[2]; LUT_TEMP[i * 3 + 2] = ct[3];

      const eav = (i / 255) * 90.0;
      const cea = lerpStops(eav, EARTH_STOPS);
      LUT_EARTH[i * 3] = cea[1]; LUT_EARTH[i * 3 + 1] = cea[2]; LUT_EARTH[i * 3 + 2] = cea[3];
    }
  })();

  /* ---------------- Lossless PNG Data Decoding ---------------- */
  function loadImagePixels(url) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = () => {
        const c = document.createElement("canvas");
        c.width = img.width;
        c.height = img.height;
        const ctx = c.getContext("2d", { willReadFrequently: true });
        ctx.drawImage(img, 0, 0);
        resolve(ctx.getImageData(0, 0, img.width, img.height).data);
      };
      img.onerror = () => reject(new Error("Failed to load " + url));
      img.src = url;
    });
  }

  async function decodePole(pole) {
    const [demPx, illPx, thmPx, auxPx] = await Promise.all([
      loadImagePixels(`assets/${pole}_dem.png`),
      loadImagePixels(`assets/${pole}_illum.png`),
      loadImagePixels(`assets/${pole}_thermal.png`),
      loadImagePixels(`assets/${pole}_aux.png`)
    ]);

    const len = N * N;
    const elev = new Float32Array(len);
    const slopeP90 = new Float32Array(len);
    const sunPct = new Float32Array(len);
    const earthPct = new Float32Array(len);
    const psrPct = new Float32Array(len);
    const tmaxK = new Float32Array(len);
    const tminK = new Float32Array(len);
    const iceCode = new Uint8Array(len);
    const distPsrKm = new Float32Array(len);
    const inCap80 = new Uint8Array(len);

    const rho80Sq = RHO_80 * RHO_80;

    for (let i = 0; i < len; i++) {
      const p = i * 4;
      const u16 = (demPx[p] << 8) | demPx[p + 1];
      elev[i] = u16 / 2.5 - 12000.0;
      slopeP90[i] = demPx[p + 2] * 0.25;

      sunPct[i] = illPx[p] * 0.5;
      earthPct[i] = illPx[p + 1] * 0.5;
      psrPct[i] = illPx[p + 2] * 0.4;

      tmaxK[i] = thmPx[p] === 255 ? NaN : thmPx[p] + 15.0;
      iceCode[i] = thmPx[p + 1];
      distPsrKm[i] = thmPx[p + 2] * 0.2;

      tminK[i] = auxPx[p + 1] === 255 ? NaN : auxPx[p + 1] * 0.5 + 15.0;

      const r = (i / N) | 0;
      const c = i - r * N;
      const x = -HALF_EXTENT + (c + 0.5) * CELL_RES;
      const y = HALF_EXTENT - (r + 0.5) * CELL_RES;
      inCap80[i] = (x * x + y * y <= rho80Sq) ? 1 : 0;
    }

    // Pre-compute surface gradients (dz/dx, dz/dy) with 2.2x vertical exaggeration for crisp low-angle polar lighting
    const dzdx = new Float32Array(len);
    const dzdy = new Float32Array(len);
    const zExag = 2.3 / (2.0 * CELL_RES);
    for (let r = 0; r < N; r++) {
      const rUp = r > 0 ? r - 1 : 0;
      const rDn = r < N - 1 ? r + 1 : N - 1;
      for (let c = 0; c < N; c++) {
        const cLt = c > 0 ? c - 1 : 0;
        const cRt = c < N - 1 ? c + 1 : N - 1;
        const idx = r * N + c;
        dzdx[idx] = (elev[r * N + cRt] - elev[r * N + cLt]) * zExag;
        // Screen +Y is down, stereographic +Y is up -> invert Y difference
        dzdy[idx] = (elev[rUp * N + c] - elev[rDn * N + c]) * zExag;
      }
    }

    const offCanvas = document.createElement("canvas");
    offCanvas.width = N;
    offCanvas.height = N;
    const offCtx = offCanvas.getContext("2d");
    const imgData = offCtx.createImageData(N, N);

    return {
      pole,
      elev,
      slopeP90,
      sunPct,
      earthPct,
      psrPct,
      tmaxK,
      tminK,
      iceCode,
      distPsrKm,
      inCap80,
      dzdx,
      dzdy,
      offCanvas,
      offCtx,
      imgData,
      viableKm2: 0
    };
  }

  /* ---------------- Real-Time 60 FPS Raster Shader & Suitability Solver ---------------- */
  function renderPoleRaster(pd) {
    if (!pd) return 0;
    const len = N * N;
    const out = pd.imgData.data;
    const { elev, slopeP90, sunPct, earthPct, psrPct, tmaxK, tminK, iceCode, distPsrKm, inCap80, dzdx, dzdy } = pd;

    // Sun vector in stereographic XY plane from planetocentric longitude azimuth
    const azRad = (state.sunAzDeg * Math.PI) / 180.0;
    const lx = Math.sin(azRad);
    const ly = pd.pole === "north" ? -Math.cos(azRad) : +Math.cos(azRad);
    const sunAltRad = (8.5 * Math.PI) / 180.0; // Grazing polar sun elevation + ambient bounce
    const cosAlt = Math.cos(sunAltRad);
    const sinAlt = Math.sin(sunAltRad);

    const layer = state.layer;
    const minSun = state.minSun;
    const maxSlope = state.maxSlope;
    const maxPsr = state.maxPsr;
    const earthVal = state.earthVal;
    const radioQuiet = state.radioQuiet;

    let viableCount = 0;

    for (let i = 0; i < len; i++) {
      // Lambertian hillshade on LOLA topography
      const gx = dzdx[i];
      const gy = dzdy[i];
      const invNorm = 1.0 / Math.sqrt(gx * gx + gy * gy + 1.0);
      let shade = (-gx * lx * cosAlt - gy * ly * cosAlt + sinAlt) * invNorm;
      shade = shade < 0 ? 0.14 : 0.14 + 0.86 * Math.min(1.0, shade * 1.45);

      // Evaluate Artemis HLS Multi-Criteria Suitability everywhere inside 80-90 deg cap
      const earthOk = radioQuiet ? (earthPct[i] <= earthVal) : (earthPct[i] >= earthVal);
      const isViable =
        inCap80[i] === 1 &&
        sunPct[i] >= minSun &&
        slopeP90[i] <= maxSlope &&
        distPsrKm[i] <= maxPsr &&
        earthOk;

      if (isViable) viableCount++;

      let r = 0, g = 0, b = 0;

      if (layer === "composite") {
        // Subtle hypsometric titanium base + grazing polar hillshade
        const tElev = Math.max(0, Math.min(255, (((elev[i] + 4500) / 11300) * 255) | 0)) * 3;
        const baseLum = 28 + shade * 175;
        r = (baseLum * 0.76 + LUT_ELEV[tElev] * 0.24) | 0;
        g = (baseLum * 0.78 + LUT_ELEV[tElev + 1] * 0.24) | 0;
        b = (baseLum * 0.84 + LUT_ELEV[tElev + 2] * 0.26) | 0;

        // Permanently Shadowed Regions (PSRs) rendered as deep cryogenic cold traps
        if (psrPct[i] >= 35.0) {
          const pf = Math.min(1.0, (psrPct[i] - 25.0) / 60.0);
          r = (r * (1 - pf) + 6 * pf) | 0;
          g = (g * (1 - pf) + 22 * pf) | 0;
          b = (b * (1 - pf) + 46 * pf) | 0;
        }

        // Viable Artemis Landing Zones glow in high-contrast Emerald / Solar Gold
        if (isViable) {
          if (sunPct[i] >= 78.0) {
            r = 251; g = 198; b = 42;
          } else {
            r = 16; g = 212; b = 142;
          }
        }
      } else if (layer === "elevation") {
        const idx = Math.max(0, Math.min(255, (((elev[i] + 4500) / 11300) * 255) | 0)) * 3;
        const sf = 0.35 + 0.82 * shade;
        r = Math.min(255, (LUT_ELEV[idx] * sf) | 0);
        g = Math.min(255, (LUT_ELEV[idx + 1] * sf) | 0);
        b = Math.min(255, (LUT_ELEV[idx + 2] * sf) | 0);
      } else if (layer === "solar") {
        const idx = Math.max(0, Math.min(255, ((sunPct[i] / 90.0) * 255) | 0)) * 3;
        const sf = 0.62 + 0.45 * shade;
        r = Math.min(255, (LUT_SUN[idx] * sf) | 0);
        g = Math.min(255, (LUT_SUN[idx + 1] * sf) | 0);
        b = Math.min(255, (LUT_SUN[idx + 2] * sf) | 0);
      } else if (layer === "thermal") {
        const tk = pd.pole === "north" && !Number.isNaN(tminK[i]) && psrPct[i] > 20 ? tminK[i] : tmaxK[i];
        if (Number.isNaN(tk)) {
          const lum = (24 + shade * 110) | 0;
          r = lum; g = lum; b = (lum * 1.08) | 0;
        } else {
          const idx = Math.max(0, Math.min(255, (((tk - 22.0) / 233.0) * 255) | 0)) * 3;
          const sf = 0.68 + 0.38 * shade;
          r = Math.min(255, (LUT_TEMP[idx] * sf) | 0);
          g = Math.min(255, (LUT_TEMP[idx + 1] * sf) | 0);
          b = Math.min(255, (LUT_TEMP[idx + 2] * sf) | 0);
        }
      } else if (layer === "ice") {
        const ic = iceCode[i];
        const lum = 24 + shade * 128;
        if (ic === 0) {
          // Exposed surface water frost stable (0.00 m)
          r = 145; g = 246; b = 255;
        } else if (ic >= 1 && ic <= 50) {
          // Very shallow permafrost (0.01 - 0.50 m)
          r = 46; g = 196; b = 248;
        } else if (ic > 50 && ic <= 150) {
          // Drillable permafrost (0.50 - 1.50 m)
          r = 52; g = 122; b = 232;
        } else if (ic > 150 && ic <= 250) {
          // Deep permafrost (1.50 - 2.50 m)
          r = (lum * 0.4 + 48) | 0; g = (lum * 0.45 + 68) | 0; b = (lum * 0.5 + 158) | 0;
        } else {
          r = lum | 0; g = (lum * 1.02) | 0; b = (lum * 1.08) | 0;
        }
      } else if (layer === "earth") {
        const idx = Math.max(0, Math.min(255, ((earthPct[i] / 90.0) * 255) | 0)) * 3;
        const sf = 0.52 + 0.55 * shade;
        r = Math.min(255, (LUT_EARTH[idx] * sf) | 0);
        g = Math.min(255, (LUT_EARTH[idx + 1] * sf) | 0);
        b = Math.min(255, (LUT_EARTH[idx + 2] * sf) | 0);
      }

      // Dim outside 80 deg latitude circle gently so the polar cap boundary reads cleanly
      if (inCap80[i] === 0) {
        r = (r * 0.52) | 0;
        g = (g * 0.54) | 0;
        b = (b * 0.58) | 0;
      }

      const p = i * 4;
      out[p] = r;
      out[p + 1] = g;
      out[p + 2] = b;
      out[p + 3] = 255;
    }

    pd.offCtx.putImageData(pd.imgData, 0, 0);
    const cellKm2 = (CELL_RES / 1000.0) * (CELL_RES / 1000.0);
    pd.viableKm2 = viableCount * cellKm2;
    return pd.viableKm2;
  }

  /* ---------------- Viewport Camera & Vector Cartography ---------------- */
  function getViewportTransform(vpEl) {
    const rect = vpEl.getBoundingClientRect();
    const w = Math.max(1, rect.width);
    const h = Math.max(1, rect.height);
    const baseScale = (Math.min(w, h) * 0.94) / N;
    const scale = baseScale * state.zoom;
    const tx = w * 0.5 - (N * 0.5 + state.panX) * scale;
    const ty = h * 0.5 - (N * 0.5 + state.panY) * scale;
    return { w, h, scale, tx, ty };
  }

  function drawPoleViewport(pole) {
    const pd = state.poles[pole];
    if (!pd) return;
    const vpEl = document.getElementById(`vp-${pole}`);
    if (vpEl.classList.contains("hidden")) return;

    const cv = document.getElementById(`cv-${pole}`);
    const ov = document.getElementById(`ov-${pole}`);
    const { w, h, scale, tx, ty } = getViewportTransform(vpEl);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    if (cv.width !== ((w * dpr) | 0) || cv.height !== ((h * dpr) | 0)) {
      cv.width = (w * dpr) | 0;
      cv.height = (h * dpr) | 0;
      ov.width = (w * dpr) | 0;
      ov.height = (h * dpr) | 0;
    }

    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#04070d";
    ctx.fillRect(0, 0, w, h);
    ctx.imageSmoothingEnabled = scale < 2.2;
    ctx.drawImage(pd.offCanvas, tx, ty, N * scale, N * scale);

    // Vector Cartography Overlay
    const octx = ov.getContext("2d");
    octx.setTransform(dpr, 0, 0, dpr, 0, 0);
    octx.clearRect(0, 0, w, h);

    const cx = tx + N * 0.5 * scale;
    const cy = ty + N * 0.5 * scale;
    const dict = I18N[state.lang];

    // 1. Polar Stereographic Graticule (85 deg & 80 deg circles + cardinal meridians)
    if (state.overlays.graticule) {
      octx.save();
      octx.strokeStyle = "rgba(226, 232, 240, 0.20)";
      octx.lineWidth = 1;
      octx.setLineDash([4, 4]);

      [85, 80].forEach((latAbs) => {
        const rho = 2.0 * R_MOON * Math.tan(((90.0 - latAbs) * Math.PI) / 360.0);
        const radPx = (rho / CELL_RES) * scale;
        octx.beginPath();
        octx.arc(cx, cy, radPx, 0, Math.PI * 2);
        octx.stroke();

        octx.fillStyle = "rgba(226, 232, 240, 0.58)";
        octx.font = "600 10px 'Space Grotesk', monospace";
        octx.fillText(`${latAbs}°${pole === "north" ? "N" : "S"}`, cx + radPx * 0.707 + 4, cy - radPx * 0.707 - 3);
      });

      const r80Px = (RHO_80 / CELL_RES) * scale;
      octx.strokeStyle = "rgba(226, 232, 240, 0.14)";
      octx.beginPath();
      octx.moveTo(cx - r80Px, cy); octx.lineTo(cx + r80Px, cy);
      octx.moveTo(cx, cy - r80Px); octx.lineTo(cx, cy + r80Px);
      octx.stroke();
      octx.setLineDash([]);

      // Cardinal meridian labels respecting exact IAU polar orientation
      octx.font = "700 10px 'Space Grotesk', monospace";
      octx.textAlign = "center";
      octx.fillStyle = "rgba(56, 189, 248, 0.85)";
      const topLbl = pole === "north" ? dict.far_side : dict.near_side;
      const botLbl = pole === "north" ? dict.near_side : dict.far_side;
      if (cy - r80Px - 8 > 48) octx.fillText(topLbl, cx, cy - r80Px - 7);
      if (cy + r80Px + 14 < h - 10) octx.fillText(botLbl, cx, cy + r80Px + 14);

      octx.fillStyle = "rgba(148, 163, 184, 0.72)";
      octx.fillText("90°E", Math.min(w - 22, cx + r80Px + 18), cy + 3);
      octx.fillText("90°W", Math.max(22, cx - r80Px - 18), cy + 3);

      // Metric Scale Bar (100 km)
      const bar100Px = (100000.0 / CELL_RES) * scale;
      const bx = w - bar100Px - 16;
      const by = h - 18;
      if (bx > 180) {
        octx.strokeStyle = "rgba(248, 250, 252, 0.85)";
        octx.lineWidth = 2;
        octx.beginPath();
        octx.moveTo(bx, by - 4); octx.lineTo(bx, by); octx.lineTo(bx + bar100Px, by); octx.lineTo(bx + bar100Px, by - 4);
        octx.stroke();
        octx.fillStyle = "#f8fafc";
        octx.font = "700 10px 'Space Grotesk', monospace";
        octx.textAlign = "right";
        octx.fillText("100 km", bx + bar100Px, by - 6);
      }
      octx.restore();
    }

    // 2. Official IAU Crater & Massif Labels (Collision-Avoided against Candidate Pins & Graticule Labels)
    const placedBoxes = [];
    if (state.overlays.graticule) {
      const r80Px = (RHO_80 / CELL_RES) * scale;
      placedBoxes.push({ x0: cx - 78, y0: cy - r80Px - 22, x1: cx + 78, y1: cy - r80Px + 2 });
      placedBoxes.push({ x0: cx - 78, y0: cy + r80Px + 2, x1: cx + 78, y1: cy + r80Px + 22 });
    }
    if (state.overlays.candidates && state.meta) {
      (state.meta.poles[pole].candidates || []).forEach((c) => {
        const g = xyToGrid(c.x_km * 1000.0, c.y_km * 1000.0);
        const sx = tx + g.col * scale;
        const sy = ty + g.row * scale;
        placedBoxes.push({ x0: sx - 11, y0: sy - 11, x1: sx + 11, y1: sy + 11 });
      });
    }

    if (state.overlays.craters && state.meta) {
      const lms = state.meta.poles[pole].landmarks || [];
      octx.save();
      octx.textAlign = "center";

      for (let i = 0; i < lms.length; i++) {
        const f = lms[i];
        if (f.is_satellite && f.name !== "Hermite A" && state.zoom < 1.6) continue;
        if (f.diameter_km < 16 && f.type === "Crater" && state.zoom < 1.35 && !["Whipple", "Erlanger", "Hinshelwood", "Shackleton"].includes(f.name)) continue;

        const g = xyToGrid(f.x_km * 1000.0, f.y_km * 1000.0);
        const sx = tx + g.col * scale;
        let sy = ty + g.row * scale;
        if (sx < 28 || sx > w - 28 || sy < 44 || sy > h - 32) continue;

        const cleanName = f.name.replace("Idel son", "Idel'son").replace("Nefed ev", "Nefed'ev");
        const isMajor = f.diameter_km >= 45 || ["Peary", "Hermite", "Whipple", "Shackleton", "Mons Malapert", "Mons Mouton", "Cabeus"].includes(cleanName);
        octx.font = isMajor ? "700 11px 'Plus Jakarta Sans', sans-serif" : "600 10px 'Plus Jakarta Sans', sans-serif";
        const tw = octx.measureText(cleanName).width + 10;

        // Try centered first, then slightly above/below if colliding with a candidate pin
        let chosenY = null;
        for (const dy of [0, -15, 15]) {
          const box = { x0: sx - tw / 2, y0: sy + dy - 8, x1: sx + tw / 2, y1: sy + dy + 8 };
          let hit = false;
          for (let j = 0; j < placedBoxes.length; j++) {
            const b = placedBoxes[j];
            if (!(box.x1 < b.x0 || box.x0 > b.x1 || box.y1 < b.y0 || box.y0 > b.y1)) {
              hit = true;
              break;
            }
          }
          if (!hit) {
            chosenY = sy + dy;
            placedBoxes.push(box);
            break;
          }
        }
        if (chosenY === null) continue;

        octx.lineWidth = 3;
        octx.strokeStyle = "rgba(4, 7, 13, 0.90)";
        octx.strokeText(cleanName, sx, chosenY + 3);
        octx.fillStyle = f.type.startsWith("Mons") ? "#fde68a" : "rgba(241, 245, 249, 0.92)";
        octx.fillText(cleanName, sx, chosenY + 3);
      }
      octx.restore();
    }

    // 3. Top 6 Ranked Artemis Base Camp Candidate Pins
    if (state.overlays.candidates && state.meta) {
      const cands = state.meta.poles[pole].candidates || [];
      octx.save();
      cands.forEach((c) => {
        const g = xyToGrid(c.x_km * 1000.0, c.y_km * 1000.0);
        const sx = tx + g.col * scale;
        const sy = ty + g.row * scale;
        if (sx < 10 || sx > w - 10 || sy < 10 || sy > h - 10) return;

        const isSel = state.selectedCandId === c.id;
        const rad = isSel ? 10 : 7.5;
        octx.beginPath();
        octx.arc(sx, sy, rad, 0, Math.PI * 2);
        octx.fillStyle = isSel ? "#fbbf24" : "#10b981";
        octx.fill();
        octx.lineWidth = isSel ? 2.5 : 1.5;
        octx.strokeStyle = "#041019";
        octx.stroke();

        octx.fillStyle = "#041019";
        octx.font = "800 9.5px 'Space Grotesk', monospace";
        octx.textAlign = "center";
        octx.textBaseline = "middle";
        octx.fillText(String(c.rank), sx, sy + 0.5);
      });
      octx.restore();
    }

    // 4. Active Rover Transect Line A -> B
    if (state.overlays.transect && state.activeTransect && state.activeTransect.pole === pole) {
      const tr = state.activeTransect;
      const g1 = xyToGrid(tr.x1, tr.y1);
      const g2 = xyToGrid(tr.x2, tr.y2);
      const x1 = tx + g1.col * scale, y1 = ty + g1.row * scale;
      const x2 = tx + g2.col * scale, y2 = ty + g2.row * scale;

      octx.save();
      octx.strokeStyle = "#38bdf8";
      octx.lineWidth = 2.4;
      octx.beginPath();
      octx.moveTo(x1, y1);
      octx.lineTo(x2, y2);
      octx.stroke();

      [
        [x1, y1, "A"],
        [x2, y2, "B"]
      ].forEach(([px, py, lbl]) => {
        octx.beginPath();
        octx.arc(px, py, 6.5, 0, Math.PI * 2);
        octx.fillStyle = "#38bdf8";
        octx.fill();
        octx.strokeStyle = "#04101d";
        octx.lineWidth = 1.5;
        octx.stroke();
        octx.fillStyle = "#04101d";
        octx.font = "800 9px 'Space Grotesk', monospace";
        octx.textAlign = "center";
        octx.textBaseline = "middle";
        octx.fillText(lbl, px, py + 0.5);
      });
      octx.restore();
    }
  }

  /* ---------------- Legend, Telemetry & Candidate Cards ---------------- */
  function updateLegend() {
    const titleEl = document.getElementById("legend-title");
    const gradEl = document.getElementById("legend-gradient");
    const ticksEl = document.getElementById("legend-ticks");

    const configs = {
      composite: {
        title: "ARTEMIS HLS SUITABILITY + LOLA RELIEF",
        grad: "linear-gradient(90deg, #06162e 0%, #3d4b5c 35%, #cbd5e1 65%, #10d48e 84%, #fbc62a 100%)",
        ticks: ["PSR Cold Trap", "LOLA Relief", "HLS Viable", "Peak Sun >78%"]
      },
      elevation: {
        title: "LOLA LASER ALTIMETRY ELEVATION (m)",
        grad: "linear-gradient(90deg, #0e2244 0%, #38627a 32%, #768894 52%, #dec6a4 80%, #faf4e8 100%)",
        ticks: ["-4,500 m", "-1,500 m", "+1,000 m", "+4,000 m", "+6,800 m"]
      },
      solar: {
        title: "SOLAR POWER CONTINUITY (% 18.6-YR CYCLE)",
        grad: "linear-gradient(90deg, #060810 0%, #4a2280 35%, #eb7a2a 72%, #fccc3a 88%, #fffcd4 100%)",
        ticks: ["0% (PSR)", "30%", "60%", "75%", "89%"]
      },
      thermal: {
        title: "DIVINER SURFACE TEMPERATURE (KELVIN)",
        grad: "linear-gradient(90deg, #22eeff 0%, #4844c4 28%, #882a94 42%, #cc4452 68%, #fef08a 100%)",
        ticks: ["26 K (-247°C)", "80 K", "110 K (H2O)", "180 K", "255 K"]
      },
      ice: {
        title: "DIVINER WATER-ICE STABILITY DEPTH (m)",
        grad: "linear-gradient(90deg, #91f6ff 0%, #2ec4f8 25%, #347ae8 55%, #30449e 78%, #64748b 100%)",
        ticks: ["0.0m Frost", "0.5m", "1.5m", "2.5m", ">2.5m Dry"]
      },
      earth: {
        title: "DIRECT-TO-EARTH (DTE) VISIBILITY (%)",
        grad: "linear-gradient(90deg, #0a0e18 0%, #166080 32%, #189e8e 58%, #44d494 80%, #d4f8ac 100%)",
        ticks: ["0% Far Side", "25%", "50%", "75%", "90%+"]
      }
    };

    const cfg = configs[state.layer] || configs.composite;
    titleEl.textContent = cfg.title;
    gradEl.style.background = cfg.grad;
    ticksEl.innerHTML = cfg.ticks.map((t) => `<span>${t}</span>`).join("");
  }

  function updateTelemetrySummary() {
    if (!state.poles.north || !state.poles.south || !state.meta) return;
    const dict = I18N[state.lang];
    const vn = state.poles.north.viableKm2;
    const vs = state.poles.south.viableKm2;
    const nStats = state.meta.poles.north.stats;
    const sStats = state.meta.poles.south.stats;

    const fmtKm = (v) => v >= 100 ? Math.round(v).toLocaleString() : v.toFixed(1);

    document.getElementById("badge-metric-north").textContent = `${dict.viable_prefix}: ${fmtKm(vn)} km²`;
    document.getElementById("badge-metric-south").textContent = `${dict.viable_prefix}: ${fmtKm(vs)} km²`;

    document.getElementById("vs-n-viable").textContent = `80°N: ${fmtKm(vn)} km²`;
    document.getElementById("vs-s-viable").textContent = `80°S: ${fmtKm(vs)} km²`;
    const totV = Math.max(0.01, vn + vs);
    document.getElementById("vs-bar-viable").style.width = `${Math.max(4, Math.min(96, (vn / totV) * 100)).toFixed(1)}%`;

    document.getElementById("vs-n-psr").textContent = `80°N: ${Math.round(nStats.psr_area_km2).toLocaleString()} km²`;
    document.getElementById("vs-s-psr").textContent = `80°S: ${Math.round(sStats.psr_area_km2).toLocaleString()} km²`;
    const totP = nStats.psr_area_km2 + sStats.psr_area_km2;
    document.getElementById("vs-bar-psr").style.width = `${((nStats.psr_area_km2 / totP) * 100).toFixed(1)}%`;

    const wMin = nStats.winter_solstice_obs
      ? nStats.winter_solstice_obs.hermite_winter_min_k
      : nStats.coldest_prp.temp_avg_k;
    document.getElementById("kpi-hermite-k").textContent = `${wMin.toFixed(1)} K`;
    document.getElementById("kpi-hermite-sub").textContent = `Hermite (${Math.round(wMin - 273.15)}°C)`;
    document.getElementById("kpi-peak-sun").textContent = `${nStats.peak_solar_60m_pct.toFixed(1)}%`;
    document.getElementById("kpi-surf-ice").textContent = `${Math.round(nStats.surface_ice_stable_km2).toLocaleString()} km²`;
    document.getElementById("kpi-relief").textContent = `${(sStats.relief_span_m / 1000.0).toFixed(1)} km`;
  }

  function renderCandidateCards() {
    if (!state.meta) return;
    const pole = state.candTab;
    const dict = I18N[state.lang];
    document.getElementById("cand-header-lbl").textContent =
      pole === "north" ? dict.sec_cands : dict.sec_cands_south;

    const listEl = document.getElementById("candidate-list");
    const cands = state.meta.poles[pole].candidates || [];
    listEl.innerHTML = cands
      .map((c) => {
        const latStr = `${Math.abs(c.lat).toFixed(2)}°${pole === "north" ? "N" : "S"}`;
        const lonStr = `${Math.abs(c.lon).toFixed(1)}°${c.lon >= 0 ? "E" : "W"}`;
        const selCls = state.selectedCandId === c.id ? "selected" : "";
        return `
        <div class="cand-card ${selCls}" data-cand-id="${c.id}" data-pole="${pole}">
          <div class="cand-top">
            <span class="cand-rank">#${c.rank}</span>
            <span class="cand-title">${c.title}</span>
            <span class="cand-coords">${latStr}, ${lonStr}</span>
          </div>
          <div class="cand-chips">
            <span>Sun ${c.sun_pct}%</span>
            <span>Slope ${c.slope_deg}°</span>
            <span>PSR ${c.dist_psr_km} km</span>
            <span>DTE ${c.earth_pct}%</span>
          </div>
        </div>`;
      })
      .join("");

    listEl.querySelectorAll(".cand-card").forEach((el) => {
      el.addEventListener("click", () => {
        const p = el.dataset.pole;
        const id = el.dataset.candId;
        state.selectedCandId = id;
        const cand = state.meta.poles[p].candidates.find((x) => x.id === id);
        if (cand) {
          if (state.mode !== "dual" && state.mode !== p) {
            setMode(p);
          }
          const g = xyToGrid(cand.x_km * 1000.0, cand.y_km * 1000.0);
          state.zoom = Math.max(state.zoom, 2.4);
          state.panX = g.col - N * 0.5;
          state.panY = g.row - N * 0.5;
          inspectGridCell(p, Math.round(g.col), Math.round(g.row));
          renderCandidateCards();
          redrawOverlays();
        }
      });
    });
  }

  function inspectGridCell(pole, col, row) {
    const pd = state.poles[pole];
    if (!pd || col < 0 || col >= N || row < 0 || row >= N) return;
    const idx = row * N + col;
    const { x, y } = gridToXY(col + 0.5, row + 0.5);
    const { lat, lon } = xyToLatLon(x, y, pole);

    document.getElementById("probe-pole-tag").textContent = pole === "north" ? "ARCTIC 80°N" : "SOUTH 80°S";
    document.getElementById("pr-latlon").textContent =
      `${Math.abs(lat).toFixed(2)}°${lat >= 0 ? "N" : "S"}, ${Math.abs(lon).toFixed(1)}°${lon >= 0 ? "E" : "W"}`;
    const ev = Math.round(pd.elev[idx]);
    document.getElementById("pr-elev").textContent = `${ev >= 0 ? "+" : ""}${ev.toLocaleString()} m`;
    document.getElementById("pr-slope").textContent = `${pd.slopeP90[idx].toFixed(1)}°`;
    document.getElementById("pr-sun").textContent = `${pd.sunPct[idx].toFixed(1)}%`;
    document.getElementById("pr-earth").textContent = `${pd.earthPct[idx].toFixed(1)}%`;

    const tmx = Number.isNaN(pd.tmaxK[idx]) ? "--" : `${Math.round(pd.tmaxK[idx])}`;
    const tmn = Number.isNaN(pd.tminK[idx]) ? "--" : `${Math.round(pd.tminK[idx])}`;
    document.getElementById("pr-temp").textContent = `${tmx} / ${tmn} K`;

    const ic = pd.iceCode[idx];
    let iceTxt = "> 2.5 m";
    if (ic === 0) iceTxt = "0.00 m (Frost)";
    else if (ic >= 1 && ic <= 250) iceTxt = `${(ic / 100.0).toFixed(2)} m`;
    else if (ic === 255) iceTxt = "--";
    document.getElementById("pr-ice").textContent = iceTxt;
    document.getElementById("pr-psr").textContent =
      pd.psrPct[idx] >= 50 ? "0.0 km (In PSR)" : `${pd.distPsrKm[idx].toFixed(1)} km`;
  }

  /* ---------------- Rover Transect Cross-Section SVG ---------------- */
  function activateTransect(pole, x1, y1, x2, y2, label) {
    state.activeTransect = { pole, x1, y1, x2, y2, label };
    renderTransectSVG();
    redrawOverlays();
  }

  function renderTransectSVG() {
    const svg = document.getElementById("transect-svg");
    const tr = state.activeTransect;
    if (!tr || !state.poles[tr.pole]) return;
    const pd = state.poles[tr.pole];

    const STEPS = 120;
    const distKm = Math.hypot(tr.x2 - tr.x1, tr.y2 - tr.y1) / 1000.0;
    document.getElementById("transect-title").textContent =
      `${tr.label || "ROVER TRANSECT"} (${distKm.toFixed(1)} km)`;

    const pts = [];
    let zMin = Infinity, zMax = -Infinity;
    for (let s = 0; s <= STEPS; s++) {
      const f = s / STEPS;
      const x = tr.x1 + (tr.x2 - tr.x1) * f;
      const y = tr.y1 + (tr.y2 - tr.y1) * f;
      const g = xyToGrid(x, y);
      const c = Math.max(0, Math.min(N - 1, Math.round(g.col)));
      const r = Math.max(0, Math.min(N - 1, Math.round(g.row)));
      const idx = r * N + c;
      const z = pd.elev[idx];
      if (z < zMin) zMin = z;
      if (z > zMax) zMax = z;
      pts.push({
        d: f * distKm,
        z,
        sun: pd.sunPct[idx],
        psr: pd.psrPct[idx] >= 40,
        tk: !Number.isNaN(pd.tminK[idx]) ? pd.tminK[idx] : pd.tmaxK[idx]
      });
    }

    const W = 760, H = 126;
    const padL = 50, padR = 64, padT = 12, padB = 22;
    const pw = W - padL - padR;
    const ph = H - padT - padB;
    const zSpan = Math.max(200, zMax - zMin);
    const zLo = zMin - zSpan * 0.08;
    const zHi = zMax + zSpan * 0.10;

    const xOf = (i) => padL + (i / STEPS) * pw;
    const yElev = (z) => padT + (1 - (z - zLo) / (zHi - zLo)) * ph;
    const ySun = (s) => padT + (1 - s / 100.0) * ph;

    let areaD = `M ${padL.toFixed(1)} ${(padT + ph).toFixed(1)} `;
    let lineD = "";
    let sunD = "";
    let psrRects = "";

    for (let i = 0; i <= STEPS; i++) {
      const px = xOf(i).toFixed(1);
      const py = yElev(pts[i].z).toFixed(1);
      const sy = ySun(pts[i].sun).toFixed(1);
      areaD += `L ${px} ${py} `;
      lineD += (i === 0 ? "M " : "L ") + `${px} ${py} `;
      sunD += (i === 0 ? "M " : "L ") + `${px} ${sy} `;
      if (pts[i].psr) {
        const bw = (pw / STEPS + 0.8).toFixed(1);
        psrRects += `<rect x="${px}" y="${padT}" width="${bw}" height="${ph}" fill="rgba(34,211,238,0.13)" />`;
      }
    }
    areaD += `L ${(padL + pw).toFixed(1)} ${(padT + ph).toFixed(1)} Z`;

    svg.innerHTML = `
      <defs>
        <linearGradient id="elevFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.42" />
          <stop offset="100%" stop-color="#0f172a" stop-opacity="0.08" />
        </linearGradient>
      </defs>
      ${psrRects}
      <line x1="${padL}" y1="${padT + ph}" x2="${padL + pw}" y2="${padT + ph}" stroke="rgba(148,163,184,0.28)" />
      <line x1="${padL}" y1="${padT + ph * 0.5}" x2="${padL + pw}" y2="${padT + ph * 0.5}" stroke="rgba(148,163,184,0.14)" stroke-dasharray="3,3" />
      <path d="${areaD}" fill="url(#elevFill)" />
      <path d="${lineD}" fill="none" stroke="#e2e8f0" stroke-width="2" />
      <path d="${sunD}" fill="none" stroke="#fbbf24" stroke-width="1.6" stroke-dasharray="4,2" />
      <text x="${padL - 5}" y="${padT + 9}" fill="#e2e8f0" font-size="9.5" font-family="Space Grotesk, monospace" text-anchor="end">${Math.round(zMax)}m</text>
      <text x="${padL - 5}" y="${padT + ph}" fill="#94a3b8" font-size="9.5" font-family="Space Grotesk, monospace" text-anchor="end">${Math.round(zMin)}m</text>
      <text x="${padL + pw + 5}" y="${padT + 9}" fill="#fbbf24" font-size="9.5" font-family="Space Grotesk, monospace">100% Sun</text>
      <text x="${padL + pw + 5}" y="${padT + ph}" fill="#22d3ee" font-size="9.5" font-family="Space Grotesk, monospace">0% PSR</text>
      <text x="${padL}" y="${H - 5}" fill="#94a3b8" font-size="9.5" font-family="Space Grotesk, monospace">A (0 km)</text>
      <text x="${padL + pw}" y="${H - 5}" fill="#94a3b8" font-size="9.5" font-family="Space Grotesk, monospace" text-anchor="end">B (${distKm.toFixed(1)} km)</text>
    `;
  }

  /* ---------------- Master Redraw Pipeline ---------------- */
  function recomputeAllRasters() {
    renderPoleRaster(state.poles.north);
    renderPoleRaster(state.poles.south);
    updateTelemetrySummary();
    redrawOverlays();
  }

  function redrawOverlays() {
    drawPoleViewport("north");
    drawPoleViewport("south");
  }

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll(".mode-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.mode === mode);
    });
    const grid = document.getElementById("canvas-grid");
    const vpN = document.getElementById("vp-north");
    const vpS = document.getElementById("vp-south");
    grid.classList.toggle("dual-mode", mode === "dual");
    vpN.classList.toggle("hidden", mode === "south");
    vpS.classList.toggle("hidden", mode === "north");
    requestAnimationFrame(redrawOverlays);
  }

  function applyLanguage(lang) {
    state.lang = lang;
    localStorage.setItem("sounny_lang", lang);
    document.documentElement.lang = lang;
    document.querySelectorAll(".lang-toggle [data-lang]").forEach((b) => {
      b.classList.toggle("active", b.dataset.lang === lang);
    });
    const dict = I18N[lang];
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const k = el.dataset.i18n;
      if (dict[k]) {
        if (k === "sources_copy") el.innerHTML = dict[k];
        else el.textContent = dict[k];
      }
    });
    document.getElementById("lbl-earth-mode").textContent =
      state.radioQuiet ? dict.sl_earth_quiet : dict.sl_earth;
    renderTransectPills();
    renderCandidateCards();
    updateTelemetrySummary();
    redrawOverlays();
  }

  function renderTransectPills() {
    if (!state.meta) return;
    const wrap = document.getElementById("transect-presets");
    wrap.innerHTML = state.meta.transects
      .map((t, idx) => {
        const lbl = state.lang === "fr" ? t.label_fr : t.label_en;
        const active = state.activeTransect && state.activeTransect.id === t.id ? "active" : (!state.activeTransect && idx === 0 ? "active" : "");
        return `<button class="transect-pill ${active}" data-tr-id="${t.id}">${lbl}</button>`;
      })
      .join("");

    wrap.querySelectorAll(".transect-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        const t = state.meta.transects.find((x) => x.id === btn.dataset.trId);
        if (!t) return;
        const a = latLonToXY(t.p1.lat, t.p1.lon, t.pole);
        const b = latLonToXY(t.p2.lat, t.p2.lon, t.pole);
        const lbl = state.lang === "fr" ? t.label_fr : t.label_en;
        state.activeTransect = { id: t.id, pole: t.pole, x1: a.x, y1: a.y, x2: b.x, y2: b.y, label: lbl };
        if (state.mode !== "dual" && state.mode !== t.pole) setMode(t.pole);
        renderTransectPills();
        renderTransectSVG();
        redrawOverlays();
      });
    });
  }

  /* ---------------- Interactive Bindings ---------------- */
  function bindUI() {
    // Mode switcher
    document.querySelectorAll(".mode-btn").forEach((btn) => {
      btn.addEventListener("click", () => setMode(btn.dataset.mode));
    });

    // Language toggle
    document.querySelectorAll(".lang-toggle [data-lang]").forEach((btn) => {
      btn.addEventListener("click", () => applyLanguage(btn.dataset.lang));
    });

    // Layer selector + keyboard 1..6
    const selectLayer = (lyr) => {
      state.layer = lyr;
      document.querySelectorAll(".layer-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.layer === lyr);
      });
      updateLegend();
      recomputeAllRasters();
    };
    document.querySelectorAll(".layer-btn").forEach((btn) => {
      btn.addEventListener("click", () => selectLayer(btn.dataset.layer));
    });
    window.addEventListener("keydown", (e) => {
      if (e.target.tagName === "INPUT") return;
      const map = { "1": "composite", "2": "elevation", "3": "solar", "4": "thermal", "5": "ice", "6": "earth" };
      if (map[e.key]) selectLayer(map[e.key]);
    });

    // Sun azimuth dial + Lunar Day animation
    const sunSlider = document.getElementById("slider-sun-az");
    const sunVal = document.getElementById("sun-az-val");
    sunSlider.addEventListener("input", () => {
      state.sunAzDeg = Number(sunSlider.value);
      sunVal.textContent = `${state.sunAzDeg}° E`;
      recomputeAllRasters();
    });

    const playBtn = document.getElementById("btn-play-sun");
    const playIcon = document.getElementById("icon-play-sun");
    let rafId = null;
    const stepSun = () => {
      if (!state.playingSun) return;
      state.sunAzDeg = (state.sunAzDeg + 1.5) % 360;
      sunSlider.value = String(Math.floor(state.sunAzDeg));
      sunVal.textContent = `${Math.floor(state.sunAzDeg)}° E`;
      recomputeAllRasters();
      rafId = requestAnimationFrame(stepSun);
    };
    playBtn.addEventListener("click", () => {
      state.playingSun = !state.playingSun;
      playBtn.classList.toggle("playing", state.playingSun);
      playIcon.className = state.playingSun ? "fa-solid fa-pause" : "fa-solid fa-play";
      if (state.playingSun) stepSun();
      else if (rafId) cancelAnimationFrame(rafId);
    });

    // Presets & Sliders
    const slSun = document.getElementById("sl-min-sun");
    const slSlope = document.getElementById("sl-max-slope");
    const slPsr = document.getElementById("sl-max-psr");
    const slEarth = document.getElementById("sl-earth");

    function syncSlidersUI() {
      slSun.value = String(state.minSun);
      slSlope.value = String(state.maxSlope);
      slPsr.value = String(state.maxPsr);
      slEarth.value = String(state.earthVal);
      document.getElementById("val-min-sun").innerHTML = `&ge; ${state.minSun}%`;
      document.getElementById("val-max-slope").innerHTML = `&le; ${state.maxSlope.toFixed(1)}°`;
      document.getElementById("val-max-psr").innerHTML = `&le; ${state.maxPsr.toFixed(1)} km`;
      document.getElementById("val-earth").innerHTML =
        state.radioQuiet ? `&le; ${state.earthVal}%` : `&ge; ${state.earthVal}%`;
      document.getElementById("lbl-earth-mode").textContent =
        state.radioQuiet ? I18N[state.lang].sl_earth_quiet : I18N[state.lang].sl_earth;
    }

    document.querySelectorAll(".preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.preset;
        const p = PRESETS[key];
        if (!p) return;
        state.preset = key;
        Object.assign(state, p);
        document.querySelectorAll(".preset-btn").forEach((b) => b.classList.toggle("active", b === btn));
        syncSlidersUI();
        if (state.layer !== "composite") selectLayer("composite");
        else recomputeAllRasters();
      });
    });

    [
      [slSun, (v) => (state.minSun = v)],
      [slSlope, (v) => (state.maxSlope = v)],
      [slPsr, (v) => (state.maxPsr = v)],
      [slEarth, (v) => (state.earthVal = v)]
    ].forEach(([el, setter]) => {
      el.addEventListener("input", () => {
        setter(Number(el.value));
        document.querySelectorAll(".preset-btn").forEach((b) => b.classList.remove("active"));
        syncSlidersUI();
        recomputeAllRasters();
      });
    });

    // Cartographic overlay toggles
    document.querySelectorAll(".chip-toggle").forEach((btn) => {
      btn.addEventListener("click", () => {
        const k = btn.dataset.ov;
        state.overlays[k] = !state.overlays[k];
        btn.classList.toggle("active", state.overlays[k]);
        redrawOverlays();
      });
    });

    // Candidate tab North / South
    document.getElementById("cand-tab-north").addEventListener("click", () => {
      state.candTab = "north";
      document.getElementById("cand-tab-north").classList.add("active");
      document.getElementById("cand-tab-south").classList.remove("active");
      renderCandidateCards();
    });
    document.getElementById("cand-tab-south").addEventListener("click", () => {
      state.candTab = "south";
      document.getElementById("cand-tab-south").classList.add("active");
      document.getElementById("cand-tab-north").classList.remove("active");
      renderCandidateCards();
    });

    // Zoom / Reset / Transect tools
    document.getElementById("btn-zoom-in").addEventListener("click", () => {
      state.zoom = Math.min(8.0, state.zoom * 1.35);
      redrawOverlays();
    });
    document.getElementById("btn-zoom-out").addEventListener("click", () => {
      state.zoom = Math.max(0.85, state.zoom / 1.35);
      redrawOverlays();
    });
    document.getElementById("btn-reset-view").addEventListener("click", () => {
      state.zoom = 1.0;
      state.panX = 0;
      state.panY = 0;
      state.selectedCandId = null;
      renderCandidateCards();
      redrawOverlays();
    });

    const btnDrawTr = document.getElementById("btn-draw-transect");
    btnDrawTr.addEventListener("click", () => {
      state.drawingTransect = !state.drawingTransect;
      state.drawStart = null;
      btnDrawTr.classList.toggle("active", state.drawingTransect);
    });

    const btnDrawer = document.getElementById("btn-toggle-drawer");
    const drawer = document.getElementById("transect-drawer");
    btnDrawer.addEventListener("click", () => {
      const collapsed = drawer.classList.toggle("collapsed");
      btnDrawer.classList.toggle("active", !collapsed);
      requestAnimationFrame(redrawOverlays);
    });

    // Pan, Wheel Zoom, Pixel Probe & 2-Point Transect on Viewports
    ["north", "south"].forEach((pole) => {
      const vp = document.getElementById(`vp-${pole}`);
      let dragging = false;
      let lastX = 0, lastY = 0;

      vp.addEventListener("pointerdown", (e) => {
        const { scale, tx, ty } = getViewportTransform(vp);
        const rect = vp.getBoundingClientRect();
        const col = (e.clientX - rect.left - tx) / scale;
        const row = (e.clientY - rect.top - ty) / scale;

        if (state.drawingTransect) {
          const pt = gridToXY(col, row);
          if (!state.drawStart || state.drawStart.pole !== pole) {
            state.drawStart = { pole, x: pt.x, y: pt.y };
          } else {
            activateTransect(pole, state.drawStart.x, state.drawStart.y, pt.x, pt.y, "CUSTOM ROVER TRANSECT");
            state.drawingTransect = false;
            state.drawStart = null;
            btnDrawTr.classList.remove("active");
            document.querySelectorAll(".transect-pill").forEach((b) => b.classList.remove("active"));
          }
          return;
        }

        dragging = true;
        lastX = e.clientX;
        lastY = e.clientY;
        vp.setPointerCapture(e.pointerId);
      });

      vp.addEventListener("pointermove", (e) => {
        const { scale, tx, ty } = getViewportTransform(vp);
        const rect = vp.getBoundingClientRect();
        const col = Math.floor((e.clientX - rect.left - tx) / scale);
        const row = Math.floor((e.clientY - rect.top - ty) / scale);
        inspectGridCell(pole, col, row);

        if (dragging) {
          const dx = e.clientX - lastX;
          const dy = e.clientY - lastY;
          lastX = e.clientX;
          lastY = e.clientY;
          state.panX = Math.max(-N * 0.45, Math.min(N * 0.45, state.panX - dx / scale));
          state.panY = Math.max(-N * 0.45, Math.min(N * 0.45, state.panY - dy / scale));
          redrawOverlays();
        }
      });

      vp.addEventListener("pointerup", () => { dragging = false; });
      vp.addEventListener("pointercancel", () => { dragging = false; });

      vp.addEventListener("wheel", (e) => {
        e.preventDefault();
        const { scale, tx, ty } = getViewportTransform(vp);
        const rect = vp.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const gCol = (mx - tx) / scale;
        const gRow = (my - ty) / scale;

        const factor = e.deltaY < 0 ? 1.18 : 1 / 1.18;
        const nextZoom = Math.max(0.85, Math.min(8.0, state.zoom * factor));
        const baseScale = scale / state.zoom;
        const nextScale = baseScale * nextZoom;

        state.zoom = nextZoom;
        state.panX = gCol - N * 0.5 - (mx - rect.width * 0.5) / nextScale;
        state.panY = gRow - N * 0.5 - (my - rect.height * 0.5) / nextScale;
        redrawOverlays();
      }, { passive: false });
    });

    window.addEventListener("resize", () => requestAnimationFrame(redrawOverlays));
  }

  /* ---------------- Bootstrap ---------------- */
  async function init() {
    bindUI();
    updateLegend();

    const resp = await fetch("assets/polar_atlas_meta.json");
    const meta = await resp.json();
    state.meta = meta;
    N = meta.grid.size;
    HALF_EXTENT = meta.grid.half_extent_m;
    CELL_RES = meta.grid.cell_res_m;
    R_MOON = meta.grid.moon_radius_m;
    RHO_80 = 2.0 * R_MOON * Math.tan((10.0 * Math.PI) / 360.0);

    const [northData, southData] = await Promise.all([decodePole("north"), decodePole("south")]);
    state.poles.north = northData;
    state.poles.south = southData;

    // Default active transect: Peary Sunlit Rim -> Whipple Ice Cold Trap
    const tr0 = meta.transects[0];
    const pA = latLonToXY(tr0.p1.lat, tr0.p1.lon, tr0.pole);
    const pB = latLonToXY(tr0.p2.lat, tr0.p2.lon, tr0.pole);
    state.activeTransect = {
      id: tr0.id,
      pole: tr0.pole,
      x1: pA.x,
      y1: pA.y,
      x2: pB.x,
      y2: pB.y,
      label: state.lang === "fr" ? tr0.label_fr : tr0.label_en
    };

    applyLanguage(state.lang);
    recomputeAllRasters();
    renderTransectSVG();

    // Seed initial probe telemetry with #1 Artemis North Candidate
    if (meta.poles.north.candidates.length > 0) {
      const c0 = meta.poles.north.candidates[0];
      const g0 = xyToGrid(c0.x_km * 1000.0, c0.y_km * 1000.0);
      inspectGridCell("north", Math.round(g0.col), Math.round(g0.row));
    }

    document.getElementById("loading-overlay").classList.add("done");
  }

  init().catch((err) => {
    console.error(err);
    document.getElementById("loading-overlay").innerHTML =
      `<div style="color:#f43f5e;font-family:monospace;padding:1rem;">Error loading NASA polar assets: ${err.message}</div>`;
  });
})();
