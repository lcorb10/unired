"""Graba las escenas «app» del plan (app de UniRed y Neo4j Browser), sincronizadas con la narración.

    python grabar.py <clave_admin> [escena ...]
Al terminar deshace lo que se creó durante la grabación (reacción, comentario, invitación, postulación…).
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "app"))
from grabadora import Grabadora, desplazar, escribir, mover, nuevo_contexto, tiempos  # noqa: E402
from plan import ESCENAS  # noqa: E402

B = "http://127.0.0.1:8000"
import os
CLIPS = AQUI / os.getenv("CARPETA_CLIPS", "clips")
CLIPS.mkdir(exist_ok=True)
ADMIN = sys.argv[1]
import os  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
load_dotenv(pathlib.Path(__file__).resolve().parents[1] / "app" / ".env")
DEMO, NEO4J_CLAVE = os.environ["CLAVE_DEMO"], os.environ["NEO4J_PASSWORD"]
MARCA = "(video)"  # todo lo que se cree durante la grabación lleva esta marca para deshacerlo
SIN_INTRO = "document.getElementById('carga')?.setAttribute('hidden','')"


def entrar(pg, email, clave, despacio=False, saltar_intro=True):
    pg.goto(B + "/entrar")
    if despacio:
        escribir(pg, "#email", email, 45)
        escribir(pg, "#clave", clave, 60)
        mover(pg, "button.btn-rojo", clic=True, nav=True)
    else:
        pg.fill("#email", email)
        pg.fill("#clave", clave)
        pg.click("button.btn-rojo")
    pg.wait_for_load_state("domcontentloaded")
    if saltar_intro:
        pg.evaluate(SIN_INTRO)


# ------------------------------------------------------------------ escenas
def s06_browser(pg, g, T):
    pg.goto("http://localhost:7474/browser/")
    pg.wait_for_timeout(3500)
    for sel in ["[data-testid='dismissBanner']", "button[aria-label='Close']"]:
        try:
            pg.locator(sel).first.click(timeout=800)
        except Exception:
            pass
    g.iniciar()
    g.esperar_hasta(T[1])
    try:
        escribir(pg, "input[data-testid='boltaddress']", "neo4j://localhost:7687", 25)
    except Exception:
        pass
    escribir(pg, "input[data-testid='username']", "neo4j", 70)
    escribir(pg, "input[data-testid='password']", NEO4J_CLAVE, 50)
    mover(pg, "button[data-testid='connect']", clic=True)
    pg.wait_for_timeout(2500)
    pg.evaluate("[...document.querySelectorAll('div')].filter(d => d.textContent.startsWith('To help make Neo4j Browser') && d.children.length < 6).forEach(d => d.remove())")

    def consulta(q, ms=40):
        ed = pg.locator(".monaco-editor textarea, [data-testid='activeEditor'] textarea").first
        mover(pg, ".monaco-editor", clic=True)
        ed.focus()
        pg.keyboard.press("Control+A")
        pg.keyboard.press("Backspace")
        pg.keyboard.type(q, delay=ms)
        pg.wait_for_timeout(300)
        pg.keyboard.press("Control+Enter")
    g.esperar_hasta(T[2])
    consulta("CALL db.schema.visualization()")
    g.esperar_hasta(T[3])
    consulta("MATCH (u:Usuario)-[r:CONECTA_CON]->(v:Usuario) RETURN u, r, v", 30)
    pg.wait_for_timeout(3500)
    mover(pg, (900, 560), pasos=40)
    g.esperar_hasta(T[4])
    consulta("MATCH (u:Usuario)-[:ESTUDIO_EN]->(i:Institucion {nombre:'Universidad del Norte'}) RETURN u.nombre, u.titular", 25)
    pg.wait_for_timeout(2200)
    g.esperar_hasta(T[5])
    try:
        mover(pg, "[data-testid='navigationDBMS'], [aria-label='Database Information']", clic=True)
        pg.wait_for_timeout(1800)
        pg.wait_for_timeout(1200)
        mover(pg, pg.get_by_text("Usuario", exact=True).first.bounding_box() and (
            pg.get_by_text("Usuario", exact=True).first.bounding_box()["x"] + 30, pg.get_by_text("Usuario", exact=True).first.bounding_box()["y"] + 10), clic=True)
    except Exception as ex:
        print("   (panel lateral no encontrado)", ex)


def s08_feed(pg, g, T):
    pg.goto(B + "/entrar")
    g.iniciar()
    entrar(pg, "sebastian@mail.com", DEMO, despacio=True, saltar_intro=False)
    g.esperar_hasta(T[1])
    pg.evaluate(SIN_INTRO)
    for xy in [(170, 230), (720, 380), (1230, 260), (1230, 620)]:
        mover(pg, xy, pasos=34, pausa=700)
    g.esperar_hasta(T[2])
    post = pg.locator(".post").first
    mover(pg, ".post .reaccionar .btn-reaccion")
    pg.wait_for_timeout(1500)
    mover(pg, ".post .paleta button[data-tipo='encanta']", clic=True, pasos=12)
    pg.wait_for_timeout(1200)
    g.esperar_hasta(T[3])
    mover(pg, ".post .btn-comentar", clic=True)
    post.locator(".comentarios input[name=texto]").type(f"¡Me encantó cómo se arma el grafo! {MARCA}", delay=45)
    mover(pg, ".post .comentarios button.btn-rojo", clic=True, nav=True)
    pg.wait_for_load_state("domcontentloaded")
    g.esperar_hasta(T[4])
    pg.evaluate("scrollTo({top: 0, behavior: 'smooth'})")
    mover(pg, ".crear .abrir", clic=True)
    pg.wait_for_timeout(700)
    pg.locator("#modal-publicar textarea").type(f"Probando las publicaciones con foto en UniRed {MARCA}", delay=40)
    pg.set_input_files("#archivo-post", str(AQUI.parent / "flow" / "unired_cuadro_final.png"))
    pg.wait_for_timeout(1500)
    mover(pg, "#modal-publicar button.btn-rojo", clic=True, nav=True)
    pg.wait_for_load_state("domcontentloaded")
    g.esperar_hasta(T[5])
    mover(pg, "[data-cy-abrir]", clic=True)
    pg.wait_for_timeout(1500)
    mover(pg, (1150, 500), pasos=30)
    desplazar(pg, 500, ms=2500)


def s09_perfil(pg, g, T):
    entrar(pg, "sebastian@mail.com", DEMO)
    pg.goto(B + "/in/u16")
    g.iniciar()
    mover(pg, (500, 300), pasos=30)
    desplazar(pg, 700, ms=3500)
    g.esperar_hasta(T[1])
    pg.goto(B + "/perfil/editar")
    mover(pg, (520, 300), pasos=30)
    desplazar(pg, 900, ms=4000)
    g.esperar_hasta(T[2])
    pg.goto(B + "/in/u7")
    pg.wait_for_timeout(600)
    desplazar(pg, 330, ms=1200)
    mover(pg, ".camino", pasos=36)
    g.esperar_hasta(T[3])
    pg.goto(B + "/red")
    mover(pg, ".caja .persona button.btn-borde:has-text('Aceptar'), form[action*='/u18/aceptar'] button", clic=True, nav=True)
    pg.wait_for_load_state("domcontentloaded")
    g.esperar_hasta(T[4])
    desplazar(pg, 300, ms=1500)
    mover(pg, (520, 520), pasos=30)


def s10_empleos(pg, g, T):
    entrar(pg, "sebastian@mail.com", DEMO)
    pg.goto(B + "/empleos")
    g.iniciar()
    mover(pg, ".empleo .chip.si", pasos=30)
    pg.wait_for_timeout(800)
    mover(pg, ".empleo .ajuste", pasos=20)
    g.esperar_hasta(T[1])
    boton = "form[action*='/o2/postular'] button"
    mover(pg, boton, clic=True, nav=True)
    pg.wait_for_load_state("domcontentloaded")
    pg.wait_for_timeout(600)
    mover(pg, "#postulaciones", pasos=30)
    g.esperar_hasta(T[2])
    pg.goto(B + "/empresa/e6")
    desplazar(pg, 520, ms=2200)
    mover(pg, "input[name='titulo']", pasos=30)
    g.esperar_hasta(T[3])
    pg.goto(B + "/notificaciones")
    mover(pg, ".notif", pasos=30)
    desplazar(pg, 300, ms=1500)


def s11_mensajes(pg, g, T, nav):
    entrar(pg, "sebastian@mail.com", DEMO)
    otro = nuevo_contexto(nav)
    tp = otro.new_page()
    entrar(tp, "tomas@mail.com", DEMO)
    tp.goto(B + "/mensajes/u16")
    pg.goto(B + "/mensajes/u20")
    g.iniciar()
    mover(pg, "#form-msg textarea", clic=True)
    pg.keyboard.type(f"Tomás, ¿ya viste la oferta de Analista BI en AgroSmart? {MARCA}", delay=42)
    pg.wait_for_timeout(300)
    pg.keyboard.press("Enter")
    g.esperar_hasta(T[1])
    tp.locator("#form-msg textarea").type(f"¡Sí! Ya me postulé, gracias por avisarme {MARCA}", delay=10)
    tp.keyboard.press("Enter")
    pg.wait_for_timeout(3500)
    g.esperar_hasta(T[2])
    mover(pg, ".aviso-24", pasos=30)
    otro.close()


def s12_admin_base(pg, g, T):
    entrar(pg, "admin@unired.co", ADMIN)
    pg.goto(B + "/admin/base")
    pg.wait_for_timeout(500)
    pg.evaluate(SIN_INTRO)
    g.iniciar()
    mover(pg, ".admin-menu a.activo", pasos=30)
    g.esperar_hasta(T[1])
    mover(pg, ".card table", pasos=30, pausa=1500)
    mover(pg, (950, 420), pasos=30)
    g.esperar_hasta(T[2])
    mover(pg, "[data-ejemplo]:has-text('Ruta más corta')", clic=True)
    pg.wait_for_timeout(600)
    mover(pg, "#consola button.btn-rojo", clic=True, nav=True)
    pg.evaluate("document.getElementById('consola').scrollIntoView()")
    pg.wait_for_timeout(3000)
    escribir(pg, "#consola textarea", "MATCH (u:Usuario) DETACH DELETE u", 45)
    mover(pg, "#consola button.btn-rojo", clic=True, nav=True)
    pg.evaluate("document.getElementById('consola').scrollIntoView()")
    pg.evaluate(SIN_INTRO)
    mover(pg, ".alert-danger", pasos=20)
    g.esperar_hasta(T[3])
    pg.evaluate(SIN_INTRO)
    pg.evaluate("document.getElementById('g-todo').scrollIntoView({behavior:'smooth'})")
    pg.wait_for_timeout(1500)
    mover(pg, "#g-todo", pasos=30)
    b = pg.locator("#g-todo").bounding_box()
    pg.mouse.down()
    pg.mouse.move(b["x"] + b["width"] / 2 + 160, b["y"] + b["height"] / 2 + 60, steps=30)
    pg.mouse.up()


def s13_admin_crud(pg, g, T):
    pg.on("dialog", lambda d: d.accept())
    entrar(pg, "admin@unired.co", ADMIN)
    pg.goto(B + "/admin/usuarios")
    g.iniciar()
    escribir(pg, "input[name='nombre']", f"Elena Prado {MARCA}", 40)
    escribir(pg, "input[name='email']", "elena.video@mail.com", 30)
    escribir(pg, "input[name='titular']", "Ingeniera de Datos", 30)
    mover(pg, "form[action*='usuarios/crear'] button", clic=True, nav=True)
    pg.wait_for_load_state("domcontentloaded")
    g.esperar_hasta(T[1])
    fila = pg.locator("tr", has_text="Elena Prado")
    fila.scroll_into_view_if_needed()
    mover(pg, "tr:has-text('Elena Prado') button.btn-outline-danger", clic=True, nav=True)
    pg.wait_for_load_state("domcontentloaded")
    g.esperar_hasta(T[2])
    pg.goto(B + "/admin/relaciones")
    mover(pg, (700, 360), pasos=30, pausa=2000)
    pg.goto(B + "/admin/ofertas")
    mover(pg, (520, 330), pasos=30)


def s14_consultas(pg, g, T):
    entrar(pg, "admin@unired.co", ADMIN)
    pg.goto(B + "/admin/consultas?q=1")
    g.iniciar()
    mover(pg, ".list-group-item.active", pasos=30)
    g.esperar_hasta(T[1])
    mover(pg, "table", pasos=30)
    g.esperar_hasta(T[2])
    mover(pg, "[data-cy-abrir]", clic=True)
    pg.wait_for_timeout(1500)
    mover(pg, (1150, 420), pasos=24)
    desplazar(pg, 250, ms=1200)
    g.esperar_hasta(T[3] - 0.8)
    pg.goto(B + "/admin/consultas?q=2")
    g.esperar_hasta(T[4] - 0.8)
    pg.goto(B + "/admin/consultas?q=3&u=u16&e=e3")
    pg.wait_for_timeout(2500)
    mover(pg, ".alert-success", pasos=30)
    g.esperar_hasta(T[5] - 0.8)
    pg.goto(B + "/admin/consultas?q=4")
    mover(pg, "table", pasos=30)
    g.esperar_hasta(T[6] - 0.8)
    pg.goto(B + "/admin/consultas?q=5")
    pg.wait_for_timeout(3200)
    pg.goto(B + "/admin/consultas?q=6")
    pg.wait_for_timeout(800)
    desplazar(pg, 500, ms=2000)


def s15_analitica(pg, g, T):
    entrar(pg, "admin@unired.co", ADMIN)
    pg.goto(B + "/admin/recomendaciones?u=u14")
    g.iniciar()
    mover(pg, (600, 450), pasos=30, pausa=1500)
    mover(pg, (1100, 450), pasos=30)
    g.esperar_hasta(T[1])
    pg.goto(B + "/admin/analitica")
    pg.wait_for_timeout(1500)
    mover(pg, (600, 400), pasos=30, pausa=1800)
    mover(pg, (1150, 400), pasos=30)
    g.esperar_hasta(T[2])
    desplazar(pg, 900, ms=3000)
    mover(pg, (900, 520), pasos=30)


FUNCIONES = {k: v for k, v in globals().items() if k[:1] == "s" and k[1:3].isdigit()}


def deshacer():
    import db
    db.run(f"MATCH (k:Comentario) WHERE k.texto CONTAINS '{MARCA}' DETACH DELETE k")
    db.run(f"MATCH (m:Mensaje) WHERE m.texto CONTAINS '{MARCA}' DETACH DELETE m")
    db.run(f"MATCH (u:Usuario) WHERE u.nombre CONTAINS '{MARCA}' DETACH DELETE u")
    r = db.run(f"MATCH (:Usuario)-[:PUBLICO]->(p:Publicacion) WHERE p.texto CONTAINS '{MARCA}' "
               "WITH p, p.media AS media DETACH DELETE p RETURN media")
    for f in r:
        if f["media"]:
            (AQUI.parent / "app" / "uploads" / f["media"]).unlink(missing_ok=True)
    # reacción de Sebastián al video de Tomás vuelve a «celebrar» (estaba así antes)
    db.run("""MATCH (:Usuario {id:'u20'})-[:PUBLICO]->(p:Publicacion {tipo_media:'video'}), (s:Usuario {id:'u16'})
              MERGE (s)-[x:REACCIONO]->(p) SET x.tipo = 'celebrar'""")
    # invitación de Nicolás pendiente otra vez
    db.run("""MATCH (a:Usuario {id:'u18'})-[c:CONECTA_CON]-(b:Usuario {id:'u16'}) WHERE c.desde = date() DELETE c
              WITH 1 AS x MATCH (a:Usuario {id:'u18'}), (b:Usuario {id:'u16'})
              WHERE NOT (a)-[:CONECTA_CON]-(b) MERGE (a)-[s:SOLICITA_CONEXION]->(b) ON CREATE SET s.fecha = datetime() - duration({hours: 5})""")
    db.run("MATCH (:Usuario {id:'u16'})-[p:POSTULA_A]->(:Oferta {id:'o2'}) WHERE p.fecha = date() DELETE p")
    print("Cambios de la grabación deshechos.")


if __name__ == "__main__":
    pedidas = sys.argv[2:] or list(FUNCIONES)
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="msedge", headless=True)
        try:
            for e in ESCENAS:
                if e["id"] not in pedidas or e["id"] not in FUNCIONES:
                    continue
                T, dur = tiempos(e)
                print(f"{e['id']}: {dur:.1f}s", flush=True)
                ctx = nuevo_contexto(nav)
                pg = ctx.new_page()
                g = Grabadora(pg, CLIPS / f"{e['id']}.mp4")
                extra = (nav,) if e["id"] == "s11_mensajes" else ()
                FUNCIONES[e["id"]](pg, g, T + [dur], *extra)
                g.terminar(dur)
                ctx.close()
        finally:
            nav.close()
            deshacer()
