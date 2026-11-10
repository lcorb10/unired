"""UniRed: red profesional sobre Neo4j (aplicación Flask).

    python app.py              -> desarrollo en http://localhost:5000
    python servidor.py         -> producción (waitress), es lo que se publica con el túnel
"""
import json
import os
import pathlib
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import (Blueprint, Flask, abort, flash, g, has_request_context, redirect,
                   render_template, request, send_from_directory, session, url_for)
from neo4j.exceptions import AuthError, ConstraintError, ServiceUnavailable
from werkzeug.security import check_password_hash, generate_password_hash

import db
import red
from comun import UPLOADS, mudo, requiere_usuario

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "dev-" + secrets.token_hex(16)
app.config.update(
    MAX_CONTENT_LENGTH=int(os.getenv("MAX_SUBIDA_MB", "80")) * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)
# El botón «Ver Cypher» se muestra a todos en modo demo; si no, solo al administrador.
MODO_DEMO = os.getenv("MODO_DEMO", "1") == "1"

COLORES = {"Usuario": "#C8102E", "Empresa": "#1F1F1F", "Habilidad": "#E0A800",
           "Proyecto": "#7A1A2C", "Oferta": "#E4572E", "Publicacion": "#4C78A8",
           "Comentario": "#72B7B2", "Institucion": "#54A24B", "Mensaje": "#9D755D",
           "Admin": "#888888"}
COLOMBIA = timezone(timedelta(hours=-5))


# ============================================================ «Ver Cypher»
def _guardar_cypher(texto, params):
    if has_request_context() and not g.get("cy_mute"):
        g.setdefault("cypher", []).append({"q": texto, "p": params})


db.on_cypher(_guardar_cypher)


def _resumir(lista, limite=2600):
    out, total = [], 0
    for c in lista:
        q = c["q"] if len(c["q"]) <= 700 else c["q"][:700] + " …"
        p = json.dumps(c["p"], ensure_ascii=False, default=str)
        p = p if len(p) <= 200 else p[:200] + " …"
        total += len(q) + len(p)
        if total > limite:
            out.append({"q": "// … (más consultas omitidas)", "p": "{}"})
            break
        out.append({"q": q, "p": p})
    return out


@app.after_request
def _cypher_de_accion(resp):
    # Las acciones (POST) redirigen: sus consultas se muestran en la página siguiente.
    if request.method == "POST" and g.get("cypher") and not request.path.startswith("/api/"):
        session["cy_prev"] = {"ruta": request.path, "consultas": _resumir(g.cypher)}
    return resp


# ============================================ caché de estáticos (versión por fecha)
@app.url_defaults
def _version_estaticos(endpoint, valores):
    if endpoint == "static" and "filename" in valores and "v" not in valores:
        f = pathlib.Path(app.static_folder) / valores["filename"]
        if f.is_file():
            valores["v"] = int(f.stat().st_mtime)


# ================================================================= CSRF
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


@app.before_request
def _verificar_csrf():
    g.cypher = []
    if request.method == "POST":
        enviado = request.form.get("csrf") or request.headers.get("X-CSRF")
        if not enviado or enviado != session.get("csrf"):
            abort(400, "La sesión expiró o el formulario no es válido. Recarga la página.")


# ========================================================== utilidades UI
def _a_nativo(dt):
    if dt is None:
        return None
    if hasattr(dt, "to_native"):
        dt = dt.to_native()
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if getattr(dt, "tzinfo", None) is None and isinstance(dt, datetime):
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@app.template_filter("hace")
def hace(dt):
    dt = _a_nativo(dt)
    if not isinstance(dt, datetime):
        return str(dt or "")
    s = (datetime.now(timezone.utc) - dt).total_seconds()
    if s < 60:
        return "ahora"
    if s < 3600:
        return f"{int(s // 60)} min"
    if s < 86400:
        return f"{int(s // 3600)} h"
    if s < 7 * 86400:
        return f"{int(s // 86400)} d"
    return dt.astimezone(COLOMBIA).strftime("%d/%m/%Y")


@app.template_filter("hora")
def hora(dt):
    dt = _a_nativo(dt)
    return dt.astimezone(COLOMBIA).strftime("%I:%M %p").lstrip("0") if isinstance(dt, datetime) else ""


@app.template_filter("iso")
def iso(dt):
    dt = _a_nativo(dt)
    return dt.isoformat() if isinstance(dt, datetime) else ""


@app.template_filter("iniciales")
def iniciales(nombre):
    partes = [p for p in (nombre or "?").split() if p]
    return "".join(p[0] for p in partes[:2]).upper()


_PALETA_AV = ["#C8102E", "#1E1E1E", "#7A1A2C", "#B07D00", "#4A4A4A", "#9E0B23"]


@app.template_filter("color_av")
def color_av(clave):
    return _PALETA_AV[sum(ord(c) for c in str(clave)) % len(_PALETA_AV)]


@app.template_filter("dinero")
def dinero(v):
    try:
        return "$" + f"{int(v):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


@app.template_filter("tojson_cy")
def tojson_cy(v):
    return json.dumps(v, ensure_ascii=False, default=str)


