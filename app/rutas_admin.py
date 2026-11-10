"""Panel de administración: todo lo que pide el enunciado (CRUD, relaciones, consultas,
recomendaciones y analítica) más el explorador de la base de datos."""
import networkx as nx
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from neo4j.exceptions import ClientError, ConstraintError

import db
import red

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
def solo_admin():
    if session.get("rol") != "admin":
        return redirect(url_for("auth.entrar", siguiente=request.path))


COLORES = {"Usuario": "#4C78A8", "Empresa": "#F58518", "Habilidad": "#54A24B",
           "Proyecto": "#B279A2", "Oferta": "#E45756"}
PALETA = ["#4C78A8", "#F58518", "#54A24B", "#B279A2", "#E45756", "#72B7B2", "#9D755D"]


# ------------------------------------------------------------ utilidades
def usuarios():
    return db.opciones("Usuario", "id", "nombre")


def empresas():
    return db.opciones("Empresa", "id", "nombre")


def habilidades():
    return db.opciones("Habilidad", "nombre", "nombre")


def proyectos():
    return db.opciones("Proyecto", "id", "nombre")


def ofertas_abiertas():
    return [{"id": o["id"], "texto": f"{o['titulo']} — {o['empresa']}"}
            for o in db.listar_ofertas(solo_abiertas=True)]


def elegido(param, lista, indice=0):
    """Valor de ?param=... o, si no viene, el elemento `indice` de la lista."""
    v = request.args.get(param)
    if v:
        return v
    return lista[min(indice, len(lista) - 1)]["id"] if lista else None


def volver(endpoint, **kw):
    return redirect(request.referrer or url_for(endpoint, **kw))


# ------------------------------------------------------------------ inicio
@bp.route("/")
def inicio():
    us = usuarios()
    uid = elegido("u", us)
    nodos, aristas = {}, []
    if uid:
        for f in db.subgrafo_usuario(uid):
            nodos[f["s"]] = {"id": f["s"], "label": f["sn"], "group": f["sl"]}
            nodos[f["e"]] = {"id": f["e"], "label": f["en"], "group": f["el"]}
            aristas.append({"from": f["s"], "to": f["e"], "label": f["rel"]})
    return render_template("admin/inicio.html", usuarios=us, uid=uid,
                           grafo={"nodes": list(nodos.values()), "edges": aristas})


# --------------------------------------------------------------- usuarios
@bp.route("/usuarios")
def usuarios_lista():
    return render_template("admin/usuarios.html", filas=db.listar_usuarios())


@bp.post("/usuarios/crear")
def usuario_crear():
    f = request.form
    if not f.get("nombre") or not f.get("email"):
        flash("Nombre y correo son obligatorios.", "warning")
    else:
        try:
            db.crear_usuario(f["nombre"], f["email"], f.get("titular", ""),
                             f.get("ciudad", ""), int(f.get("anios") or 0))
            flash("Usuario creado.", "success")
        except ConstraintError:
            flash("Ya existe un usuario con ese correo.", "danger")
    return redirect(url_for("admin.usuarios_lista"))


@bp.route("/usuarios/<uid>")
def usuario_perfil(uid):
    p = db.perfil_usuario(uid)
    if not p or not p[0]["usuario"]:
        flash("Ese usuario no existe.", "warning")
        return redirect(url_for("admin.usuarios_lista"))
    p = p[0]
    p["habilidades"] = [h for h in p["habilidades"] if h["habilidad"]]
    return render_template("admin/perfil.html", p=p, uid=uid,
                           postulaciones=db.postulaciones_de(uid))


@bp.route("/usuarios/<uid>/editar", methods=["GET", "POST"])
def usuario_editar(uid):
    if request.method == "POST":
        f = request.form
        try:
            db.actualizar_usuario(uid, f["nombre"], f["email"], f.get("titular", ""),
                                  f.get("ciudad", ""), int(f.get("anios") or 0))
            flash("Usuario actualizado.", "success")
            return redirect(url_for("admin.usuario_perfil", uid=uid))
        except ConstraintError:
            flash("Ese correo ya lo usa otro usuario.", "danger")
    p = db.perfil_usuario(uid)
    if not p or not p[0]["usuario"]:
        return redirect(url_for("admin.usuarios_lista"))
    return render_template("admin/usuario_editar.html", u=p[0]["usuario"], uid=uid)


@bp.post("/usuarios/<uid>/eliminar")
def usuario_eliminar(uid):
    db.eliminar_usuario(uid)
    flash("Usuario eliminado junto con todas sus relaciones (DETACH DELETE).", "success")
    return redirect(url_for("admin.usuarios_lista"))


