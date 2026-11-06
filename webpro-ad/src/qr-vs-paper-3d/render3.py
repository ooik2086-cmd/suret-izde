"""Render ad3/scene.html frame by frame.  usage: render3.py <dir> <outdir> (--prev t1 t2 ... | --full SECONDS FPS)"""
import sys, os, json, threading, functools, http.server, time
from playwright.sync_api import sync_playwright

D = os.path.abspath(sys.argv[1]); OUT = os.path.abspath(sys.argv[2]); os.makedirs(OUT, exist_ok=True)
TIM = {"B": 3.0, "C": 7.8, "D": 10.45, "E": 14.5, "F": 19.8, "G": 22.4, "G2": 25.2, "END": 33}

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory=D))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/scene.html"

with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.on("console", lambda m: m.type in ("error", "warning") and print("console:", m.text))
    pg.on("pageerror", lambda e: print("pageerror:", e))
    pg.add_init_script(f"window.TIM={json.dumps(TIM)};")
    pg.goto(url); pg.wait_for_function("window.__ready===true", timeout=120000)
    if sys.argv[3] == "--prev":
        for t in sys.argv[4:]:
            pg.evaluate(f"seek({float(t)})"); pg.screenshot(path=f"{OUT}/p_{t}.png")
    else:
        sec, fps = float(sys.argv[4]), int(sys.argv[5]); n = int(sec * fps); t0 = time.time()
        a0 = int(sys.argv[6]) if len(sys.argv) > 6 else 0; a1 = int(sys.argv[7]) if len(sys.argv) > 7 else n
        for i in range(a0, min(a1, n)):
            pg.evaluate(f"seek({i/fps})"); pg.screenshot(path=f"{OUT}/f{i:04d}.jpg", type="jpeg", quality=90)
            if i % 100 == 0: print(i, round(time.time() - t0, 1), flush=True)
    b.close()
