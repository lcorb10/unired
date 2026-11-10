"""Carga el esquema y los datos de ejemplo en Neo4j.

Uso:  python cargar_datos.py            (carga esquema + datos; no duplica nada)
      python cargar_datos.py --reset    (borra TODO el grafo antes de cargar)

Además deja lista la parte de UniRed:
  * a cada usuario de ejemplo sin contraseña le pone la clave de demostración (CLAVE_DEMO)
  * crea o actualiza la cuenta de administrador (ADMIN_EMAIL / ADMIN_PASSWORD del .env)
"""
import os
import pathlib
import sys

from werkzeug.security import generate_password_hash

import db

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
ARCHIVOS = ("01_schema.cypher", "02_seed.cypher", "04_red_social.cypher")


def sentencias(archivo):
    texto = "\n".join(l for l in archivo.read_text(encoding="utf-8").splitlines()
                      if not l.strip().startswith("//"))
    return [s.strip() for s in texto.split(";") if s.strip()]


if __name__ == "__main__":
    if "--reset" in sys.argv:
        db.run("MATCH (n) DETACH DELETE n")
        print("Grafo vaciado.")
    for nombre in ARCHIVOS:
        for q in sentencias(SCRIPTS / nombre):
            db.run(q)
        print(f"OK  {nombre}")

    clave_demo = os.getenv("CLAVE_DEMO") or "cambia-esta-clave"
    n = db.run("""
        MATCH (u:Usuario) WHERE u.clave_hash IS NULL
        SET u.clave_hash = $clave_hash
        RETURN count(u) AS n""", clave_hash=generate_password_hash(clave_demo))[0]["n"]
    print(f"Usuarios de ejemplo con clave de demostración: {n}")

    email = os.getenv("ADMIN_EMAIL", "admin@unired.co").strip().lower()
    clave = os.getenv("ADMIN_PASSWORD", "")
    if clave:
        db.run("""
            MERGE (a:Admin {email:$email})
              ON CREATE SET a.id = 'admin-' + randomUUID(), a.nombre = 'Administrador'
            SET a.clave_hash = $clave_hash""", email=email, clave_hash=generate_password_hash(clave))
        print(f"Administrador listo: {email}")
    else:
        print("AVISO: define ADMIN_PASSWORD en app/.env para crear la cuenta de administrador.")
    print(db.resumen())