# -------------------------------------------------------------- relaciones
@bp.route("/relaciones")
def relaciones():
    return render_template("admin/relaciones.html", usuarios=usuarios(), empresas=empresas(),
                           habilidades=habilidades(), proyectos=proyectos())


@bp.post("/relaciones/conectar")
def rel_conectar():
    r = db.conectar_usuarios(request.form["a"], request.form["b"])
    if r and r[0]["creadas"]:
        flash("Conexión CONECTA_CON creada.", "success")
    else:
        flash("Ya estaban conectados (o es el mismo usuario).", "info")
    return redirect(url_for("admin.relaciones"))


@bp.post("/relaciones/habilidad")
def rel_habilidad():
    f = request.form
    db.asignar_habilidad(f["u"], f["h"], int(f.get("nivel", 3)))
    flash("Habilidad asignada (TIENE_HABILIDAD).", "success")
    return redirect(url_for("admin.relaciones"))


@bp.post("/habilidades/crear")
def habilidad_crear():
    nombre = request.form.get("nombre", "").strip()
    if nombre:
        db.crear_habilidad(nombre)
        flash(f"Habilidad «{nombre}» creada.", "success")
    return volver("admin.relaciones")


@bp.post("/relaciones/empresa")
def rel_empresa():
    f = request.form
    db.asignar_empresa(f["u"], f["e"], f.get("cargo", ""))
    flash("Usuario vinculado a la empresa (TRABAJA_EN).", "success")
    return redirect(url_for("admin.relaciones"))


@bp.post("/relaciones/proyecto")
def rel_proyecto():
    db.asignar_proyecto(request.form["u"], request.form["p"])
    flash("Participación registrada (PARTICIPA_EN).", "success")
    return redirect(url_for("admin.relaciones"))


@bp.post("/proyectos/crear")
def proyecto_crear():
    f = request.form
    if f.get("nombre"):
        db.crear_proyecto(f["nombre"], f.get("descripcion", ""), f.getlist("tecnologias"))
        flash("Proyecto creado.", "success")
    return redirect(url_for("admin.relaciones"))


# ------------------------------------------------------- empresas y ofertas
@bp.route("/empresas")
def empresas_lista():
    return render_template("admin/empresas.html", filas=db.listar_empresas())


@bp.post("/empresas/crear")
def empresa_crear():
    f = request.form
    if f.get("nombre"):
        db.crear_empresa(f["nombre"], f.get("sector", ""), f.get("ciudad", ""))
        flash("Empresa registrada.", "success")
    return redirect(url_for("admin.empresas_lista"))


@bp.route("/ofertas")
def ofertas():
    us = usuarios()
    uid = elegido("u", us)
    return render_template("admin/ofertas.html", filas=db.listar_ofertas(), empresas=empresas(),
                           habilidades=habilidades(), usuarios=us, uid=uid,
                           abiertas=ofertas_abiertas(),
                           postulaciones=db.postulaciones_de(uid) if uid else [])


@bp.post("/ofertas/crear")
def oferta_crear():
    f = request.form
    if f.get("titulo"):
        db.crear_oferta(f["e"], f["titulo"], f.get("ubicacion", ""),
                        int(f.get("salario") or 0), f.getlist("habilidades"))
        flash("Oferta publicada (PUBLICA + REQUIERE).", "success")
    return redirect(url_for("admin.ofertas"))


@bp.post("/ofertas/postular")
def oferta_postular():
    uid = request.form["u"]
    r = db.postular(uid, request.form["o"])
    if r:
        flash(f"Postulación registrada (POSTULA_A), estado: {r[0]['estado']}.", "success")
    else:
        flash("La oferta no está abierta.", "warning")
    return redirect(url_for("admin.ofertas", u=uid))


# ----------------------------------------------------------------- consultas
PREGUNTAS = {
    "1": "¿Qué usuarios tienen habilidades similares?",
    "2": "¿Qué contactos en común existen entre dos profesionales?",
    "3": "¿Cuál es la ruta más corta entre un usuario y una empresa?",
    "4": "¿Qué candidatos podrían recomendarse para una oferta?",
    "5": "¿Qué proyectos comparten tecnologías o miembros?",
    "6": "¿Qué habilidades son las más demandadas?",
}


