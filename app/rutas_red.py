"""UniRed: lo que ve un usuario registrado (feed, perfil, red, empleos, mensajes)."""
import os
import uuid

from flask import (Blueprint, abort, flash, g, jsonify, redirect, render_template, request,
                   session, url_for)

import db
import red
from comun import UPLOADS, mudo, requiere_usuario

bp = Blueprint("red", __name__)

IMAGENES = {"jpg", "jpeg", "png", "gif", "webp"}
VIDEOS = {"mp4", "webm", "mov", "m4v"}


def yo_id():
    return session["uid"]


def guardar_archivo(archivo, permitidos):
    """Guarda un archivo subido con nombre aleatorio. Devuelve (nombre, tipo) o (None, error)."""
    if not archivo or not archivo.filename:
        return None, None
    ext = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
    if ext not in permitidos:
        return None, "Formato no permitido. Usa " + ", ".join(sorted(permitidos)) + "."
    nombre = f"{uuid.uuid4().hex}.{ext}"
    archivo.save(os.path.join(UPLOADS, nombre))
    return nombre, ("video" if ext in VIDEOS else "imagen")


def borrar_archivo(nombre):
    if nombre and "/" not in nombre and "\\" not in nombre:
        try:
            os.remove(os.path.join(UPLOADS, nombre))
        except OSError:
            pass


def volver(defecto="red.inicio", **kw):
    ref = request.referrer
    return redirect(ref if ref and ref.startswith(request.host_url) else url_for(defecto, **kw))


# ------------------------------------------------------------------ feed
@bp.route("/")
def inicio():
    if session.get("rol") == "admin":
        return redirect(url_for("admin.inicio"))
    if session.get("rol") != "usuario":
        return redirect(url_for("auth.entrar"))
    return _feed()


@requiere_usuario
def _feed():
    solo_red = request.args.get("ver") == "red"
    return render_template("red/inicio.html", posts=red.feed(yo_id(), solo_red), solo_red=solo_red,
                           sugeridos=mudo(red.sugerencias, yo_id(), 4),
                           demanda=mudo(red.habilidades_en_demanda))


@bp.post("/publicar")
@requiere_usuario
def publicar():
    texto = request.form.get("texto", "").strip()[:3000]
    media, tipo = guardar_archivo(request.files.get("archivo"), IMAGENES | VIDEOS)
    if media is None and tipo:  # error de formato
        flash(tipo, "danger")
        return redirect(url_for("red.inicio"))
    if not texto and not media:
        flash("Escribe algo o adjunta una foto o un video.", "warning")
        return redirect(url_for("red.inicio"))
    red.publicar(yo_id(), texto, media, tipo)
    flash("Publicado.", "success")
    return redirect(url_for("red.inicio"))


@bp.post("/p/<pid>/reaccion")
@requiere_usuario
def reaccionar(pid):
    tipo = request.form.get("tipo", "recomendar")
    if tipo not in red.REACCIONES:
        abort(400)
    r = red.reaccionar(yo_id(), pid, tipo)
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(r[0] if r else {"reacciones": [], "mia": []})
    return volver()


@bp.post("/p/<pid>/comentar")
@requiere_usuario
def comentar(pid):
    texto = request.form.get("texto", "").strip()[:1500]
    if texto:
        red.comentar(yo_id(), pid, texto)
    return redirect((request.referrer or url_for("red.inicio")).split("#")[0] + f"#post-{pid}")


@bp.post("/p/<pid>/eliminar")
@requiere_usuario
def eliminar_publicacion(pid):
    media = red.eliminar_publicacion(pid, yo_id())
    if media is False:
        flash("Solo puedes eliminar tus propias publicaciones.", "warning")
    else:
        borrar_archivo(media)
        flash("Publicación eliminada.", "success")
    return volver()


@bp.post("/k/<kid>/eliminar")
@requiere_usuario
def eliminar_comentario(kid):
    red.eliminar_comentario(kid, yo_id())
    return volver()


# ---------------------------------------------------------------- perfil
@bp.route("/in/<uid>")
@requiere_usuario
def perfil(uid):
    p = red.perfil(uid, yo_id())
    if not p:
        abort(404)
    camino = red.camino_hacia(yo_id(), uid) if uid != yo_id() else None
    return render_template("red/perfil.html", p=p, uid=uid, propio=uid == yo_id(), camino=camino,
                           posts=red.publicaciones_de(uid, yo_id()))


