"""Utilidades compartidas por app.py y las rutas (evita importaciones circulares)."""
import os
from functools import wraps

from flask import g, redirect, request, session, url_for

import red

UPLOADS = os.path.abspath(os.getenv("CARPETA_SUBIDAS", os.path.join(os.path.dirname(__file__), "uploads")))
os.makedirs(UPLOADS, exist_ok=True)


def mudo(fn, *a, **kw):
    """Ejecuta consultas de apoyo (menú, contadores) sin mostrarlas en «Ver Cypher»."""
    antes = g.get("cy_mute")
    g.cy_mute = True
    try:
        return fn(*a, **kw)
    finally:
        g.cy_mute = antes


def requiere_usuario(fn):
    @wraps(fn)
    def envoltura(*a, **kw):
        if session.get("rol") == "admin":
            return redirect(url_for("admin.inicio"))
        if session.get("rol") != "usuario":
            return redirect(url_for("auth.entrar", siguiente=request.path))
        if g.get("yo_info") is None:
            g.yo_info = mudo(red.yo, session["uid"])
            if not g.yo_info:  # la cuenta fue eliminada
                session.clear()
                return redirect(url_for("auth.entrar"))
            g.yo_info["notif"] = mudo(red.notificaciones_nuevas, session["uid"])
        return fn(*a, **kw)
    return envoltura