@bp.route("/consultas")
def consultas():
    q = request.args.get("q", "1")
    us, ctx = usuarios(), {}
    if q == "1":
        ctx["u"] = elegido("u", us)
        ctx["filas"] = db.habilidades_similares(ctx["u"]) if ctx["u"] else []
    elif q == "2":
        ctx["a"], ctx["b"] = elegido("a", us, 0), elegido("b", us, 1)
        ctx["filas"] = db.contactos_comunes(ctx["a"], ctx["b"]) if us else []
    elif q == "3":
        es = empresas()
        ctx.update(empresas=es, u=elegido("u", us), e=elegido("e", es),
                   solo=request.args.get("solo") == "1")
        r = db.ruta_mas_corta(ctx["u"], ctx["e"], ctx["solo"]) if us and es else []
        if r:
            r = r[0]
            ctx["ruta"] = r
            ctx["grafo"] = {
                "nodes": [{"id": i, "label": n["nombre"], "group": n["etiqueta"]}
                          for i, n in enumerate(r["nodos"])],
                "edges": [{"from": i, "to": i + 1, "label": rel}
                          for i, rel in enumerate(r["relaciones"])]}
    elif q == "4":
        ab = ofertas_abiertas()
        ctx.update(abiertas=ab, o=elegido("o", ab))
        ctx["filas"] = db.candidatos_para_oferta(ctx["o"]) if ctx["o"] else []
    elif q == "5":
        ctx["filas"] = db.proyectos_relacionados()
    else:
        q = "6"
        ctx["filas"] = db.habilidades_demandadas()
    return render_template("admin/consultas.html", q=q, preguntas=PREGUNTAS, usuarios=us, **ctx)


# ----------------------------------------------------------- recomendaciones
@bp.route("/recomendaciones")
def recomendaciones():
    us = usuarios()
    uid = elegido("u", us)
    return render_template(
        "admin/recomendaciones.html", usuarios=us, uid=uid,
        contactos=db.sugerir_contactos(uid) if uid else [],
        empleos=db.sugerir_empleos(uid) if uid else [],
        colaboradores=db.sugerir_colaboradores(uid) if uid else [])


# ------------------------------------------------------------------ analítica
@bp.route("/analitica")
def analitica():
    aristas = db.aristas_usuarios()
    G = nx.Graph()
    nombres = {}
    for r in aristas:
        G.add_edge(r["a"], r["b"])
        nombres[r["a"]], nombres[r["b"]] = r["na"], r["nb"]

    # Influencia: centralidad de grado (Cypher) + PageRank (networkx)
    pr = nx.pagerank(G) if G.number_of_nodes() else {}
    influyentes = [{"usuario": g["nombre"], "conexiones": g["conexiones"],
                    "PageRank": round(pr.get(g["id"], 0), 3)}
                   for g in db.grado_usuarios()]
    influyentes.sort(key=lambda x: (x["conexiones"], x["PageRank"]), reverse=True)
    influyentes = influyentes[:10]

    # Habilidades demandadas y brecha demanda - profesionales
    demandadas = db.habilidades_demandadas()
    for h in demandadas:
        h["brecha"] = h["demanda"] - h["profesionales"]

    # Comunidades: modularidad voraz (no requiere el plugin GDS)
    comunidades, grafo = [], {"nodes": [], "edges": []}
    if G.number_of_nodes():
        cs = sorted(nx.community.greedy_modularity_communities(G), key=len, reverse=True)
        for i, c in enumerate(cs):
            color = PALETA[i % len(PALETA)]
            comunidades.append({"n": i + 1, "color": color,
                                "miembros": sorted(nombres[x] for x in c)})
            for x in c:
                grafo["nodes"].append({"id": x, "label": nombres[x], "value": G.degree(x),
                                       "color": color})
        grafo["edges"] = [{"from": a, "to": b} for a, b in G.edges()]

    return render_template("admin/analitica.html", influyentes=influyentes,
                           demandadas=demandadas, comunidades=comunidades, grafo=grafo)


# ------------------------------------------------------------ base de datos
EJEMPLOS = [
    ("Todo el grafo (100 relaciones)", "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 100"),
    ("Esquema (nodos y relaciones)", "CALL db.schema.visualization()"),
    ("Contactos de Ana Torres", "MATCH (:Usuario {nombre:'Ana Torres'})-[:CONECTA_CON]-(c:Usuario)\nRETURN c.nombre, c.titular"),
    ("Amigos de amigos (2 saltos)", "MATCH (:Usuario {id:'u1'})-[:CONECTA_CON*2]-(x:Usuario)\nRETURN DISTINCT x.nombre"),
    ("Ruta más corta a una empresa", "MATCH (u:Usuario {id:'u6'}), (e:Empresa {nombre:'CloudNine'}),\n      p = shortestPath((u)-[:CONECTA_CON|TRABAJA_EN|PARTICIPA_EN|POSTULA_A|PUBLICA|REQUIERE|TIENE_HABILIDAD|USA_TECNOLOGIA*..8]-(e))\nRETURN [n IN nodes(p) | coalesce(n.nombre, n.titulo)] AS camino"),
    ("Publicaciones con más reacciones", "MATCH (a:Usuario)-[:PUBLICO]->(p:Publicacion)\nRETURN a.nombre, left(p.texto, 60) AS texto,\n       COUNT { ()-[:REACCIONO]->(p) } AS reacciones\nORDER BY reacciones DESC LIMIT 10"),
    ("Compañeros de universidad", "MATCH (a:Usuario)-[:ESTUDIO_EN]->(i:Institucion)<-[:ESTUDIO_EN]-(b:Usuario)\nWHERE a.id < b.id\nRETURN i.nombre, a.nombre, b.nombre"),
    ("Restricciones e índices", "SHOW CONSTRAINTS"),
]


