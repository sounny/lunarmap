(() => {
  'use strict';

  const I18N = {
    en: {
      pole_north: 'North Pole · 80°N',
      pole_south: 'South Pole · 80°S',
      fact_sun: 'Peak Sun',
      fact_psr: 'Perm. Shadow',
      sec_lenses: 'ORBITAL LENS',
      sec_webgl: 'REAL-TIME GPU',
      probe_lbl: 'SURFACE PROBE',
      reset_view: 'Reset Orbit',
      far_side: '180° FAR SIDE',
      near_side: '0° EARTH',
      lbl_elev: 'ELEVATION',
      lbl_sun: 'SOLAR 18.6Y',
      lbl_temp: 'DIVINER AVG',
      mode_shadow: 'Sunlight',
      mode_light: 'Peak Sun',
      mode_cold: 'Ice Traps',
      scroll_zoom: 'SCROLL TO ZOOM',
      loading: 'LOADING NASA LRO POLAR TOPOGRAPHY',
      poles: {
        north: {
          eyebrow: 'NASA LRO · 80°N - 90°N',
          title: 'LUNAR NORTH POLE',
          subtitle: 'Sweep the grazing +1.54° summer polar sun across sunlit crater rims, permanent shadows, and 24.7 K cold traps.',
          sun_horizon: '+1.54° Summer Horizon Sun',
        },
        south: {
          eyebrow: 'NASA LRO · 80°S - 90°S',
          title: 'LUNAR SOUTH POLE',
          subtitle: 'Sweep the grazing -1.54° summer polar sun across Shackleton\'s rim, Mons Malapert, and 25.5 K cold traps.',
          sun_horizon: '-1.54° Summer Horizon Sun',
        },
      },
    },
    fr: {
      pole_north: 'Pôle Nord · 80°N',
      pole_south: 'Pôle Sud · 80°S',
      fact_sun: 'Pic Solaire',
      fact_psr: 'Ombre Perm.',
      sec_lenses: 'FILTRE ORBITAL',
      sec_webgl: 'GPU TEMPS RÉEL',
      probe_lbl: 'SONDE DE SURFACE',
      reset_view: 'Réinitialiser',
      far_side: '180° FACE CACHÉE',
      near_side: '0° TERRE',
      lbl_elev: 'ALTITUDE',
      lbl_sun: 'SOLEIL 18,6A',
      lbl_temp: 'MOY. DIVINER',
      mode_shadow: 'Lumière',
      mode_light: 'Pic Solaire',
      mode_cold: 'Pièges Glace',
      scroll_zoom: 'ZOOM MOLETTE',
      loading: 'CHARGEMENT TOPOGRAPHIE POLAIRE NASA LRO',
      poles: {
        north: {
          eyebrow: 'NASA LRO · 80°N - 90°N',
          title: 'PÔLE NORD LUNAIRE',
          subtitle: 'Faites glisser le Soleil polaire rasant (+1,54°) sur les crêtes éclairées, les ombres permanentes et les pièges à 24,7 K.',
          sun_horizon: 'Soleil Rasant d\'Été +1,54°',
        },
        south: {
          eyebrow: 'NASA LRO · 80°S - 90°S',
          title: 'PÔLE SUD LUNAIRE',
          subtitle: 'Faites glisser le Soleil polaire rasant (-1,54°) sur le rempart de Shackleton, Mons Malapert et les pièges à 25,5 K.',
          sun_horizon: 'Soleil Rasant d\'Été -1,54°',
        },
      },
    },
  };

  const VERT_SRC = `#version 300 es
  in vec2 a_pos;
  void main() {
    gl_Position = vec4(a_pos, 0.0, 1.0);
  }`;

  const FRAG_SRC = `#version 300 es
  precision highp float;

  uniform sampler2D u_demTex;
  uniform sampler2D u_sciTex;
  uniform vec2 u_resolution;
  uniform float u_zoom;
  uniform vec2 u_pan;
  uniform float u_hemi;       // +1.0 for North (IAU_2015:30130), -1.0 for South (IAU_2015:30135)
  uniform float u_elevOffset; // -5500.0 North, -7500.0 South
  uniform float u_elevSpan;   //  8500.0 North, 15000.0 South
  uniform float u_sunLonRad;
  uniform float u_subLatRad;
  uniform vec3 u_modeWeights; // x: shadow, y: peak sunlight, z: cryogenic cold traps

  out vec4 fragColor;

  const float R_MOON = 1737400.0;
  const float HALF_EXTENT = 304000.0;
  const float RES_2K = 608000.0 / 2048.0;

  // Single-tap 16-bit elevation fetch for distant shadow raymarching
  float sampleElevFast(vec2 uv) {
    ivec2 ts = textureSize(u_demTex, 0);
    ivec2 ic = clamp(ivec2(uv * vec2(ts)), ivec2(0), ts - 1);
    vec4 t = texelFetch(u_demTex, ic, 0);
    return ((t.r * 255.0 * 256.0 + t.g * 255.0) / 65535.0) * u_elevSpan + u_elevOffset;
  }

  // Exact 16-bit bilinear elevation fetch (zero RG wrap artifacts)
  float sampleElev(vec2 uv) {
    vec2 ts = vec2(textureSize(u_demTex, 0));
    vec2 c = uv * ts - 0.5;
    ivec2 i0 = clamp(ivec2(floor(c)), ivec2(0), ivec2(ts) - 1);
    ivec2 i1 = clamp(i0 + ivec2(1), ivec2(0), ivec2(ts) - 1);
    vec2 f = fract(c);

    vec4 t00 = texelFetch(u_demTex, i0, 0);
    vec4 t10 = texelFetch(u_demTex, ivec2(i1.x, i0.y), 0);
    vec4 t01 = texelFetch(u_demTex, ivec2(i0.x, i1.y), 0);
    vec4 t11 = texelFetch(u_demTex, i1, 0);

    float h00 = ((t00.r * 255.0 * 256.0 + t00.g * 255.0) / 65535.0) * u_elevSpan + u_elevOffset;
    float h10 = ((t10.r * 255.0 * 256.0 + t10.g * 255.0) / 65535.0) * u_elevSpan + u_elevOffset;
    float h01 = ((t01.r * 255.0 * 256.0 + t01.g * 255.0) / 65535.0) * u_elevSpan + u_elevOffset;
    float h11 = ((t11.r * 255.0 * 256.0 + t11.g * 255.0) / 65535.0) * u_elevSpan + u_elevOffset;

    return mix(mix(h00, h10, f.x), mix(h01, h11, f.x), f.y);
  }

  // Right-handed local polar stereographic unit sphere (Z outward at pole in both hemispheres)
  vec3 moonUnitSphere(vec2 xy) {
    float rho2 = dot(xy, xy);
    float d = 4.0 * R_MOON * R_MOON + rho2;
    return vec3(
      4.0 * R_MOON * xy.x / d,
      4.0 * R_MOON * xy.y / d,
      (4.0 * R_MOON * R_MOON - rho2) / d
    );
  }

  void main() {
    vec2 screenUV = vec2(gl_FragCoord.x / u_resolution.x, 1.0 - gl_FragCoord.y / u_resolution.y);
    vec2 uv = (screenUV - 0.5) / u_zoom + 0.5 + u_pan;

    vec2 xy = vec2(
      -HALF_EXTENT + uv.x * (2.0 * HALF_EXTENT),
      +HALF_EXTENT - uv.y * (2.0 * HALF_EXTENT)
    );

    float rNorm = length(xy) / HALF_EXTENT;
    if (rNorm > 1.002) {
      fragColor = vec4(0.0, 0.0, 0.0, 0.0);
      return;
    }

    float h0 = sampleElev(uv);

    // True unexaggerated (1.0x) local slope & 3D surface normal on Moon sphere
    float du = 1.0 / 2048.0;
    float hR = sampleElev(uv + vec2(du, 0.0));
    float hL = sampleElev(uv - vec2(du, 0.0));
    float hU = sampleElev(uv - vec2(0.0, du));
    float hD = sampleElev(uv + vec2(0.0, du));

    float dzdx = (hR - hL) / (2.0 * RES_2K);
    float dzdy = (hU - hD) / (2.0 * RES_2K);

    vec3 uSphere = moonUnitSphere(xy);
    vec3 east = normalize(vec3(1.0, 0.0, 0.0) - uSphere * uSphere.x);
    vec3 northY = normalize(cross(uSphere, east));
    vec3 surfNormal = normalize(uSphere - (dzdx * east + dzdy * northY));

    // True 3D solar unit vector in hemisphere stereographic frame
    vec3 sunDir = normalize(vec3(
      cos(u_subLatRad) * sin(u_sunLonRad),
      -u_hemi * cos(u_subLatRad) * cos(u_sunLonRad),
      u_hemi * sin(u_subLatRad)
    ));

    // 40-step 3D Spherical Lunar Horizon Raymarching with 0.53° Solar Disc Penumbra
    float shadow = 1.0;
    float horizonDot = dot(uSphere, sunDir);
    if (horizonDot < -0.09) {
      shadow = 0.0;
    } else {
      vec3 P0 = uSphere * (R_MOON + h0 + 1.5);
      float maxOcc = -1.0;
      float t = 340.0;
      for (int i = 0; i < 40; i++) {
        vec3 P = P0 + sunDir * t;
        float rRay = length(P);
        vec3 uStep = P / rRay;
        vec2 xyStep = (2.0 * R_MOON / (1.0 + uStep.z)) * uStep.xy;
        if (length(xyStep) > HALF_EXTENT * 1.01) {
          break;
        }
        vec2 uvStep = vec2(
          (xyStep.x + HALF_EXTENT) / (2.0 * HALF_EXTENT),
          (HALF_EXTENT - xyStep.y) / (2.0 * HALF_EXTENT)
        );
        float hStep = sampleElevFast(uvStep);
        float diff = (R_MOON + hStep) - rRay;
        float ang = diff / t;
        maxOcc = max(maxOcc, ang);
        if (maxOcc > 0.0052) {
          shadow = 0.0;
          break;
        }
        t *= 1.168;
      }
      if (shadow > 0.0) {
        shadow = 1.0 - smoothstep(-0.00465, 0.00465, maxOcc);
      }
    }

    // Exact Lommel-Seeliger lunar regolith photometric reflectance: 2 * mu0 / (mu0 + mu)
    float mu0 = max(dot(surfNormal, sunDir), 0.0);
    float mu = max(dot(surfNormal, uSphere), 0.12);
    float ls = (mu0 > 0.0) ? (2.0 * mu0 / (mu0 + mu)) : 0.0;

    // Physically bounded near-side-only Earthshine (-90° < lon < +90° <=> -u_hemi * xy.y > 0)
    vec3 earthDir = normalize(vec3(0.0, -u_hemi, 0.095));
    float nearSideMask = (-u_hemi * xy.y > 0.0) ? 1.0 : 0.0;
    float earthVis = clamp(texture(u_sciTex, uv).a, 0.0, 1.0) * nearSideMask;
    float earthInc = max(dot(surfNormal, earthDir), 0.0);
    vec3 earthshine = vec3(0.026, 0.035, 0.054) * earthVis * (0.25 + 0.75 * earthInc);
    vec3 starlightFloor = vec3(0.010, 0.013, 0.020);

    // sRGB display transfer on uniform-albedo Lommel-Seeliger radiance (zero synthetic albedo or noise)
    float directLit = pow(clamp(ls * shadow, 0.0, 1.0), 1.0 / 2.2) * 1.08;
    vec3 sunlitCol = vec3(0.95, 0.955, 0.97) * directLit;
    vec3 shadowScene = starlightFloor + earthshine + sunlitCol;

    // Sample Scientific Channels
    float solarPct = texture(u_demTex, uv).b * 100.0;
    vec4 sci = texture(u_sciTex, uv);
    float tempK = sci.r * 200.0 + 20.0;

    // Integer texelFetch for exact surface-frost flag (g_ice == 0 iff ice_depth == 0.0 m)
    ivec2 icSci = clamp(ivec2(uv * vec2(textureSize(u_sciTex, 0))), ivec2(0), textureSize(u_sciTex, 0) - 1);
    float iceExact = texelFetch(u_sciTex, icSci, 0).g * 255.0;

    // Dark sculpted lunar base for scientific luminescence modes
    float reliefShade = 0.22 + 0.62 * ls * (0.35 + 0.65 * shadow);
    vec3 darkMoon = vec3(0.055, 0.068, 0.092) * (0.6 + 1.5 * reliefShade);

    // Mode 2: Peak Polar Sunlight (Quasi-continuous sunlit crests over 18.6-year nodal precession cycle)
    float sPeak = max(solarPct, max(
      max(texture(u_demTex, uv + vec2(du * 2.0, 0.0)).b, texture(u_demTex, uv - vec2(du * 2.0, 0.0)).b),
      max(texture(u_demTex, uv + vec2(0.0, du * 2.0)).b, texture(u_demTex, uv - vec2(0.0, du * 2.0)).b)
    ) * 100.0);
    float sunWarm = smoothstep(47.0, 62.0, sPeak);
    float sunHot  = smoothstep(56.0, 76.0, sPeak);
    float sunCore = smoothstep(70.0, 88.0, solarPct);
    vec3 goldAmber = vec3(0.76, 0.38, 0.04);
    vec3 goldBright = vec3(1.00, 0.78, 0.16);
    vec3 goldWhite = vec3(1.00, 0.98, 0.86);
    vec3 goldCol = mix(goldAmber, goldBright, sunHot);
    goldCol = mix(goldCol, goldWhite, sunCore);
    vec3 lightBase = shadowScene * 0.28 + darkMoon * 0.42;
    vec3 lightScene = mix(lightBase, goldCol * (0.88 + 0.30 * sunHot), clamp(sunWarm * 1.18, 0.0, 1.0));

    // Mode 3: Cryogenic Cold Traps & Surface Water Frost (Sapphire-Cyan Luminescence)
    float coldT = 1.0 - smoothstep(24.0, 110.0, tempK);
    float ultraCold = 1.0 - smoothstep(24.0, 48.0, tempK);
    float surfaceFrost = (iceExact < 0.5) ? 1.0 : 0.0;
    vec3 cryoDeep = vec3(0.05, 0.32, 0.62);
    vec3 cryoMid  = vec3(0.20, 0.72, 0.98);
    vec3 cryoIce  = vec3(0.86, 0.97, 1.00);
    vec3 coldCol = mix(cryoDeep, cryoMid, coldT);
    coldCol = mix(coldCol, cryoIce, clamp(ultraCold * 0.85 + surfaceFrost * 0.45, 0.0, 1.0));
    float coldMask = clamp(coldT * 1.15, 0.0, 1.0);
    vec3 coldScene = mix(shadowScene * 0.48 + darkMoon * 0.35, coldCol * 0.95, coldMask);

    // Smoothly blend active lens
    vec3 col = shadowScene * u_modeWeights.x
             + lightScene  * u_modeWeights.y
             + coldScene   * u_modeWeights.z;

    // Subtle spherical limb darkening + crisp 1px rim highlight at 80° boundary
    float limbVignette = 1.0 - 0.16 * smoothstep(0.78, 1.0, rNorm);
    float rimLine = smoothstep(0.993, 0.9985, rNorm) * (1.0 - smoothstep(0.9985, 1.001, rNorm));
    col = col * limbVignette + vec3(0.32, 0.38, 0.48) * rimLine * 0.45;

    // Anti-aliased circular clip
    float alpha = 1.0 - smoothstep(0.997, 1.001, rNorm);
    fragColor = vec4(clamp(col, 0.0, 1.0), alpha);
  }`;

  const MODE_INDEX = { shadow: 0, light: 1, cold: 2 };

  // Application State
  const state = {
    lang: localStorage.getItem('sounny_lang') || 'en',
    pole: 'north',
    mode: 'shadow',
    weights: [1, 0, 0],
    targetWeights: [1, 0, 0],
    sunLonDeg: 132.0,
    subLatDeg: 1.54,
    orbitPlaying: false,
    zoom: 1.0,
    targetZoom: 1.0,
    pan: { x: 0, y: 0 },
    targetPan: { x: 0, y: 0 },
    activeLandmarkIdx: 0,
    atlasMeta: null,
    poleMeta: null,
    cpuDem: null,
    cpuSci: null,
  };

  // Cached GPU textures + CPU RGBA buffers per hemisphere ('north' | 'south')
  const poleCache = {};
  const polePromises = {};

  // DOM References
  const starCanvas = document.getElementById('starfield');
  const glCanvas = document.getElementById('gl-canvas');
  const moonDisc = document.getElementById('moon-disc');
  const overlaySvg = document.getElementById('moon-overlay-svg');
  const dialTicksG = document.getElementById('dial-ticks');
  const sunHandle = document.getElementById('sun-handle');
  const sunAzLabel = document.getElementById('sun-az-label');
  const sunDialSvg = document.getElementById('sun-dial-svg');
  const cardinalTop = document.getElementById('cardinal-top');
  const cardinalBottom = document.getElementById('cardinal-bottom');
  const crsStamp = document.getElementById('crs-stamp');
  const btnResetZoom = document.getElementById('btn-reset-zoom');
  const btnPlaySun = document.getElementById('btn-play-sun');
  const btnPlaySunMobile = document.getElementById('btn-play-sun-mobile');
  const rngAzimuth = document.getElementById('rng-azimuth');
  const panelSunAz = document.getElementById('panel-sun-az');
  const scaleLabel = document.getElementById('scale-label');
  const scaleLine = document.getElementById('scale-line');
  const loadingVeil = document.getElementById('loading-veil');

  // ─── 1. Subtle Deep-Space Starfield ───
  function renderStarfield() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;
    starCanvas.width = Math.round(w * dpr);
    starCanvas.height = Math.round(h * dpr);
    const ctx = starCanvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    let seed = 42197;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };

    const count = Math.round((w * h) / 4200);
    for (let i = 0; i < count; i++) {
      const x = rand() * w;
      const y = rand() * h;
      const r = 0.35 + Math.pow(rand(), 3.0) * 1.15;
      const alpha = 0.08 + Math.pow(rand(), 2.2) * 0.48;
      const tint = rand();
      const col = tint < 0.25 ? `rgba(186, 214, 255, ${alpha})`
                : tint < 0.82 ? `rgba(241, 245, 249, ${alpha})`
                : `rgba(254, 232, 196, ${alpha})`;
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // ─── 2. Engraved 360° Orbital Sun Dial ───
  function buildSunDialTicks() {
    const frag = document.createDocumentFragment();
    const ns = 'http://www.w3.org/2000/svg';
    for (let deg = 0; deg < 360; deg += 5) {
      const rad = (deg * Math.PI) / 180;
      const isMajor = deg % 30 === 0;
      const r1 = 344;
      const r2 = isMajor ? 353 : 349;
      const line = document.createElementNS(ns, 'line');
      line.setAttribute('x1', (r1 * Math.sin(rad)).toFixed(2));
      line.setAttribute('y1', (r1 * Math.cos(rad)).toFixed(2));
      line.setAttribute('x2', (r2 * Math.sin(rad)).toFixed(2));
      line.setAttribute('y2', (r2 * Math.cos(rad)).toFixed(2));
      line.setAttribute('class', isMajor ? 'dial-tick major' : 'dial-tick');
      frag.appendChild(line);
    }
    dialTicksG.appendChild(frag);
  }

  function updateSunDialUI() {
    const hemi = state.poleMeta ? state.poleMeta.hemi : 1;
    const rad = (state.sunLonDeg * Math.PI) / 180;
    const r = 354;
    // Screen SVG +Y is downward (-Y_map): North 0°E is bottom (+r), South 0°E is top (-r)
    const x = r * Math.sin(rad);
    const y = hemi * r * Math.cos(rad);
    sunHandle.setAttribute('transform', `translate(${x.toFixed(2)}, ${y.toFixed(2)})`);

    const norm = ((state.sunLonDeg + 540) % 360) - 180;
    const absDeg = Math.round(Math.abs(norm));
    const dir = absDeg === 0 || absDeg === 180 ? '°' : norm > 0 ? '°E' : '°W';
    const labelText = `${absDeg}${dir}`;
    sunAzLabel.textContent = labelText;
    if (panelSunAz) panelSunAz.textContent = labelText;
    if (rngAzimuth) rngAzimuth.value = String(Math.round(norm));

    if (x < -20) {
      sunAzLabel.setAttribute('x', '-14');
      sunAzLabel.setAttribute('text-anchor', 'end');
    } else {
      sunAzLabel.setAttribute('x', '14');
      sunAzLabel.setAttribute('text-anchor', 'start');
    }
  }

  function updateScaleBar() {
    if (!scaleLabel || !scaleLine) return;
    const discW = moonDisc.clientWidth || 620;
    const pxPerKm = (discW * state.zoom) / 608.0;
    const steps = [200, 100, 50, 25, 10];
    let chosen = 100;
    for (const km of steps) {
      const px = km * pxPerKm;
      if (px <= 118 && px >= 44) {
        chosen = km;
        break;
      }
    }
    scaleLabel.textContent = `${chosen} KM`;
    scaleLine.style.width = `${Math.round(chosen * pxPerKm)}px`;
  }

  // ─── 3. WebGL2 Shader Setup & Texture Loader ───
  let gl = null;
  let prog = null;
  let uniforms = {};
  let demTex = null;
  let sciTex = null;

  function compileShader(type, src) {
    const sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(sh) || 'Shader compile error');
    }
    return sh;
  }

  function initWebGL() {
    gl = glCanvas.getContext('webgl2', {
      antialias: true,
      alpha: true,
      premultipliedAlpha: false,
      preserveDrawingBuffer: true,
    });
    if (!gl) throw new Error('WebGL2 unavailable');

    const vs = compileShader(gl.VERTEX_SHADER, VERT_SRC);
    const fs = compileShader(gl.FRAGMENT_SHADER, FRAG_SRC);
    prog = gl.createProgram();
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(prog) || 'Program link error');
    }
    gl.useProgram(prog);

    const quad = new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]);
    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, quad, gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'a_pos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    [
      'u_demTex', 'u_sciTex', 'u_resolution', 'u_zoom', 'u_pan',
      'u_hemi', 'u_elevOffset', 'u_elevSpan',
      'u_sunLonRad', 'u_subLatRad', 'u_modeWeights'
    ].forEach((name) => {
      uniforms[name] = gl.getUniformLocation(prog, name);
    });
  }

  function createTexture(img, filterMode) {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filterMode);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filterMode);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return tex;
  }

  function extractPixels(img) {
    const c = document.createElement('canvas');
    c.width = img.naturalWidth;
    c.height = img.naturalHeight;
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(img, 0, 0);
    return ctx.getImageData(0, 0, c.width, c.height).data;
  }

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }

  function ensurePoleLoaded(poleKey) {
    if (poleCache[poleKey]) return Promise.resolve(poleCache[poleKey]);
    if (polePromises[poleKey]) return polePromises[poleKey];

    const pMeta = state.atlasMeta.poles[poleKey];
    polePromises[poleKey] = Promise.all([
      loadImage(pMeta.assets.dem_2k),
      loadImage(pMeta.assets.science_1k),
    ]).then(([demImg, sciImg]) => {
      const pack = {
        demTex: createTexture(demImg, gl.LINEAR),
        sciTex: createTexture(sciImg, gl.LINEAR),
        cpuDem: extractPixels(demImg),
        cpuSci: extractPixels(sciImg),
      };
      poleCache[poleKey] = pack;
      return pack;
    });
    return polePromises[poleKey];
  }

  // ─── 4. Crisp Vector Moon Overlay (Graticule, IAU Craters, 5 Landmark Pins) ───
  function renderMoonOverlay() {
    if (!state.atlasMeta || !state.poleMeta) return;
    const ns = 'http://www.w3.org/2000/svg';
    overlaySvg.innerHTML = '';

    const half = state.atlasMeta.half_extent_m;
    const toSvg = (x_m, y_m) => {
      const u = (x_m + half) / (2 * half);
      const v = (half - y_m) / (2 * half);
      return {
        x: ((u - 0.5 - state.pan.x) * state.zoom + 0.5) * 1000,
        y: ((v - 0.5 - state.pan.y) * state.zoom + 0.5) * 1000,
      };
    };

    // 85° graticule circle + 90° spin-axis crosshair
    const pole = toSvg(0, 0);
    const rho85 = 2 * state.atlasMeta.radius_moon_m * Math.tan((2.5 * Math.PI) / 180);
    const r85Svg = (rho85 / (2 * half)) * state.zoom * 1000;

    const ring85 = document.createElementNS(ns, 'circle');
    ring85.setAttribute('cx', pole.x.toFixed(1));
    ring85.setAttribute('cy', pole.y.toFixed(1));
    ring85.setAttribute('r', r85Svg.toFixed(1));
    ring85.setAttribute('class', 'graticule-ring');
    overlaySvg.appendChild(ring85);

    const cross1 = document.createElementNS(ns, 'line');
    cross1.setAttribute('x1', (pole.x - 7).toFixed(1));
    cross1.setAttribute('y1', pole.y.toFixed(1));
    cross1.setAttribute('x2', (pole.x + 7).toFixed(1));
    cross1.setAttribute('y2', pole.y.toFixed(1));
    cross1.setAttribute('class', 'pole-cross');
    overlaySvg.appendChild(cross1);

    const cross2 = document.createElementNS(ns, 'line');
    cross2.setAttribute('x1', pole.x.toFixed(1));
    cross2.setAttribute('y1', (pole.y - 7).toFixed(1));
    cross2.setAttribute('x2', pole.x.toFixed(1));
    cross2.setAttribute('y2', (pole.y + 7).toFixed(1));
    cross2.setAttribute('class', 'pole-cross');
    overlaySvg.appendChild(cross2);

    // Official IAU / USGS Gazetteer Major Craters
    state.poleMeta.major_craters.forEach((c) => {
      const p = toSvg(c.x_m, c.y_m);
      if (p.x < 60 || p.x > 940 || p.y < 60 || p.y > 940) return;
      const t = document.createElementNS(ns, 'text');
      t.setAttribute('x', p.x.toFixed(1));
      t.setAttribute('y', p.y.toFixed(1));
      t.setAttribute('class', 'crater-engraving');
      t.textContent = c.name;
      overlaySvg.appendChild(t);
    });

    // 5 Interactive Landmark Pins
    state.poleMeta.landmarks.forEach((lm, idx) => {
      const p = toSvg(lm.x_m, lm.y_m);
      if (p.x < 25 || p.x > 975 || p.y < 25 || p.y > 975) return;

      const g = document.createElementNS(ns, 'g');
      g.setAttribute('class', idx === state.activeLandmarkIdx ? 'lm-pin active' : 'lm-pin');
      g.setAttribute('transform', `translate(${p.x.toFixed(1)}, ${p.y.toFixed(1)})`);

      const halo = document.createElementNS(ns, 'circle');
      halo.setAttribute('class', 'pin-halo');
      halo.setAttribute('r', idx === state.activeLandmarkIdx ? '17' : '12');

      const core = document.createElementNS(ns, 'circle');
      core.setAttribute('class', 'pin-core');
      core.setAttribute('r', idx === state.activeLandmarkIdx ? '4.5' : '3.2');

      const num = document.createElementNS(ns, 'text');
      num.setAttribute('class', 'pin-num');
      // Slightly offset pin 01/02 labels in opposite directions when close near the South Pole
      const labelLeft = state.pole === 'south' && idx === 0;
      num.setAttribute('x', labelLeft ? '-16' : '16');
      num.setAttribute('y', '3.5');
      if (labelLeft) num.setAttribute('text-anchor', 'end');
      num.textContent = `0${lm.index}`;

      g.appendChild(halo);
      g.appendChild(core);
      g.appendChild(num);

      g.addEventListener('click', (e) => {
        e.stopPropagation();
        selectLandmark(idx, true);
      });
      overlaySvg.appendChild(g);
    });
  }

  // ─── 5. Telemetry, Landmarks, Modes & Dual-Pole Switching ───
  function formatLon(lon) {
    const a = Math.abs(lon);
    if (a < 0.05 || Math.abs(a - 180) < 0.05) return `${a.toFixed(1)}°`;
    return `${a.toFixed(1)}°${lon > 0 ? 'E' : 'W'}`;
  }

  function formatLat(lat) {
    return `${Math.abs(lat).toFixed(2)}°${lat >= 0 ? 'N' : 'S'}`;
  }

  function formatSignedM(val) {
    return `${val >= 0 ? '+' : ''}${val.toLocaleString('en-US')} m`;
  }

  function updateProbeAtUV(u, v) {
    if (!state.cpuDem || !state.cpuSci || !state.atlasMeta || !state.poleMeta) return;
    const half = state.atlasMeta.half_extent_m;
    const x_m = -half + u * (2 * half);
    const y_m = half - v * (2 * half);
    const rho = Math.hypot(x_m, y_m);
    if (rho > half) return;

    const hemi = state.poleMeta.hemi;
    const dlat = (2 * Math.atan(rho / (2 * state.atlasMeta.radius_moon_m)) * 180) / Math.PI;
    const lat = hemi * (90 - dlat);
    const lon = (Math.atan2(x_m, -hemi * y_m) * 180) / Math.PI;

    const c2 = Math.min(2047, Math.max(0, Math.floor(u * 2048)));
    const r2 = Math.min(2047, Math.max(0, Math.floor(v * 2048)));
    const i2 = (r2 * 2048 + c2) * 4;
    const elev = Math.round(
      (((state.cpuDem[i2] << 8) | state.cpuDem[i2 + 1]) / 65535) * state.poleMeta.elev_span_m +
      state.poleMeta.elev_offset_m
    );
    const sun = ((state.cpuDem[i2 + 2] / 255) * 100).toFixed(1);

    const c1 = Math.min(1023, Math.max(0, Math.floor(u * 1024)));
    const r1 = Math.min(1023, Math.max(0, Math.floor(v * 1024)));
    const i1 = (r1 * 1024 + c1) * 4;
    const temp = ((state.cpuSci[i1] / 255) * 200 + 20).toFixed(1);

    document.getElementById('ch-pos').textContent = `${formatLat(lat)} · ${formatLon(lon)}`;
    document.getElementById('ch-elev').textContent = formatSignedM(elev);
    document.getElementById('ch-sun').textContent = `${sun}%`;
    document.getElementById('ch-temp').textContent = `${temp} K`;
  }

  function selectLandmark(idx, switchLens = false) {
    if (!state.poleMeta) return;
    const list = state.poleMeta.landmarks;
    const n = list.length;
    state.activeLandmarkIdx = ((idx % n) + n) % n;
    const lm = list[state.activeLandmarkIdx];
    const isFr = state.lang === 'fr';

    document.querySelectorAll('.lm-tab').forEach((tab) => {
      tab.classList.toggle('active', Number(tab.dataset.idx) === state.activeLandmarkIdx);
    });
    document.getElementById('story-tag').textContent = isFr ? lm.tag_fr : lm.tag_en;
    document.getElementById('story-title').textContent = isFr ? lm.name_fr : lm.name_en;
    document.getElementById('story-desc').textContent = isFr ? lm.desc_fr : lm.desc_en;
    document.getElementById('sm-elev').textContent = formatSignedM(lm.elev_m);
    document.getElementById('sm-sun').textContent = `${lm.solar_pct.toFixed(1)}%`;
    document.getElementById('sm-temp').textContent = `${lm.temp_avg_k.toFixed(1)} K`;
    document.getElementById('story-coords').textContent = `${formatLat(lm.lat)} · ${formatLon(lm.lon)} · LOLA 297M GRID`;

    if (switchLens && lm.recommended_mode) {
      setMode(lm.recommended_mode);
    }
    renderMoonOverlay();
  }

  function setMode(mode) {
    const cleanMode = MODE_INDEX[mode] !== undefined ? mode : 'shadow';
    state.mode = cleanMode;
    state.targetWeights = [0, 0, 0];
    state.targetWeights[MODE_INDEX[cleanMode]] = 1;

    document.querySelectorAll('.lens-btn').forEach((b) => {
      b.classList.toggle('active', b.dataset.mode === cleanMode);
    });
  }

  function updatePoleCopyAndKPIs() {
    if (!state.poleMeta) return;
    const dict = I18N[state.lang] || I18N.en;
    const pDict = dict.poles[state.pole];
    const stats = state.poleMeta.stats;
    const coldC = Math.round(stats.coldest_temp_k - 273.15);

    document.getElementById('rail-eyebrow').textContent = pDict.eyebrow;
    document.getElementById('rail-title').textContent = pDict.title;
    document.getElementById('rail-subtitle').textContent = pDict.subtitle;
    document.getElementById('m-eyebrow').textContent = pDict.eyebrow;
    document.getElementById('m-title').textContent = pDict.title;
    document.getElementById('sun-horizon-lbl').textContent = pDict.sun_horizon;

    document.getElementById('stat-cold').textContent = `${stats.coldest_temp_k.toFixed(1)} K`;
    document.getElementById('stat-cold-lbl').textContent = state.lang === 'fr' ? `Min ${coldC} °C` : `${coldC}°C Min`;
    document.getElementById('stat-sun').textContent = `${stats.peak_solar_pct.toFixed(1)}%`;
    document.getElementById('stat-psr').textContent = `${stats.psr_area_km2.toLocaleString('en-US')} km²`;

    // Update Sun Dial North/South stereographic meridian orientation & CRS stamp
    if (state.poleMeta.hemi > 0) {
      cardinalTop.textContent = dict.far_side;
      cardinalBottom.textContent = dict.near_side;
    } else {
      cardinalTop.textContent = dict.near_side;
      cardinalBottom.textContent = dict.far_side;
    }
    if (crsStamp) {
      crsStamp.textContent = `${state.poleMeta.crs_short} · ${dict.scroll_zoom}`;
    }
  }

  async function switchPole(poleKey, isInitial = false) {
    if (!state.atlasMeta || !state.atlasMeta.poles[poleKey]) return;
    if (!isInitial && state.pole === poleKey && demTex && sciTex) return;

    const pack = await ensurePoleLoaded(poleKey);
    state.pole = poleKey;
    state.poleMeta = state.atlasMeta.poles[poleKey];
    demTex = pack.demTex;
    sciTex = pack.sciTex;
    state.cpuDem = pack.cpuDem;
    state.cpuSci = pack.cpuSci;

    state.subLatDeg = state.poleMeta.summer_subsolar_lat_deg;
    state.sunLonDeg = state.poleMeta.default_sun_lon_deg;
    state.targetZoom = 1.0;
    state.zoom = 1.0;
    state.targetPan = { x: 0, y: 0 };
    state.pan = { x: 0, y: 0 };
    btnResetZoom.classList.add('hidden');

    document.querySelectorAll('.pole-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.pole === poleKey);
    });

    updatePoleCopyAndKPIs();
    updateSunDialUI();
    updateScaleBar();
    updateProbeAtUV(0.5, 0.5);
    selectLandmark(0, false);
  }

  function applyLanguage(lang) {
    state.lang = lang;
    localStorage.setItem('sounny_lang', lang);
    document.documentElement.lang = lang;
    document.querySelectorAll('.lang-btn').forEach((b) => {
      b.classList.toggle('active', b.dataset.lang === lang);
    });
    const dict = I18N[lang] || I18N.en;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const k = el.getAttribute('data-i18n');
      if (dict[k]) el.textContent = dict[k];
    });
    updatePoleCopyAndKPIs();
    selectLandmark(state.activeLandmarkIdx, false);
  }

  // ─── 6. Interactive Sun Ring, Hemisphere Toggle, Cursor Telemetry, Pan & Zoom ───
  function bindInteractions() {
    let draggingSun = false;
    const updateSunFromPointer = (clientX, clientY) => {
      const hemi = state.poleMeta ? state.poleMeta.hemi : 1;
      const rect = sunDialSvg.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = clientX - cx;
      const dy = clientY - cy;
      state.sunLonDeg = (Math.atan2(dx, hemi * dy) * 180) / Math.PI;
      updateSunDialUI();
    };

    sunHandle.addEventListener('pointerdown', (e) => {
      draggingSun = true;
      state.orbitPlaying = false;
      syncPlayIcon();
      sunHandle.setPointerCapture(e.pointerId);
      updateSunFromPointer(e.clientX, e.clientY);
    });

    sunDialSvg.querySelector('.dial-track').addEventListener('pointerdown', (e) => {
      draggingSun = true;
      state.orbitPlaying = false;
      syncPlayIcon();
      updateSunFromPointer(e.clientX, e.clientY);
    });

    window.addEventListener('pointermove', (e) => {
      if (draggingSun) updateSunFromPointer(e.clientX, e.clientY);
    });
    window.addEventListener('pointerup', () => {
      draggingSun = false;
    });

    function syncPlayIcon() {
      document.querySelectorAll('.icon-play').forEach((el) => {
        el.classList.toggle('hidden-icon', state.orbitPlaying);
      });
      document.querySelectorAll('.icon-pause').forEach((el) => {
        el.classList.toggle('hidden-icon', !state.orbitPlaying);
      });
    }
    const toggleOrbit = () => {
      state.orbitPlaying = !state.orbitPlaying;
      syncPlayIcon();
    };
    if (btnPlaySun) btnPlaySun.addEventListener('click', toggleOrbit);
    if (btnPlaySunMobile) btnPlaySunMobile.addEventListener('click', toggleOrbit);

    if (rngAzimuth) {
      rngAzimuth.addEventListener('input', () => {
        state.orbitPlaying = false;
        syncPlayIcon();
        state.sunLonDeg = parseFloat(rngAzimuth.value);
        updateSunDialUI();
      });
    }

    document.querySelectorAll('.pole-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        switchPole(btn.dataset.pole);
      });
    });

    document.querySelectorAll('.lens-btn').forEach((btn) => {
      btn.addEventListener('click', () => setMode(btn.dataset.mode));
    });

    document.querySelectorAll('.lm-tab').forEach((tab) => {
      tab.addEventListener('click', () => {
        selectLandmark(Number(tab.dataset.idx), true);
      });
    });
    document.getElementById('prev-lm').addEventListener('click', () => {
      selectLandmark(state.activeLandmarkIdx - 1, true);
    });
    document.getElementById('next-lm').addEventListener('click', () => {
      selectLandmark(state.activeLandmarkIdx + 1, true);
    });

    document.querySelectorAll('.lang-btn').forEach((btn) => {
      btn.addEventListener('click', () => applyLanguage(btn.dataset.lang));
    });

    let panning = false;
    let lastPt = { x: 0, y: 0 };

    moonDisc.addEventListener('wheel', (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.16 : 1 / 1.16;
      state.targetZoom = Math.min(5.5, Math.max(1.0, state.targetZoom * factor));
      if (state.targetZoom <= 1.02) {
        state.targetZoom = 1.0;
        state.targetPan = { x: 0, y: 0 };
      }
      btnResetZoom.classList.toggle('hidden', state.targetZoom <= 1.02);
    }, { passive: false });

    moonDisc.addEventListener('pointerdown', (e) => {
      if (e.target.closest('.lm-pin')) return;
      panning = true;
      lastPt = { x: e.clientX, y: e.clientY };
      moonDisc.classList.add('dragging');
    });

    window.addEventListener('pointermove', (e) => {
      if (panning && state.targetZoom > 1.01) {
        const rect = moonDisc.getBoundingClientRect();
        const du = (e.clientX - lastPt.x) / (rect.width * state.zoom);
        const dv = (e.clientY - lastPt.y) / (rect.height * state.zoom);
        const maxPan = Math.max(0, 0.5 - 0.5 / state.targetZoom);
        state.targetPan.x = Math.min(maxPan, Math.max(-maxPan, state.targetPan.x - du));
        state.targetPan.y = Math.min(maxPan, Math.max(-maxPan, state.targetPan.y - dv));
        lastPt = { x: e.clientX, y: e.clientY };
      }
    });

    window.addEventListener('pointerup', () => {
      panning = false;
      moonDisc.classList.remove('dragging');
    });

    btnResetZoom.addEventListener('click', () => {
      state.targetZoom = 1.0;
      state.targetPan = { x: 0, y: 0 };
      btnResetZoom.classList.add('hidden');
    });

    moonDisc.addEventListener('pointermove', (e) => {
      if (!state.cpuDem || !state.cpuSci || !state.atlasMeta) return;
      const rect = moonDisc.getBoundingClientRect();
      const sx = (e.clientX - rect.left) / rect.width;
      const sy = (e.clientY - rect.top) / rect.height;
      const u = (sx - 0.5) / state.zoom + 0.5 + state.pan.x;
      const v = (sy - 0.5) / state.zoom + 0.5 + state.pan.y;
      updateProbeAtUV(u, v);
    });

    window.addEventListener('resize', () => {
      renderStarfield();
      resizeGL();
      updateScaleBar();
    });
  }

  // ─── 7. Render Loop ───
  function resizeGL() {
    if (!gl) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = moonDisc.getBoundingClientRect();
    const w = Math.max(2, Math.round(rect.width * dpr));
    const h = Math.max(2, Math.round(rect.height * dpr));
    if (glCanvas.width !== w || glCanvas.height !== h) {
      glCanvas.width = w;
      glCanvas.height = h;
      gl.viewport(0, 0, w, h);
    }
  }

  let lastTs = performance.now();
  function frame(ts) {
    const dt = Math.min(0.05, (ts - lastTs) / 1000);
    lastTs = ts;

    if (state.orbitPlaying) {
      state.sunLonDeg = ((state.sunLonDeg + dt * 22 + 540) % 360) - 180;
      updateSunDialUI();
    }

    const lerpK = 1 - Math.exp(-dt * 10);
    for (let i = 0; i < 3; i++) {
      state.weights[i] += (state.targetWeights[i] - state.weights[i]) * lerpK;
    }

    const prevZoom = state.zoom;
    const prevPanX = state.pan.x;
    const prevPanY = state.pan.y;
    state.zoom += (state.targetZoom - state.zoom) * lerpK;
    state.pan.x += (state.targetPan.x - state.pan.x) * lerpK;
    state.pan.y += (state.targetPan.y - state.pan.y) * lerpK;

    if (
      Math.abs(state.zoom - prevZoom) > 1e-4 ||
      Math.abs(state.pan.x - prevPanX) > 1e-5 ||
      Math.abs(state.pan.y - prevPanY) > 1e-5
    ) {
      renderMoonOverlay();
      updateScaleBar();
    }

    if (gl && demTex && sciTex && state.poleMeta) {
      resizeGL();
      gl.useProgram(prog);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, demTex);
      gl.uniform1i(uniforms.u_demTex, 0);

      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, sciTex);
      gl.uniform1i(uniforms.u_sciTex, 1);

      gl.uniform2f(uniforms.u_resolution, glCanvas.width, glCanvas.height);
      gl.uniform1f(uniforms.u_zoom, state.zoom);
      gl.uniform2f(uniforms.u_pan, state.pan.x, state.pan.y);
      gl.uniform1f(uniforms.u_hemi, state.poleMeta.hemi);
      gl.uniform1f(uniforms.u_elevOffset, state.poleMeta.elev_offset_m);
      gl.uniform1f(uniforms.u_elevSpan, state.poleMeta.elev_span_m);
      gl.uniform1f(uniforms.u_sunLonRad, (state.sunLonDeg * Math.PI) / 180);
      gl.uniform1f(uniforms.u_subLatRad, (state.subLatDeg * Math.PI) / 180);
      gl.uniform3f(
        uniforms.u_modeWeights,
        state.weights[0],
        state.weights[1],
        state.weights[2]
      );

      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    requestAnimationFrame(frame);
  }

  // ─── 8. Bootstrap ───
  async function boot() {
    renderStarfield();
    buildSunDialTicks();
    updateScaleBar();
    initWebGL();
    bindInteractions();

    state.atlasMeta = await fetch('assets/polar_atlas_meta.json').then((r) => r.json());

    // Boot with North Pole first for rapid initial paint, then warm South Pole cache in background
    await switchPole('north', true);
    applyLanguage(state.lang);
    requestAnimationFrame(frame);

    setTimeout(() => {
      loadingVeil.classList.add('done');
      setTimeout(() => {
        ensurePoleLoaded('south').catch(() => {});
      }, 350);
    }, 180);
  }

  boot().catch((err) => {
    console.error('Lunar Polar Atlas boot error:', err);
  });
})();
