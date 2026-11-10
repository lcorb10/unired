"""Capturas para el documento Word (Edge headless, no abre ventanas).

    app\\venv\\Scripts\\python docs\\capturas_doc.py <clave_admin>
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

B = "http://127.0.0.1:8000"
OUT = pathlib.Path(__file__).parent / "img"
OUT.mkdir(exist_ok=True)
ADMIN = sys.argv[1]
import os  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / "app" / ".env")
DEMO, NEO4J_CLAVE = os.environ["CLAVE_DEMO"], os.environ["NEO4J_PASSWORD"]
SIN_INTRO = "document.getElementById('carga')?.setAttribute('hidden','')"


def entrar(pg, email, clave):
    pg.goto(B + "/entrar")
    pg.fill("#email", email)
    pg.fill("#clave", clave)
    pg.click("button.btn-rojo")
    pg.wait_for_load_state("networkidle")
    pg.evaluate(SIN_INTRO)


def foto(pg, nombre, clip=None, full=False, espera=400):
    pg.wait_for_timeout(espera)
    pg.evaluate(SIN_INTRO)
    pg.screenshot(path=str(OUT / f"{nombre}.png"), clip=clip, full_page=full)
    print("ok", nombre)


with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge", headless=True)
    ctx = nav.new_context(viewport={"width": 1366, "height": 800}, device_scale_factor=1.5)
    pg = ctx.new_page()
    pg.goto(B + "/entrar")
    foto(pg, "app_entrar", espera=2600)
    entrar(pg, "sebastian@mail.com", DEMO)
    foto(pg, "app_feed")
    pg.goto(B + "/in/u20")
    foto(pg, "app_perfil", clip={"x": 100, "y": 60, "width": 1166, "height": 740})
    pg.goto(B + "/empleos")
    foto(pg, "app_empleos")
    pg.goto(B + "/mensajes/u20")
    foto(pg, "app_mensajes")
    pg.goto(B + "/red")
    foto(pg, "app_red")
    pg.goto(B + "/")
    pg.hover(".reaccionar .btn-reaccion")
    foto(pg, "app_reacciones", clip={"x": 230, "y": 160, "width": 760, "height": 420}, espera=800)
    pg.click("[data-cy-abrir]")
    foto(pg, "app_ver_cypher", espera=600)

    m = nav.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    mp = m.new_page()
    entrar(mp, "sebastian@mail.com", DEMO)
    foto(mp, "app_movil")

    a = nav.new_context(viewport={"width": 1366, "height": 800}, device_scale_factor=1.5)
    ap = a.new_page()
    entrar(ap, "admin@unired.co", ADMIN)
    ap.goto(B + "/admin/base")
    foto(ap, "admin_base", espera=4000)
    ap.fill("#consola textarea", "MATCH (u:Usuario {id:'u6'}), (e:Empresa {nombre:'CloudNine'}),\n      p = shortestPath((u)-[*..8]-(e))\nRETURN p")
    ap.click("#consola button.btn-rojo")
    ap.wait_for_load_state("networkidle")
    ap.wait_for_timeout(3500)
    ap.evaluate(SIN_INTRO + "; document.querySelector('.barra').style.position='static'")
    ap.locator("#consola").screenshot(path=str(OUT / "admin_consola.png"))
    print("ok admin_consola")
    for nombre, url, esp in [("admin_usuarios", "/admin/usuarios", 400), ("admin_consulta_ruta", "/admin/consultas?q=3", 2500),
                             ("admin_consulta_candidatos", "/admin/consultas?q=4", 400), ("admin_consulta_similares", "/admin/consultas?q=1", 400),
                             ("admin_analitica", "/admin/analitica", 2500), ("admin_recomendaciones", "/admin/recomendaciones?u=u14", 400),
                             ("admin_moderacion", "/admin/moderacion", 400)]:
        ap.goto(B + url)
        foto(ap, nombre, espera=esp)

    # Neo4j Browser (como Workbench)
    nb = nav.new_context(viewport={"width": 1366, "height": 800}, device_scale_factor=1.5)
    np_ = nb.new_page()
    np_.goto("http://localhost:7474/browser/")
    np_.wait_for_timeout(4000)
    foto(np_, "neo4j_conectar")
    try:
        np_.fill("input[data-testid='boltaddress']", "neo4j://localhost:7687")
    except Exception:
        pass
    np_.fill("input[data-testid='username']", "neo4j")
    np_.fill("input[data-testid='password']", NEO4J_CLAVE)
    np_.click("button[data-testid='connect']")
    np_.wait_for_timeout(5000)
    np_.evaluate("document.querySelectorAll('[data-testid=\"frame\"], .frame').length")
    for nombre, q in [("neo4j_esquema", "CALL db.schema.visualization()"),
                      ("neo4j_grafo", "MATCH (u:Usuario)-[r:CONECTA_CON]->(v:Usuario) RETURN u, r, v"),
                      ("neo4j_tabla", "MATCH (u:Usuario)-[:ESTUDIO_EN]->(i:Institucion {nombre:'Universidad del Norte'}) RETURN u.nombre, u.titular, i.nombre")]:
        ed = np_.locator(".monaco-editor textarea, [data-testid='activeEditor'] textarea").first
        ed.click()
        np_.keyboard.press("Control+A")
        np_.keyboard.type(q)
        np_.keyboard.press("Control+Enter")
        np_.wait_for_timeout(5000)
        foto(np_, nombre)
    nav.close()