def _valor(v):
    """Convierte nodos, relaciones y caminos de Neo4j en texto legible para la tabla."""
    from neo4j.graph import Node, Path, Relationship
    if isinstance(v, Node):
        props = dict(v)
        props.pop("clave_hash", None)
        return {"tipo": "nodo", "etiqueta": ":".join(v.labels), "props": props}
    if isinstance(v, Relationship):
        return {"tipo": "rel", "etiqueta": v.type, "props": dict(v)}
    if isinstance(v, Path):
        return " → ".join(str(n.get("nombre") or n.get("titulo") or n.element_id) for n in v.nodes)
    if isinstance(v, list):
        return [_valor(x) for x in v]
    if hasattr(v, "iso_format"):
        return v.iso_format()[:19]
    return v


def _grafo_de(registros):
    """Si el resultado trae nodos/relaciones, también se dibuja."""
    from neo4j.graph import Node, Path, Relationship
    nodos, aristas = {}, {}

    def nodo(n):
        et = next(iter(n.labels), "?")
        nodos[n.element_id] = {"id": n.element_id, "group": et,
                               "label": str(n.get("nombre") or n.get("titulo") or (n.get("texto") or "")[:20] or et)}

    def visitar(v):
        if isinstance(v, Node):
            nodo(v)
        elif isinstance(v, Relationship):
            nodo(v.start_node), nodo(v.end_node)
            aristas[v.element_id] = {"from": v.start_node.element_id, "to": v.end_node.element_id,
                                     "label": v.type}
        elif isinstance(v, Path):
            for r in v.relationships:
                visitar(r)
        elif isinstance(v, list):
            for x in v:
                visitar(x)
    for r in registros:
        for v in r.values():
            visitar(v)
    return {"nodes": list(nodos.values()), "edges": list(aristas.values())} if nodos else None


@bp.route("/base", methods=["GET", "POST"])
def base_datos():
    consulta = request.form.get("cypher", "").strip() or request.args.get("cypher", "")
    resultado = None
    if consulta:
        try:
            cols, regs = db.run_lectura(consulta)
            resultado = {"cols": cols, "filas": [[_valor(r[c]) for c in cols] for r in regs],
                         "grafo": _grafo_de(regs)}
        except ClientError as ex:
            msg = ex.message or str(ex)
            if "write" in msg.lower() and "read" in msg.lower():
                msg = "La consola es de solo lectura: usa MATCH/RETURN. Los cambios se hacen desde la app."
            resultado = {"error": msg}
    filas = red.grafo_completo()
    nodos = {}
    for f in filas:
        nodos[f["s"]] = {"id": f["s"], "label": f["sn"], "group": f["sl"]}
        nodos[f["e"]] = {"id": f["e"], "label": f["en"], "group": f["el"]}
    return render_template("admin/base_datos.html", consulta=consulta, resultado=resultado,
                           ejemplos=EJEMPLOS, etiquetas=red.conteo_etiquetas(),
                           relaciones=red.conteo_relaciones(), esquema=red.esquema(),
                           restricciones=red.restricciones(),
                           grafo={"nodes": list(nodos.values()),
                                  "edges": [{"from": f["s"], "to": f["e"]} for f in filas]})


# --------------------------------------------------------------- moderación
@bp.route("/moderacion")
def moderacion():
    return render_template("admin/moderacion.html", posts=red.moderacion(), red_res=red.resumen_red())


@bp.post("/moderacion/publicacion/<pid>/eliminar")
def mod_eliminar_publicacion(pid):
    from rutas_red import borrar_archivo
    media = red.eliminar_publicacion(pid)
    borrar_archivo(media)
    flash("Publicación eliminada con sus comentarios y reacciones.", "success")
    return redirect(url_for("admin.moderacion"))


@bp.post("/moderacion/comentario/<kid>/eliminar")
def mod_eliminar_comentario(kid):
    red.eliminar_comentario(kid)
    flash("Comentario eliminado.", "success")
    return redirect(url_for("admin.moderacion"))


@bp.post("/mensajes/limpiar")
def limpiar_mensajes():
    n = red.limpiar_mensajes()
    flash(f"Limpieza ejecutada: {n} mensajes con más de 24 h borrados.", "success")
    return redirect(url_for("admin.moderacion"))
