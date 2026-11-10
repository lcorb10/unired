"""Copia y restauración del grafo para la demo (reemplaza a cargar_datos.py --reset).

    python preparar_demo.py guardar      -> guarda TODO el grafo en demo_copia.json
    python preparar_demo.py restaurar    -> deja el grafo exactamente como en la copia

Uso: antes del ensayo ya está guardado el estado ideal (publicaciones con foto y video,
2 invitaciones pendientes para Sebastián). Después del ensayo se corre «restaurar» y todo
lo que se creó al ensayar desaparece. Los archivos subidos (uploads/) no se tocan.
"""
import datetime as dt
import json
import pathlib
import sys

from neo4j.time import Date, DateTime

import db

COPIA = pathlib.Path(__file__).resolve().parent / "demo_copia.json"
LOTE = 500


def _a_json(v):
    if isinstance(v, DateTime):
        return {"$dt": v.to_native().isoformat()}
    if isinstance(v, Date):
        return {"$d": v.to_native().isoformat()}
    if isinstance(v, list):
        return [_a_json(x) for x in v]
    return v


def _de_json(v):
    if isinstance(v, dict) and "$dt" in v:
        return dt.datetime.fromisoformat(v["$dt"])
    if isinstance(v, dict) and "$d" in v:
        return dt.date.fromisoformat(v["$d"])
    if isinstance(v, list):
        return [_de_json(x) for x in v]
    return v


def _q(nombre):
    return "`" + nombre.replace("`", "``") + "`"


def guardar():
    nodos = [{"k": r["k"], "labels": sorted(r["labels"]), "props": {a: _a_json(b) for a, b in r["props"].items()}}
             for r in db.run("MATCH (n) RETURN elementId(n) AS k, labels(n) AS labels, properties(n) AS props")]
    rels = [{"a": r["a"], "b": r["b"], "tipo": r["tipo"], "props": {x: _a_json(y) for x, y in r["props"].items()}}
            for r in db.run("MATCH (a)-[r]->(b) RETURN elementId(a) AS a, elementId(b) AS b, type(r) AS tipo, properties(r) AS props")]
    COPIA.write_text(json.dumps({"guardado": dt.datetime.now().isoformat(timespec="seconds"),
                                 "nodos": nodos, "relaciones": rels}, ensure_ascii=False), encoding="utf-8")
    print(f"Copia guardada: {len(nodos)} nodos y {len(rels)} relaciones -> {COPIA.name}")


def restaurar():
    if not COPIA.exists():
        sys.exit("No hay copia. Primero: python preparar_demo.py guardar")
    datos = json.loads(COPIA.read_text(encoding="utf-8"))
    db.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS")
    grupos = {}
    for n in datos["nodos"]:
        grupos.setdefault(tuple(n["labels"]), []).append({"k": n["k"], "props": {a: _de_json(b) for a, b in n["props"].items()}})
    for labels, filas in grupos.items():
        etiq = "".join(":" + _q(x) for x in labels) or ":_Sin"
        for i in range(0, len(filas), LOTE):
            db.run(f"UNWIND $filas AS f CREATE (n{etiq}) SET n = f.props, n._k = f.k", filas=filas[i:i + LOTE])
    db.run("CREATE INDEX demo_k IF NOT EXISTS FOR (n:_Tmp) ON (n._k)")
    db.run("MATCH (n) SET n:_Tmp")
    db.run("CALL db.awaitIndexes(30)")
    tipos = {}
    for r in datos["relaciones"]:
        tipos.setdefault(r["tipo"], []).append({"a": r["a"], "b": r["b"], "props": {x: _de_json(y) for x, y in r["props"].items()}})
    for tipo, filas in tipos.items():
        for i in range(0, len(filas), LOTE):
            db.run(f"""UNWIND $filas AS f
                       MATCH (a:_Tmp {{_k: f.a}}), (b:_Tmp {{_k: f.b}})
                       CREATE (a)-[r:{_q(tipo)}]->(b) SET r = f.props""", filas=filas[i:i + LOTE])
    db.run("MATCH (n:_Tmp) REMOVE n._k, n:_Tmp")
    db.run("DROP INDEX demo_k IF EXISTS")
    n = db.run("MATCH (n) RETURN count(n) AS c")[0]["c"]
    r = db.run("MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
    print(f"Restaurado a la copia del {datos['guardado']}: {n} nodos y {r} relaciones.")


if __name__ == "__main__":
    {"guardar": guardar, "restaurar": restaurar}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