@bp.route("/perfil/editar", methods=["GET", "POST"])
@requiere_usuario
def perfil_editar():
    f, uid = request.form, yo_id()
    if request.method == "POST":
        accion = f.get("accion")
        if accion == "datos":
            try:
                anios = max(0, min(60, int(f.get("anios") or 0)))
            except ValueError:
                anios = 0
            red.actualizar_perfil(uid, f.get("nombre", "").strip()[:80] or session["nombre"],
                                  f.get("titular", "").strip()[:120], f.get("ciudad", "").strip()[:60],
                                  f.get("acerca", "").strip()[:2000], anios)
            session["nombre"] = f.get("nombre", "").strip()[:80] or session["nombre"]
            flash("Datos guardados.", "success")
        elif accion in ("foto", "portada"):
            nombre, err = guardar_archivo(request.files.get("archivo"), IMAGENES)
            if nombre:
                borrar_archivo(red.poner_foto(uid, accion, nombre))
                flash("Imagen actualizada.", "success")
            else:
                flash(err or "Elige una imagen.", "warning")
        elif accion == "estudio":
            if f.get("institucion", "").strip():
                red.agregar_estudio(uid, f["institucion"].strip()[:120], f.get("titulo", "").strip()[:120],
                                    f.get("area", "").strip()[:120], f.get("inicio", "").strip()[:4],
                                    f.get("fin", "").strip()[:4])
                flash("Estudio agregado.", "success")
        elif accion == "quitar_estudio":
            red.quitar_estudio(uid, f.get("id"))
        elif accion == "habilidad":
            nombre = (f.get("nueva", "").strip() or f.get("habilidad", "")).strip()[:40]
            if nombre:
                db.crear_habilidad(nombre)
                try:
                    nivel = max(1, min(5, int(f.get("nivel", 3))))
                except ValueError:
                    nivel = 3
                db.asignar_habilidad(uid, nombre, nivel)
                flash(f"Habilidad «{nombre}» agregada.", "success")
        elif accion == "quitar_habilidad":
            red.quitar_habilidad(uid, f.get("nombre"))
        elif accion == "trabajo":
            if f.get("empresa", "").strip():
                red.trabajo_actual(uid, f["empresa"].strip()[:80], f.get("cargo", "").strip()[:80])
                flash("Experiencia actualizada.", "success")
        elif accion == "quitar_trabajo":
            red.quitar_trabajo(uid)
        elif accion == "proyecto":
            if f.get("proyecto"):
                db.asignar_proyecto(uid, f["proyecto"])
                flash("Proyecto agregado a tu perfil.", "success")
        elif accion == "clave":
            from werkzeug.security import generate_password_hash
            if len(f.get("clave", "")) >= 8:
                red.cambiar_clave(uid, generate_password_hash(f["clave"]))
                flash("Contraseña cambiada.", "success")
            else:
                flash("La contraseña debe tener al menos 8 caracteres.", "warning")
        return redirect(url_for("red.perfil_editar") + "#" + (accion or ""))
    return render_template("red/perfil_editar.html", p=red.perfil(uid, uid),
                           habilidades=mudo(db.opciones, "Habilidad", "nombre", "nombre"),
                           empresas=mudo(db.opciones, "Empresa", "id", "nombre"),
                           proyectos=mudo(db.opciones, "Proyecto", "id", "nombre"),
                           instituciones=mudo(red.instituciones))


# ---------------------------------------------------------------- mi red
@bp.route("/red")
@requiere_usuario
def mi_red():
    return render_template("red/red.html", invitaciones=red.invitaciones(yo_id()),
                           enviadas=red.enviadas(yo_id()), contactos=red.contactos(yo_id()),
                           sugeridos=red.sugerencias(yo_id(), 12))


@bp.post("/red/<uid>/<accion>")
@requiere_usuario
def red_accion(uid, accion):
    if accion == "conectar":
        r = red.solicitar(yo_id(), uid)
        flash("Ahora están conectados." if r else "Solicitud enviada.", "success")
    elif accion in ("aceptar", "rechazar"):
        red.responder(yo_id(), uid, accion == "aceptar")
        flash("Solicitud aceptada: ya son contactos." if accion == "aceptar" else "Solicitud rechazada.",
              "success" if accion == "aceptar" else "info")
    elif accion == "cancelar":
        red.cancelar_solicitud(yo_id(), uid)
    elif accion == "desconectar":
        red.desconectar(yo_id(), uid)
        flash("Contacto eliminado.", "info")
    else:
        abort(404)
    return volver("red.mi_red")


# --------------------------------------------------------------- empleos
@bp.route("/empleos")
@requiere_usuario
def empleos():
    q = request.args.get("q", "").strip()
    return render_template("red/empleos.html", empleos=red.empleos(yo_id(), q), q=q,
                           postulaciones=red.mis_postulaciones(yo_id()),
                           mi_empresa=mudo(red.mi_empresa, yo_id()))


@bp.post("/empleos/<oid>/<accion>")
@requiere_usuario
def empleo_accion(oid, accion):
    if accion == "postular":
        r = db.postular(yo_id(), oid)
        flash("Postulación enviada. Estado: en revisión." if r else "Esta oferta ya no está abierta.",
              "success" if r else "warning")
    elif accion == "retirar":
        red.retirar_postulacion(yo_id(), oid)
        flash("Postulación retirada.", "info")
    else:
        abort(404)
    return volver("red.empleos")


