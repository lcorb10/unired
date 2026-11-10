"""Graba las escenas «anim» (escenas/escena.html) sincronizadas con la narración.

    python grabar_anim.py [escena ...]          -> clips/<escena>.mp4
    python grabar_anim.py --vista [escena ...]  -> capturas de cada paso en vista/ (sin voz, tiempos de prueba)
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from grabadora import ESCALA, VIEW, Grabadora, tiempos  # noqa: E402
from plan import ESCENAS  # noqa: E402

HTML = (AQUI / "escenas" / "escena.html").as_uri()
vista = "--vista" in sys.argv
pedidas = [a for a in sys.argv[1:] if not a.startswith("--")]
(AQUI / "clips").mkdir(exist_ok=True)
(AQUI / "vista").mkdir(exist_ok=True)

with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge", headless=True, args=["--allow-file-access-from-files"])
    for e in ESCENAS:
        if e["tipo"] != "anim" or (pedidas and e["id"] not in pedidas):
            continue
        ctx = nav.new_context(viewport=VIEW, device_scale_factor=ESCALA)
        pg = ctx.new_page()
        if vista:
            n = len(e["lineas"])
            T = [i * 2.5 for i in range(n)]
            pg.goto(f"{HTML}?id={e['id']}&t={','.join(map(str, T))}")
            for i in range(n):
                pg.wait_for_timeout(2400)
                pg.screenshot(path=str(AQUI / "vista" / f"{e['id']}_{i}.png"))
            print("vista", e["id"])
        else:
            T, dur = tiempos(e)
            pg.goto(f"{HTML}?id={e['id']}&esperar=1&t={','.join(f'{t:.2f}' for t in T)}")
            pg.wait_for_timeout(800)
            g = Grabadora(pg, AQUI / "clips" / f"{e['id']}.mp4")
            g.iniciar()
            pg.evaluate("window.empezar()")
            g.terminar(dur)
        ctx.close()
    nav.close()