@app.context_processor
def _globales():
    ctx = {"colores": COLORES, "csrf_token": csrf_token, "reacciones_info": red.REACCIONES,
           "modo_demo": MODO_DEMO, "rol": session.get("rol")}
    ctx["cy_prev"] = session.pop("cy_prev", None) if request.method == "GET" else None
    if session.get("rol") == "usuario" and "yo_info" not in g:
        try:
            g.yo_info = mudo(red.yo, session["uid"])
            if g.yo_info:
                g.yo_info["notif"] = mudo(red.notificaciones_nuevas, session["uid"])
        except Exception:  # noqa: BLE001
            g.yo_info = None
    ctx["yo"] = g.get("yo_info")
    if session.get("rol") == "admin":
        try:
            ctx["resumen_global"] = mudo(db.resumen)
        except Exception:  # noqa: BLE001
            ctx["resumen_global"] = {}
    return ctx


@app.errorhandler(ServiceUnavailable)
@app.errorhandler(AuthError)
def _sin_conexion(ex):
    return render_template("error.html", uri=db.URI, detalle=str(ex)), 503


@app.errorhandler(413)
def _muy_grande(_ex):
    flash(f"El archivo supera el máximo de {app.config['MAX_CONTENT_LENGTH'] // 1048576} MB.", "danger")
    return redirect(request.referrer or url_for("red.inicio"))


@app.errorhandler(400)
def _mala_peticion(ex):
    return render_template("mensaje.html", titulo="No se pudo completar la acción",
                           texto=getattr(ex, "description", str(ex))), 400


@app.errorhandler(404)
def _no_existe(_ex):
    return render_template("mensaje.html", titulo="Esta página no existe",
                           texto="Revisa el enlace o vuelve al inicio."), 404


@app.route("/media/<path:nombre>")
def media(nombre):
    return send_from_directory(UPLOADS, nombre, conditional=True, max_age=86400)


# ===================================================== inicio de sesión
auth = Blueprint("auth", __name__)
_intentos = {}


def _bloqueado(ip):
    ahora = time.time()
    lista = [t for t in _intentos.get(ip, []) if ahora - t < 600]
    _intentos[ip] = lista
    return len(lista) >= 8


def _destino_seguro(url, defecto):
    return url if url and url.startswith("/") and not url.startswith("//") else defecto


@auth.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        ip = request.headers.get("CF-Connecting-IP") or request.remote_addr
        if _bloqueado(ip):
            flash("Demasiados intentos. Espera 10 minutos e inténtalo de nuevo.", "danger")
            return render_template("auth/entrar.html"), 429
        email = request.form.get("email", "").strip().lower()
        cuenta = red.cuenta_por_email(email)
        if cuenta and cuenta["clave_hash"] and check_password_hash(cuenta["clave_hash"],
                                                                   request.form.get("clave", "")):
            token = session.get("csrf")
            session.clear()
            session["csrf"] = token or secrets.token_urlsafe(24)
            session.permanent = True
            session.update(uid=cuenta["id"], rol=cuenta["rol"], nombre=cuenta["nombre"], intro=True)
            defecto = url_for("admin.inicio") if cuenta["rol"] == "admin" else url_for("red.inicio")
            return redirect(_destino_seguro(request.args.get("siguiente"), defecto))
        _intentos.setdefault(ip, []).append(time.time())
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("auth/entrar.html")


@auth.route("/registro", methods=["GET", "POST"])
def registro():
    f = request.form
    if request.method == "POST":
        nombre, email = f.get("nombre", "").strip(), f.get("email", "").strip().lower()
        clave = f.get("clave", "")
        if not nombre or "@" not in email:
            flash("Escribe tu nombre y un correo válido.", "warning")
        elif len(clave) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "warning")
        elif red.cuenta_por_email(email):
            flash("Ya existe una cuenta con ese correo. Inicia sesión.", "warning")
        else:
            try:
                uid = red.registrar(nombre[:80], email[:120], generate_password_hash(clave),
                                    f.get("titular", "").strip()[:120], f.get("ciudad", "").strip()[:60])
            except ConstraintError:
                flash("Ya existe una cuenta con ese correo.", "warning")
                return render_template("auth/registro.html", f=f)
            inst = f.get("institucion", "").strip()
            if inst:
                red.agregar_estudio(uid, inst[:120], f.get("programa", "").strip()[:120], "",
                                    f.get("inicio", "").strip()[:4], "")
            token = session.get("csrf")
            session.clear()
            session["csrf"] = token
            session.permanent = True
            session.update(uid=uid, rol="usuario", nombre=nombre, intro=True)
            flash("Bienvenido a UniRed. Completa tu perfil para recibir mejores recomendaciones.", "success")
            return redirect(url_for("red.perfil_editar"))
    return render_template("auth/registro.html", f=f, instituciones=red.instituciones())


@auth.post("/salir")
def salir():
    session.clear()
    return redirect(url_for("auth.entrar"))


# =========================================== limpieza de mensajes (24 h)
def _limpiador():
    while True:
        try:
            n = red.limpiar_mensajes()
            if n:
                app.logger.info("Mensajes vencidos borrados: %s", n)
        except Exception as ex:  # noqa: BLE001
            app.logger.warning("No se pudo limpiar mensajes: %s", ex)
        time.sleep(600)


def iniciar_limpiador():
    threading.Thread(target=_limpiador, daemon=True, name="limpiador-mensajes").start()


import rutas_admin  # noqa: E402
import rutas_red  # noqa: E402

app.register_blueprint(auth)
app.register_blueprint(rutas_red.bp)
app.register_blueprint(rutas_admin.bp)

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        iniciar_limpiador()
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1", host=os.getenv("HOST", "127.0.0.1"))