@bp.route("/empresa/<eid>")
@requiere_usuario
def empresa(eid):
    e = red.empresa(eid, yo_id())
    if not e:
        abort(404)
    return render_template("red/empresa.html", e=e,
                           postulantes=red.postulantes(eid, yo_id()) if e["trabajo_aqui"] else [],
                           habilidades=mudo(db.opciones, "Habilidad", "nombre", "nombre"))


@bp.post("/empresa/<eid>/oferta")
@requiere_usuario
def empresa_oferta(eid):
    """Quien trabaja en la empresa puede publicar ofertas (PUBLICA + REQUIERE)."""
    mia = red.mi_empresa(yo_id())
    if not mia or mia["id"] != eid:
        abort(403)
    f = request.form
    if f.get("titulo", "").strip():
        try:
            salario = max(0, int(f.get("salario") or 0))
        except ValueError:
            salario = 0
        db.crear_oferta(eid, f["titulo"].strip()[:120], f.get("ubicacion", "").strip()[:60], salario,
                        f.getlist("habilidades"))
        flash("Oferta publicada.", "success")
    return redirect(url_for("red.empresa", eid=eid))


@bp.post("/empresa/<eid>/oferta/<oid>/<accion>")
@requiere_usuario
def oferta_gestion(eid, oid, accion):
    if accion in ("cerrar", "abrir"):
        red.cerrar_oferta(yo_id(), oid, accion == "abrir")
    elif accion == "estado":
        estado = request.form.get("estado")
        if estado in ("EN_REVISION", "ENTREVISTA", "SELECCIONADO", "DESCARTADO"):
            red.cambiar_estado_postulacion(yo_id(), oid, request.form.get("u"), estado)
    return redirect(url_for("red.empresa", eid=eid))


# -------------------------------------------------------------- mensajes
@bp.route("/mensajes")
@bp.route("/mensajes/<uid>")
@requiere_usuario
def mensajes(uid=None):
    mudo(red.limpiar_mensajes)
    hilo = []
    if uid:
        if not red.puede_escribir(yo_id(), uid):
            flash("Solo puedes escribirles a tus contactos.", "warning")
            return redirect(url_for("red.mensajes"))
        hilo = red.hilo(yo_id(), uid)  # primero: así queda marcado como leído
        g.yo_info = mudo(red.yo, yo_id())
        g.yo_info["notif"] = mudo(red.notificaciones_nuevas, yo_id())
    convs = red.conversaciones(yo_id())
    otro = next((c["u"] for c in convs if c["u"]["id"] == uid), None) if uid else None
    return render_template("red/mensajes.html", convs=convs, otro=otro, hilo=hilo,
                           horas=red.HORAS_MENSAJES)


def _msg_json(m):
    from datetime import timedelta, timezone
    dt = m["fecha"].to_native()
    local = dt.astimezone(timezone(timedelta(hours=-5)))
    return {"id": m["id"], "texto": m["texto"], "mio": m["mio"], "fecha": dt.isoformat(),
            "hora": local.strftime("%I:%M %p").lstrip("0")}


@bp.route("/api/mensajes/<uid>", methods=["GET", "POST"])
@requiere_usuario
def api_mensajes(uid):
    if request.method == "POST":
        texto = (request.form.get("texto") or "").strip()[:2000]
        if not texto:
            return jsonify({"error": "vacío"}), 400
        m = red.enviar(yo_id(), uid, texto)
        if not m:
            return jsonify({"error": "Solo puedes escribirles a tus contactos."}), 403
        return jsonify(_msg_json(m))
    desde = request.args.get("desde") or None
    return jsonify([_msg_json(m) for m in mudo(red.hilo, yo_id(), uid, desde)])


# -------------------------------------------------------- notificaciones
@bp.route("/notificaciones")
@requiere_usuario
def notificaciones():
    lista = red.notificaciones(yo_id())
    visto = g.yo_info.get("notif_visto")
    for n in lista:
        n["nueva"] = visto is None or (n["fecha"] is not None and n["fecha"].to_native() > visto.to_native())
    mudo(red.marcar_notificaciones, yo_id())
    g.yo_info["notif"] = 0
    return render_template("red/notificaciones.html", lista=lista, visto=visto)


# ---------------------------------------------------------------- buscar
@bp.route("/buscar")
@requiere_usuario
def buscar():
    q = request.args.get("q", "").strip()
    return render_template("red/buscar.html", q=q, r=red.buscar(q) if q else None)


@bp.route("/p/<pid>")
@requiere_usuario
def publicacion(pid):
    post = red.publicacion(pid, yo_id())
    if not post:
        abort(404)
    return render_template("red/publicacion.html", p=post)
