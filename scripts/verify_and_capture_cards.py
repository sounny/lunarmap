#!/usr/bin/env python3
"""
End-to-end Playwright WebGL2 verification + Dual-Pole 2400x2400 Retina LinkedIn Poster & OpenGraph generator.
Verifies both North Pole (80N-90N) and South Pole (80S-90S), 3 empirical lenses, zero Artemis legend items, and EN/FR i18n.
"""
import base64
import functools
import http.server
import json
import os
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_DIR = os.path.join(os.path.dirname(BASE_DIR), "social_media_queue")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def start_server(root_dir):
    handler = functools.partial(QuietHandler, directory=root_dir)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def b64_png(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def capture_transparent_orb(page, out_path):
    page.evaluate("""
      document.getElementById('studio-rail').style.visibility='hidden';
      document.querySelector('.utility-bar').style.visibility='hidden';
      document.querySelector('.carto-stamp').style.visibility='hidden';
      document.getElementById('starfield').style.visibility='hidden';
      document.getElementById('cosmos').style.background='transparent';
      document.documentElement.style.background='transparent';
      document.body.style.background='transparent';
    """)
    page.wait_for_timeout(400)
    page.locator("#orb-stage").screenshot(path=out_path, omit_background=True)
    page.evaluate("""
      document.getElementById('studio-rail').style.visibility='visible';
      document.querySelector('.utility-bar').style.visibility='visible';
      document.querySelector('.carto-stamp').style.visibility='visible';
      document.getElementById('starfield').style.visibility='visible';
      document.getElementById('cosmos').style.background='';
      document.documentElement.style.background='';
      document.body.style.background='';
    """)


def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(QUEUE_DIR, exist_ok=True)

    # Remove legacy Artemis screenshot if present
    old_artemis = os.path.join(SCREENSHOTS_DIR, "arctic_artemis_sites.png")
    if os.path.exists(old_artemis):
        os.remove(old_artemis)

    meta_path = os.path.join(BASE_DIR, "assets", "polar_atlas_meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    httpd, port = start_server(BASE_DIR)
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"Serving {BASE_DIR} at {url}", flush=True)

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = ctx.new_page()
        page.on("pageerror", lambda err: errors.append(f"PAGEERROR: {err}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE_ERR: {msg.text}") if msg.type == "error" else None)

        page.goto(url, wait_until="networkidle")
        page.wait_for_function("document.getElementById('loading-veil').classList.contains('done')", timeout=20000)
        page.wait_for_timeout(500)

        # Assert zero Artemis Sites / Outpost Sites in legend
        lens_texts = page.locator("#studio-rail .lens-btn").all_inner_texts()
        assert len(lens_texts) == 3, f"Expected 3 lenses, found {len(lens_texts)}: {lens_texts}"
        for lt in lens_texts:
            assert "Artemis" not in lt and "Outpost" not in lt, f"Forbidden lens label: {lt}"

        # Verify North Pole boot telemetry
        probe_pos = page.locator("#ch-pos").inner_text()
        assert "90.00°N" in probe_pos and "--" not in probe_pos, f"North probe check failed: {probe_pos}"
        assert "24.7 K" in page.locator("#stat-cold").inner_text()
        assert "180° FAR SIDE" in (page.locator("#cardinal-top").text_content() or "")
        assert "0° EARTH" in (page.locator("#cardinal-bottom").text_content() or "")

        # 1. Capture North Pole Sunlight Hero (1440x900 @ 2x)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "arctic_sunlight.png"))

        # Capture OpenGraph 1200x630 (@2x = 2400x1260)
        page.set_viewport_size({"width": 1200, "height": 630})
        page.wait_for_timeout(250)
        page.screenshot(path=os.path.join(BASE_DIR, "og-card.png"))
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(250)

        # Capture North transparent orb for Dual-Pole Poster
        orb_north = os.path.join(SCREENSHOTS_DIR, "orb_north_tmp.png")
        capture_transparent_orb(page, orb_north)

        # 2. Capture Peak Sunlight (North)
        page.click('#studio-rail .lens-btn[data-mode="light"]')
        page.wait_for_timeout(450)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "arctic_eternal_light.png"))

        # 3. Switch to South Pole (80°S - 90°S) & verify live telemetry + meridian flip
        page.click('#studio-rail .pole-btn[data-pole="south"]')
        page.wait_for_function("document.getElementById('stat-cold').innerText.includes('25.5 K')", timeout=15000)
        page.wait_for_timeout(500)

        probe_south = page.locator("#ch-pos").inner_text()
        assert "90.00°S" in probe_south, f"South probe check failed: {probe_south}"
        assert "0° EARTH" in (page.locator("#cardinal-top").text_content() or "")
        assert "180° FAR SIDE" in (page.locator("#cardinal-bottom").text_content() or "")
        assert "IAU_2015:30135" in page.locator("#crs-stamp").inner_text()

        # Capture South Pole Sunlight Hero (Mons Malapert + Shackleton shadows)
        page.click('#studio-rail .lens-btn[data-mode="shadow"]')
        page.wait_for_timeout(450)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "antarctic_sunlight.png"))

        orb_south = os.path.join(SCREENSHOTS_DIR, "orb_south_tmp.png")
        capture_transparent_orb(page, orb_south)

        # 4. Capture South Pole Cold Traps (Haworth 26.3 K / South 25.5 K Cold Traps)
        page.click('#studio-rail .lm-tab[data-idx="2"]')
        page.wait_for_timeout(450)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "arctic_cold_traps.png"))

        # Verify Laptop 1280x720 (zero vertical overflow in studio-rail) & Mobile 390x844
        page.set_viewport_size({"width": 1280, "height": 720})
        page.wait_for_timeout(250)
        rail_overflow = page.evaluate("""() => {
          const r = document.getElementById('studio-rail');
          return r.scrollHeight - r.clientHeight;
        }""")
        assert rail_overflow <= 2, f"Laptop 1280x720 rail overflowed by {rail_overflow}px"

        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(250)
        page.click('.mobile-topbar .pole-btn[data-pole="north"]')
        page.wait_for_timeout(250)
        assert "NORTH" in page.locator("#m-title").inner_text()
        page.click('.mobile-dock .lens-btn[data-mode="light"]')
        page.wait_for_timeout(200)
        page.click('.mobile-dock .lens-btn[data-mode="shadow"]')

        # Restore Desktop 1440x900 & verify French i18n parity across both poles
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(250)
        page.click('.utility-bar .lang-btn[data-lang="fr"]')
        page.wait_for_timeout(150)
        assert "NORD" in page.locator("#rail-title").inner_text()
        page.click('#studio-rail .pole-btn[data-pole="south"]')
        page.wait_for_timeout(200)
        assert "SUD" in page.locator("#rail-title").inner_text()
        page.click('.utility-bar .lang-btn[data-lang="en"]')
        page.click('#studio-rail .pole-btn[data-pole="north"]')
        page.wait_for_timeout(200)

        if errors:
            print("BROWSER ERRORS DETECTED:", errors, flush=True)
            sys.exit(1)
        print("ZERO console/page errors! Dual-Pole WebGL2 raymarcher, 3 lenses, Sun dial, and EN/FR verified.", flush=True)

        # Render 1200x1200 (@2x = 2400x2400) Dual-Pole LinkedIn Poster
        north_b64 = b64_png(orb_north)
        south_b64 = b64_png(orb_south)
        sn = meta["poles"]["north"]["stats"]
        ss = meta["poles"]["south"]["stats"]
        cn = round(sn["coldest_temp_k"] - 273.15)
        cs = round(ss["coldest_temp_k"] - 273.15)

        poster_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=Plus+Jakarta+Sans:wght@700;800&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1200px;
    height: 1200px;
    background: radial-gradient(circle at 50% 48%, #10182b 0%, #05080f 52%, #020306 100%);
    color: #f8fafc;
    font-family: 'Plus Jakarta Sans', sans-serif;
    padding: 54px 58px 48px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
  }}
  .top-row {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    z-index: 3;
  }}
  .kicker {{
    font-family: 'Space Grotesk', monospace;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.24em;
    color: #94a3b8;
    text-transform: uppercase;
    margin-bottom: 10px;
  }}
  h1 {{
    font-size: 58px;
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 0.98;
    color: #ffffff;
  }}
  .url-pill {{
    font-family: 'Space Grotesk', monospace;
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: #e2e8f0;
    padding: 9px 18px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.16);
  }}
  .poles-stage {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: center;
    margin: auto 0;
    z-index: 2;
  }}
  .pole-card {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
  }}
  .pole-badge {{
    font-family: 'Space Grotesk', monospace;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.20em;
    color: #cbd5e1;
    text-transform: uppercase;
    padding: 5px 14px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.11);
  }}
  .orb-img {{
    width: 530px;
    height: 530px;
    object-fit: contain;
    display: block;
  }}
  .pole-stats {{
    display: flex;
    gap: 26px;
    padding-top: 4px;
  }}
  .p-stat {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
  }}
  .p-val {{
    font-family: 'Space Grotesk', monospace;
    font-size: 21px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.02em;
  }}
  .p-lbl {{
    font-family: 'Space Grotesk', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.14em;
    color: #64748b;
    text-transform: uppercase;
  }}
  .bottom-row {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-top: 1px solid rgba(255, 255, 255, 0.10);
    padding-top: 20px;
    z-index: 3;
  }}
  .foot-left {{
    font-family: 'Space Grotesk', monospace;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.14em;
    color: #94a3b8;
    text-transform: uppercase;
    line-height: 1.6;
  }}
  .credit {{
    font-family: 'Space Grotesk', monospace;
    font-size: 11.5px;
    font-weight: 500;
    letter-spacing: 0.14em;
    color: #94a3b8;
    text-transform: uppercase;
    text-align: right;
    line-height: 1.6;
  }}
