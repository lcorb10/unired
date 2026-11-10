"""Servidor de producción de UniRed (waitress). Es el que se publica con el túnel.

    python servidor.py        -> http://127.0.0.1:8000
"""
import os

from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

from app import app, iniciar_limpiador

# Detrás de Cloudflare Tunnel: respeta https y el dominio público.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

if __name__ == "__main__":
    puerto = int(os.getenv("PUERTO", "8000"))
    iniciar_limpiador()
    print(f"UniRed en http://127.0.0.1:{puerto}")
    serve(app, host="127.0.0.1", port=puerto, threads=12, max_request_body_size=90 * 1024 * 1024)
