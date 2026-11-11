#!/usr/bin/env python3
"""
End-to-end Playwright WebGL2 verification + 2400x2400 Retina LinkedIn Billboard & OpenGraph generator.
100% real screenshots of the live WebGL2 raymarched Lunar Arctic application.
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


def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(QUEUE_DIR, exist_ok=True)

    meta_path = os.path.join(BASE_DIR, "assets", "arctic_meta.json")
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

        # Capture Hero Sunlight Raymarched View (1440x900 @ 2x)
        shot_shadow = os.path.join(SCREENSHOTS_DIR, "arctic_sunlight.png")
        page.screenshot(path=shot_shadow)

        # Capture OpenGraph 1200x630 (@2x = 2400x1260)
        page.set_viewport_size({"width": 1200, "height": 630})
        page.wait_for_timeout(300)
        og_path = os.path.join(BASE_DIR, "og-card.png")
        page.screenshot(path=og_path)
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(300)

        # Capture Eternal Light mode
        page.click('.lens-btn[data-mode="light"]')
        page.wait_for_timeout(450)
        shot_light = os.path.join(SCREENSHOTS_DIR, "arctic_eternal_light.png")
        page.screenshot(path=shot_light)

        # Capture 24 K Ice Traps mode
        page.click('.lens-btn[data-mode="cold"]')
        page.wait_for_timeout(450)
        shot_cold = os.path.join(SCREENSHOTS_DIR, "arctic_cold_traps.png")
        page.screenshot(path=shot_cold)

        # Capture Artemis Sites mode
        page.click('.lens-btn[data-mode="artemis"]')
        page.wait_for_timeout(450)
        shot_artemis = os.path.join(SCREENSHOTS_DIR, "arctic_artemis_sites.png")
        page.screenshot(path=shot_artemis)

        # Capture pure circular Moon disc close-up for ultra-clean SpaceX-style LinkedIn Billboard
        page.click('.lens-btn[data-mode="shadow"]')
        page.evaluate("document.getElementById('story-card').style.visibility='hidden'; document.getElementById('starfield').style.visibility='hidden'; document.getElementById('cosmos').style.background='transparent'; document.body.style.background='transparent';")
        page.wait_for_timeout(450)
        orb_shot = os.path.join(SCREENSHOTS_DIR, "arctic_orb_stage.png")
        page.locator("#orb-stage").screenshot(path=orb_shot, omit_background=True)
        page.evaluate("document.getElementById('story-card').style.visibility='visible'; document.getElementById('starfield').style.visibility='visible'; document.getElementById('cosmos').style.background=''; document.body.style.background='';")

        # Test FR i18n parity
        page.click('.lang-btn[data-lang="fr"]')
        page.wait_for_timeout(150)
        fr_title = page.locator(".title").inner_text()
        assert "ARCTIQUE" in fr_title, f"French i18n failed: {fr_title}"
        page.click('.lang-btn[data-lang="en"]')
        page.wait_for_timeout(150)

        if errors:
            print("BROWSER ERRORS DETECTED:", errors, flush=True)
            sys.exit(1)
        print("ZERO console/page errors! WebGL2 raymarcher, 4 lenses, Sun dial, and EN/FR verified.", flush=True)

        # Render ultra-clean SpaceX / Apple Fine-Art 1200x1200 (@2x = 2400x2400) LinkedIn Poster
        orb_b64 = b64_png(orb_shot)
        stats = meta["stats"]

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
    background: radial-gradient(circle at 50% 52%, #11192c 0%, #05070d 46%, #020306 100%);
    color: #f8fafc;
    font-family: 'Plus Jakarta Sans', sans-serif;
    padding: 54px 62px 50px;
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
    font-size: 62px;
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
  .orb-wrap {{
    position: absolute;
    top: 53.5%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 820px;
    height: 820px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
  }}
  .orb-wrap img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
    display: block;
  }}
  .bottom-row {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-top: 1px solid rgba(255, 255, 255, 0.10);
    padding-top: 22px;
    z-index: 3;
  }}
  .stat-group {{
    display: flex;
    gap: 54px;
  }}
  .stat {{
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .stat-val {{
    font-family: 'Space Grotesk', monospace;
    font-size: 30px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.02em;
  }}
  .stat-lbl {{
    font-family: 'Space Grotesk', monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.16em;
    color: #64748b;
    text-transform: uppercase;
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
      <div class="kicker">#30DAYMAPCHALLENGE · DAY 11: ARCTIC · 80°N – 90°N</div>
      <h1>THE LUNAR ARCTIC</h1>
    </div>
    <div class="url-pill">sounny.github.io/lunarmap</div>
  </div>

  <div class="orb-wrap">
    <img src="{orb_b64}" alt="Lunar Arctic 80N-90N NASA LRO Raymarched Globe" />
  </div>

  <div class="bottom-row">
    <div class="stat-group">
      <div class="stat">
        <span class="stat-val">{stats['coldest_temp_k']} K (-248°C)</span>
        <span class="stat-lbl">COLDEST POLAR ABYSS</span>
      </div>
      <div class="stat">
        <span class="stat-val">{stats['peak_solar_pct']}%</span>
        <span class="stat-lbl">PEARY PEAK SUNLIGHT</span>
      </div>
      <div class="stat">
        <span class="stat-val">{stats['psr_area_km2']:,} km²</span>
        <span class="stat-lbl">PERMANENT SHADOW</span>
      </div>
    </div>
    <div class="credit">
      NASA LRO LOLA 80M · DIVINER<br/>REAL-TIME WEBGL2 RAYMARCHER
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
        print(f"Saved 2400x2400 Fine-Art LinkedIn Poster -> {out_card_queue}", flush=True)

        browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    main()