</style>
</head>
<body>
  <div class="top-row">
    <div>
      <div class="kicker">NASA LRO DUAL-POLE ORBITAL ATLAS · 80°N - 90°N &amp; 80°S - 90°S</div>
      <h1>THE LUNAR POLES</h1>
    </div>
    <div class="url-pill">sounny.github.io/lunarmap</div>
  </div>

  <div class="poles-stage">
    <div class="pole-card">
      <div class="pole-badge">NORTH POLE · 80°N - 90°N</div>
      <img class="orb-img" src="{north_b64}" alt="Lunar North Pole Raymarched Globe" />
      <div class="pole-stats">
        <div class="p-stat">
          <span class="p-val">{sn['coldest_temp_k']} K ({cn}°C)</span>
          <span class="p-lbl">PEARY PSR MIN</span>
        </div>
        <div class="p-stat">
          <span class="p-val">{sn['peak_solar_pct']}%</span>
          <span class="p-lbl">WHIPPLE SUN</span>
        </div>
        <div class="p-stat">
          <span class="p-val">{sn['psr_area_km2']:,} km²</span>
          <span class="p-lbl">PERM. SHADOW</span>
        </div>
      </div>
    </div>

    <div class="pole-card">
      <div class="pole-badge">SOUTH POLE · 80°S - 90°S</div>
      <img class="orb-img" src="{south_b64}" alt="Lunar South Pole Raymarched Globe" />
      <div class="pole-stats">
        <div class="p-stat">
          <span class="p-val">{ss['coldest_temp_k']} K ({cs}°C)</span>
          <span class="p-lbl">SOUTH PSR MIN</span>
        </div>
        <div class="p-stat">
          <span class="p-val">{ss['peak_solar_pct']}%</span>
          <span class="p-lbl">CONNECTING RIDGE</span>
        </div>
        <div class="p-stat">
          <span class="p-val">{ss['psr_area_km2']:,} km²</span>
          <span class="p-lbl">PERM. SHADOW</span>
        </div>
      </div>
    </div>
  </div>

  <div class="bottom-row">
    <div class="foot-left">
      REAL-TIME 3D WEBGL2 HORIZON RAYMARCHER · ±1.54° GRAZING POLAR SUN<br/>SUNLIGHT · 18.6-YR PEAK ILLUMINATION · DIVINER CRYOGENIC ICE TRAPS
    </div>
    <div class="credit">
      NASA LRO LOLA (297M) · GSFC PGDA · UCLA DIVINER<br/>IAU_2015:30130 &amp; 30135 · JSMARS ECOSYSTEM
    </div>
  </div>
</body>
</html>"""

        poster_html_path = os.path.join(SCREENSHOTS_DIR, "render_poster.html")
        with open(poster_html_path, "w", encoding="utf-8") as f:
            f.write(poster_html)

        cpage = browser.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=2)
        cpage.goto(f"http://127.0.0.1:{port}/screenshots/render_poster.html", wait_until="networkidle")
        cpage.wait_for_timeout(400)

        out_card_queue = os.path.join(QUEUE_DIR, "2026-11-11_lunar_arctic_artemis_square_post.png")
        out_card_repo = os.path.join(SCREENSHOTS_DIR, "linkedin_billboard_2400.png")
        cpage.screenshot(path=out_card_queue)
        cpage.screenshot(path=out_card_repo)
        os.remove(poster_html_path)
        for tmp in (orb_north, orb_south):
            if os.path.exists(tmp):
                os.remove(tmp)
        print(f"Saved 2400x2400 Dual-Pole LinkedIn Poster -> {out_card_queue}", flush=True)

        browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    main()
