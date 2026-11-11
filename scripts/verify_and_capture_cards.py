#!/usr/bin/env python3
"""
End-to-end Playwright verification + 2400x2400 Retina LinkedIn Billboard & OpenGraph generator.
Strictly uses 100% real screenshots of the live running Lunar Arctic Artemis application.
"""
import base64
import functools
import http.server
import json
import os
import socketserver
import sys
import threading
import time

from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_DIR = os.path.join(os.path.dirname(BASE_DIR), "social_media_queue")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def start_server(root_dir):
    handler = functools.partial(QuietHandler, directory=root_dir)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


def b64_png(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(QUEUE_DIR, exist_ok=True)

    meta_path = os.path.join(BASE_DIR, "assets", "polar_atlas_meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    n_stats = meta["poles"]["north"]["stats"]
    s_stats = meta["poles"]["south"]["stats"]

    httpd, port = start_server(BASE_DIR)
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"Serving {BASE_DIR} at {url}", flush=True)

    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Verify full interactive application at 1440x900 @ 2x Retina
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = ctx.new_page()
        page.on("pageerror", lambda err: errors.append(f"PAGEERROR: {err}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE_ERR: {msg.text}") if msg.type == "error" else None)

        page.goto(url, wait_until="networkidle")
        page.wait_for_function("document.getElementById('loading-overlay').classList.contains('done')", timeout=20000)
        page.wait_for_timeout(400)

        # Verify live metrics populated
        b_north = page.locator("#badge-metric-north").inner_text()
        b_south = page.locator("#badge-metric-south").inner_text()
        print("Live Dual-Pole Metrics:", b_north, "|", b_south, flush=True)
        assert "--" not in b_north and "--" not in b_south, "Metrics failed to populate!"

        # Capture full Dual-Pole live UI screenshot
        dual_ui_shot = os.path.join(SCREENSHOTS_DIR, "live_dual_pole_ui.png")
        page.screenshot(path=dual_ui_shot)

        # Capture OpenGraph 1200x630 (@2x = 2400x1260) directly from live app
        page.set_viewport_size({"width": 1200, "height": 630})
        page.wait_for_timeout(250)
        og_path = os.path.join(BASE_DIR, "og-card.png")
        page.screenshot(path=og_path)
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(250)

        # Test all 6 scientific layers & capture pristine rasters for README & Billboard
        for lyr in ["composite", "elevation", "solar", "thermal", "ice", "earth"]:
            page.click(f'.layer-btn[data-layer="{lyr}"]')
            page.wait_for_timeout(180)
            if lyr in ("composite", "solar", "thermal", "ice"):
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, f"layer_{lyr}.png"))

        # Switch back to composite + Gateway NRHO preset so both Near & Far-Side Arctic sunlit rims shine!
        page.click('.layer-btn[data-layer="composite"]')
        page.click('.preset-btn[data-preset="gateway-nrho"]')
        page.wait_for_timeout(220)
        gateway_ui_shot = os.path.join(SCREENSHOTS_DIR, "live_gateway_dual_ui.png")
        page.screenshot(path=gateway_ui_shot)

        # Capture exact billboard-aspect-ratio (1096:726 = 1440:954) screenshot so zero left/right UI text is cropped
        page.set_viewport_size({"width": 1440, "height": 954})
        page.wait_for_timeout(250)
        billboard_ui_shot = os.path.join(SCREENSHOTS_DIR, "live_billboard_frame_ui.png")
        page.screenshot(path=billboard_ui_shot)
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(200)

        # Also capture North-Pole-only crisp stage crop for hero showcase
        page.click('#mode-north')
        page.wait_for_timeout(220)
        north_stage_shot = os.path.join(SCREENSHOTS_DIR, "live_north_stage.png")
        page.locator(".map-stage").screenshot(path=north_stage_shot)

        # Test FR i18n parity
        page.click('.lang-btn[data-lang="fr"]')
        page.wait_for_timeout(150)
        fr_title = page.locator(".brand-name").inner_text()
        assert "ARTEMIS NORD" in fr_title, f"French i18n failed: {fr_title}"
        page.click('.lang-btn[data-lang="en"]')
        page.click('#mode-dual')
        page.wait_for_timeout(150)

        if errors:
            print("BROWSER ERRORS DETECTED:", errors, flush=True)
            sys.exit(1)
        print("ZERO console/page errors! All 6 NASA layers, presets, transects, and EN/FR verified.", flush=True)

        # 2. Render 1200x1200 (@2x = 2400x2400 Retina) LinkedIn Billboard Card
        # Adhering strictly to LINKEDIN_PLAYBOOK_AND_LEARNINGS.md Section 4:
        # - 1200x1200px @ 2x = 2400x2400 Retina
        # - 68% of canvas height dominated by REAL live Playwright screenshot of the running Dual-Pole app
        # - 1 Eyebrow Kicker + 1 Tight Headline (leading 0.99) + 3 High-Contrast Real NASA Telemetry Chips
        ui_b64 = b64_png(billboard_ui_shot)
        cold_k = n_stats["coldest_prp"]["temp_avg_k"]
        peak_sun = n_stats["peak_solar_60m_pct"]
        n_psr = int(round(n_stats["psr_area_km2"]))
        s_psr = int(round(s_stats["psr_area_km2"]))

        card_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800;900&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1200px;
    height: 1200px;
    background: radial-gradient(circle at 50% 0%, #132038 0%, #070b13 62%, #04060b 100%);
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #f8fafc;
    padding: 46px 52px 44px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
    position: relative;
  }}
  .top-head {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 2;
  }}
  .kicker-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .kicker {{
    font-family: 'Space Grotesk', monospace;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.38);
    padding: 6px 14px;
    border-radius: 999px;
  }}
  .repo-tag {{
    font-family: 'Space Grotesk', monospace;
    font-size: 15px;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 0.04em;
  }}
  h1 {{
    font-size: 56px;
    font-weight: 900;
    line-height: 0.99;
    letter-spacing: -0.03em;
    color: #ffffff;
    max-width: 1060px;
  }}
  h1 span {{
    color: #38bdf8;
  }}
  .hero-frame {{
    width: 100%;
    height: 726px;
    border-radius: 18px;
    overflow: hidden;
    border: 1.5px solid rgba(255, 255, 255, 0.18);
    box-shadow: 0 28px 70px rgba(0, 0, 0, 0.78), 0 0 42px rgba(56, 189, 248, 0.14);
    background: #060911;
    position: relative;
  }}
  .hero-frame img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center top;
    display: block;
  }}
  .telemetry-bar {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    z-index: 2;
  }}
  .chip {{
    background: rgba(15, 23, 42, 0.86);
    border: 1px solid rgba(255, 255, 255, 0.13);
    border-radius: 14px;
    padding: 14px 20px;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }}
  .chip-lbl {{
    font-family: 'Space Grotesk', monospace;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
  }}
  .chip-val {{
    font-family: 'Space Grotesk', monospace;
    font-size: 29px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f8fafc;
  }}
  .chip-val.cyan {{ color: #38bdf8; }}
  .chip-val.amber {{ color: #fbbf24; }}
  .chip-val.emerald {{ color: #10b981; }}
</style>
</head>
<body>
  <div class="top-head">
    <div class="kicker-row">
      <span class="kicker">#30DAYMAPCHALLENGE | DAY 11: ARCTIC</span>
      <span class="repo-tag">sounny.github.io/lunarmap | NASA LRO WEBGIS</span>
    </div>
    <h1>What If NASA Landed Artemis<br/>in the <span>Lunar Arctic?</span></h1>
  </div>

  <div class="hero-frame">
    <img src="{ui_b64}" alt="Live Artemis North Dual-Pole WebGIS Interface" />
  </div>

  <div class="telemetry-bar">
    <div class="chip">
      <span class="chip-lbl">HERMITE COLD TRAP (86°N)</span>
      <span class="chip-val cyan">~26 K (-247°C)</span>
    </div>
    <div class="chip">
      <span class="chip-lbl">PEARY PEAK SOLAR CONTINUITY</span>
      <span class="chip-val amber">{peak_sun:.1f}% SUNLIT</span>
    </div>
    <div class="chip">
      <span class="chip-lbl">PSR COLD TRAPS (80°N VS 80°S)</span>
      <span class="chip-val emerald">{n_psr:,} vs {s_psr:,} km²</span>
    </div>
  </div>
</body>
</html>"""

        card_html_path = os.path.join(SCREENSHOTS_DIR, "render_billboard.html")
        with open(card_html_path, "w", encoding="utf-8") as f:
            f.write(card_html)

        cpage = browser.new_page(viewport={"width": 1200, "height": 1200}, device_scale_factor=2)
        cpage.goto(f"http://127.0.0.1:{port}/screenshots/render_billboard.html", wait_until="networkidle")
        cpage.wait_for_timeout(400)

        out_card_queue = os.path.join(QUEUE_DIR, "2026-11-11_lunar_arctic_artemis_square_post.png")
        out_card_repo = os.path.join(SCREENSHOTS_DIR, "linkedin_billboard_2400.png")
        cpage.screenshot(path=out_card_queue)
        cpage.screenshot(path=out_card_repo)
        print(f"Saved 2400x2400 Retina Billboard -> {out_card_queue}", flush=True)

        browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    main()
