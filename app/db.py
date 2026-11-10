"""Capa de acceso a Neo4j para la Red Profesional.

Todas las consultas Cypher de la aplicación viven aquí, parametrizadas
(nunca se concatena texto del usuario dentro de la consulta).
"""
import os
import pathlib
import textwrap
import uuid

from dotenv import load_dotenv
from neo4j import READ_ACCESS, GraphDatabase, unit_of_work

# Lee app/.env (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) si existe.
load_dotenv(pathlib.Path(__file__).resolve().parent / ".env")

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")

_driver = None


def driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD),
                                       notifications_min_severity="OFF")
    return _driver


# ---- Registro de las consultas para el panel «Ver Cypher» ----------------
_OCULTAR = ("clave", "hash", "password")
_oyentes = []


def on_cypher(fn):
    """Registra una función que recibe (consulta, parámetros) por cada ejecución."""
    _oyentes.append(fn)


def _avisar(query, params):
    if not _oyentes:
        return
    limpio = {k: ("•••" if any(o in k.lower() for o in _OCULTAR) else v)
              for k, v in params.items()}
    texto = textwrap.dedent(query).strip("\n")
    for fn in _oyentes:
        fn(texto, limpio)


def run(query, **params):
    """Ejecuta una consulta y devuelve una lista de diccionarios."""
    _avisar(query, params)
    with driver().session() as s:
        return [r.data() for r in s.run(query, **params)]


@unit_of_work(timeout=8)
def _leer(tx, query):
    res = tx.run(query)
    filas = []
    for i, r in enumerate(res):
        if i >= 300:
            break
        filas.append(r)
    return list(res.keys()), filas


def run_lectura(query):
    """Consola del administrador: SOLO lectura (Neo4j rechaza CREATE/SET/DELETE)
    y máximo 300 filas / 8 segundos. Devuelve (columnas, registros)."""
    _avisar(query, {})
    with driver().session(default_access_mode=READ_ACCESS) as s:
        return s.execute_read(_leer, query)


def nuevo_id(prefijo):
    return f"{prefijo}{uuid.uuid4().hex[:6]}"


# ----------------------------------------------------------------- Usuarios
def listar_usuarios():
    return run("""
        MATCH (u:Usuario)
        OPTIONAL MATCH (u)-[:TRABAJA_EN]->(e:Empresa)
        RETURN u.id AS id, u.nombre AS nombre, u.email AS email, u.titular AS titular,
               u.ciudad AS ciudad, u.anios_experiencia AS anios, e.nombre AS empresa
        ORDER BY u.nombre""")


def crear_usuario(nombre, email, titular, ciudad, anios):
    return run("""
        CREATE (u:Usuario {id:$id, nombre:$nombre, email:$email, titular:$titular,
                           ciudad:$ciudad, anios_experiencia:$anios})
        RETURN u.id AS id""",
               id=nuevo_id("u"), nombre=nombre, email=email, titular=titular,
               ciudad=ciudad, anios=anios)


def actualizar_usuario(uid, nombre, email, titular, ciudad, anios):
    return run("""
        MATCH (u:Usuario {id:$id})
        SET u.nombre=$nombre, u.email=$email, u.titular=$titular,
            u.ciudad=$ciudad, u.anios_experiencia=$anios
        RETURN u.id AS id""",
               id=uid, nombre=nombre, email=email, titular=titular, ciudad=ciudad, anios=anios)


def eliminar_usuario(uid):
    """DETACH DELETE borra el nodo y sus relaciones; antes se borran los nodos que
    solo existen por él (sus publicaciones con comentarios, sus comentarios y mensajes)."""
    run("""
        MATCH (u:Usuario {id:$id})
        CALL (u) { OPTIONAL MATCH (u)-[:PUBLICO]->(:Publicacion)<-[:SOBRE]-(k:Comentario) DETACH DELETE k }
        CALL (u) { OPTIONAL MATCH (u)-[:PUBLICO|ESCRIBIO|ENVIO]->(x) DETACH DELETE x }
        CALL (u) { OPTIONAL MATCH (m:Mensaje)-[:PARA]->(u) DETACH DELETE m }
        DETACH DELETE u""", id=uid)


def perfil_usuario(uid):
    return run("""
        MATCH (u:Usuario {id:$id})
        OPTIONAL MATCH (u)-[t:TRABAJA_EN]->(e:Empresa)
        OPTIONAL MATCH (u)-[th:TIENE_HABILIDAD]->(h:Habilidad)
        OPTIONAL MATCH (u)-[:PARTICIPA_EN]->(p:Proyecto)
        OPTIONAL MATCH (u)-[:CONECTA_CON]-(c:Usuario)
        RETURN u{.*} AS usuario, e.nombre AS empresa, t.cargo AS cargo,
               collect(DISTINCT {habilidad:h.nombre, nivel:th.nivel}) AS habilidades,
               collect(DISTINCT p.nombre) AS proyectos,
               collect(DISTINCT c.nombre) AS contactos""", id=uid)


# ------------------------------------------------------------- Catálogos
def opciones(label, campo_id, campo_texto):
    q = f"MATCH (n:{label}) RETURN n.{campo_id} AS id, n.{campo_texto} AS texto ORDER BY texto"
    return run(q)


def listar_empresas():
    return run("""
        MATCH (e:Empresa)
        OPTIONAL MATCH (e)<-[:TRABAJA_EN]-(u:Usuario)
        OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
        RETURN e.id AS id, e.nombre AS nombre, e.sector AS sector, e.ciudad AS ciudad,
               count(DISTINCT u) AS empleados, count(DISTINCT o) AS ofertas
        ORDER BY nombre""")


def crear_empresa(nombre, sector, ciudad):
    run("CREATE (:Empresa {id:$id, nombre:$n, sector:$s, ciudad:$c})",
        id=nuevo_id("e"), n=nombre, s=sector, c=ciudad)


def crear_habilidad(nombre):
    run("MERGE (:Habilidad {nombre:$n})", n=nombre)


def crear_proyecto(nombre, descripcion, tecnologias):
    run("""
        CREATE (p:Proyecto {id:$id, nombre:$n, descripcion:$d})
        WITH p UNWIND $techs AS t
        MATCH (h:Habilidad {nombre:t}) CREATE (p)-[:USA_TECNOLOGIA]->(h)""",
        id=nuevo_id("p"), n=nombre, d=descripcion, techs=tecnologias)


# ------------------------------------------------------------ Relaciones
def conectar_usuarios(a, b):
    return run("""
        MATCH (a:Usuario {id:$a}), (b:Usuario {id:$b})
        WHERE a <> b AND NOT (a)-[:CONECTA_CON]-(b)
        CREATE (a)-[c:CONECTA_CON {desde:date()}]->(b)
        RETURN count(c) AS creadas""", a=a, b=b)


def asignar_habilidad(uid, habilidad, nivel):
    run("""
        MATCH (u:Usuario {id:$u}), (h:Habilidad {nombre:$h})
        MERGE (u)-[t:TIENE_HABILIDAD]->(h) SET t.nivel=$n""", u=uid, h=habilidad, n=nivel)


def asignar_empresa(uid, eid, cargo):
    run("""
        MATCH (u:Usuario {id:$u})
        MATCH (e:Empresa {id:$e})
        OPTIONAL MATCH (u)-[old:TRABAJA_EN]->()
        DELETE old
        WITH DISTINCT u, e
        CREATE (u)-[:TRABAJA_EN {cargo:$c, desde:date()}]->(e)""", u=uid, e=eid, c=cargo)


def asignar_proyecto(uid, pid):
    run("""
        MATCH (u:Usuario {id:$u}), (p:Proyecto {id:$p})
        MERGE (u)-[:PARTICIPA_EN]->(p)""", u=uid, p=pid)


# --------------------------------------------------------------- Ofertas
def crear_oferta(eid, titulo, ubicacion, salario, habilidades):
    run("""
        MATCH (e:Empresa {id:$e})
        CREATE (o:Oferta {id:$id, titulo:$t, ubicacion:$u, salario:$s, estado:'ABIERTA'})
        CREATE (e)-[:PUBLICA]->(o)
        WITH o UNWIND $habs AS hn
        MATCH (h:Habilidad {nombre:hn}) CREATE (o)-[:REQUIERE]->(h)""",
        e=eid, id=nuevo_id("o"), t=titulo, u=ubicacion, s=salario, habs=habilidades)


def listar_ofertas(solo_abiertas=False):
    return run("""
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
        WHERE NOT $solo OR o.estado = 'ABIERTA'
        OPTIONAL MATCH (o)-[:REQUIERE]->(h:Habilidad)
        OPTIONAL MATCH (o)<-[p:POSTULA_A]-(:Usuario)
        RETURN o.id AS id, o.titulo AS titulo, e.nombre AS empresa, o.ubicacion AS ubicacion,
               o.salario AS salario, o.estado AS estado,
               collect(DISTINCT h.nombre) AS habilidades, count(DISTINCT p) AS postulaciones
        ORDER BY o.titulo""", solo=solo_abiertas)


def postular(uid, oid):
    return run("""
        MATCH (u:Usuario {id:$u}), (o:Oferta {id:$o, estado:'ABIERTA'})
        MERGE (u)-[p:POSTULA_A]->(o)
          ON CREATE SET p.fecha=date(), p.estado='EN_REVISION'
        RETURN p.estado AS estado""", u=uid, o=oid)


def postulaciones_de(uid):
    return run("""
        MATCH (:Usuario {id:$u})-[p:POSTULA_A]->(o:Oferta)<-[:PUBLICA]-(e:Empresa)
        RETURN o.titulo AS oferta, e.nombre AS empresa, toString(p.fecha) AS fecha, p.estado AS estado
        ORDER BY p.fecha DESC""", u=uid)


# -------------------------------------------------------------- Consultas
def habilidades_similares(uid):
    return run("""
        MATCH (a:Usuario {id:$id})-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(b:Usuario)
        WHERE a <> b
        WITH a, b, collect(h.nombre) AS compartidas
        MATCH (a)-[:TIENE_HABILIDAD]->(ha:Habilidad)
        WITH a, b, compartidas, collect(ha) AS habA
        MATCH (b)-[:TIENE_HABILIDAD]->(hb:Habilidad)
        WITH b, compartidas, habA, collect(hb) AS habB
        RETURN b.nombre AS usuario, compartidas,
               round(100.0 * size(compartidas) /
                     (size(habA) + size(habB) - size(compartidas))) / 100 AS similitud
        ORDER BY similitud DESC, usuario LIMIT 10""", id=uid)


def contactos_comunes(a, b):
    return run("""
        MATCH (a:Usuario {id:$a})-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(b:Usuario {id:$b})
        RETURN DISTINCT c.nombre AS contacto, c.titular AS titular""", a=a, b=b)


def ruta_mas_corta(uid, eid, solo_contactos=False):
    patron = ("[:CONECTA_CON|TRABAJA_EN*..8]" if solo_contactos else "[:CONECTA_CON|TRABAJA_EN|PARTICIPA_EN|POSTULA_A|PUBLICA|REQUIERE|TIENE_HABILIDAD|USA_TECNOLOGIA*..8]")
    q = f"""
        MATCH (u:Usuario {{id:$u}}), (e:Empresa {{id:$e}}),
              p = shortestPath((u)-{patron}-(e))
        RETURN [n IN nodes(p) | {{etiqueta: labels(n)[0],
                                  nombre: coalesce(n.nombre, n.titulo)}}] AS nodos,
               [r IN relationships(p) | type(r)] AS relaciones,
               length(p) AS saltos"""
    return run(q, u=uid, e=eid)


def candidatos_para_oferta(oid):
    return run("""
        MATCH (o:Oferta {id:$o})-[:REQUIERE]->(req:Habilidad)
        WITH o, collect(req) AS requeridas
        MATCH (o)<-[:PUBLICA]-(emp:Empresa)
        MATCH (u:Usuario)
        WHERE NOT (u)-[:TRABAJA_EN]->(emp) AND NOT (u)-[:POSTULA_A]->(o)
        WITH o, emp, requeridas, u,
             [h IN requeridas WHERE (u)-[:TIENE_HABILIDAD]->(h) | h.nombre] AS cumple
        WHERE size(cumple) > 0
        OPTIONAL MATCH (u)-[:CONECTA_CON]-(colega:Usuario)-[:TRABAJA_EN]->(emp)
        WITH u, requeridas, cumple, count(DISTINCT colega) AS conexiones_empresa
        RETURN u.nombre AS candidato, cumple AS habilidades_cumplidas,
               size(requeridas) AS requeridas, conexiones_empresa,
               round(100 * (0.7 * size(cumple) / size(requeridas)
                 + 0.3 * toFloat(CASE WHEN conexiones_empresa > 3 THEN 3
                                      ELSE conexiones_empresa END) / 3)) AS puntaje
        ORDER BY puntaje DESC LIMIT 10""", o=oid)


def proyectos_relacionados():
    return run("""
        MATCH (p1:Proyecto)-[:USA_TECNOLOGIA]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(p2:Proyecto)
        WHERE p1.id < p2.id
        OPTIONAL MATCH (p1)<-[:PARTICIPA_EN]-(m:Usuario)-[:PARTICIPA_EN]->(p2)
        WITH p1, p2, collect(DISTINCT h.nombre) AS tecnologias, collect(DISTINCT m.nombre) AS miembros
        RETURN p1.nombre AS proyecto_1, p2.nombre AS proyecto_2,
               tecnologias, miembros, size(tecnologias) AS n_tec
        ORDER BY n_tec DESC LIMIT 15""")


def habilidades_demandadas():
    return run("""
        MATCH (h:Habilidad)
        OPTIONAL MATCH (o:Oferta {estado:'ABIERTA'})-[:REQUIERE]->(h)
        WITH h, count(DISTINCT o) AS demanda
        OPTIONAL MATCH (u:Usuario)-[:TIENE_HABILIDAD]->(h)
        RETURN h.nombre AS habilidad, demanda, count(DISTINCT u) AS profesionales
        ORDER BY demanda DESC, habilidad""")


# -------------------------------------------------------- Recomendaciones
def sugerir_contactos(uid):
    return run("""
        MATCH (yo:Usuario {id:$id})-[:CONECTA_CON]-(m:Usuario)-[:CONECTA_CON]-(s:Usuario)
        WHERE s <> yo AND NOT (yo)-[:CONECTA_CON]-(s)
        RETURN s.id AS id, s.nombre AS sugerido, s.titular AS titular,
               count(DISTINCT m) AS contactos_comunes,
               collect(DISTINCT m.nombre) AS a_traves_de
        ORDER BY contactos_comunes DESC LIMIT 5""", id=uid)


def sugerir_empleos(uid):
    return run("""
        MATCH (yo:Usuario {id:$id})
        MATCH (o:Oferta {estado:'ABIERTA'})-[:REQUIERE]->(h:Habilidad)
        WHERE NOT (yo)-[:POSTULA_A]->(o)
        WITH yo, o, collect(h) AS requeridas
        WITH yo, o, requeridas,
             [x IN requeridas WHERE (yo)-[:TIENE_HABILIDAD]->(x) | x.nombre] AS cumple
        WHERE size(cumple) > 0
        MATCH (o)<-[:PUBLICA]-(e:Empresa)
        RETURN o.id AS id, o.titulo AS oferta, e.nombre AS empresa, cumple AS coincidencias,
               round(100.0 * size(cumple) / size(requeridas)) AS porcentaje
        ORDER BY porcentaje DESC LIMIT 5""", id=uid)


def sugerir_colaboradores(uid):
    return run("""
        MATCH (yo:Usuario {id:$id})-[:PARTICIPA_EN]->(:Proyecto)-[:USA_TECNOLOGIA]->(h:Habilidad)
              <-[:USA_TECNOLOGIA]-(p2:Proyecto)<-[:PARTICIPA_EN]-(c:Usuario)
        WHERE c <> yo AND NOT (yo)-[:PARTICIPA_EN]->(p2)
        RETURN c.nombre AS colaborador, collect(DISTINCT p2.nombre) AS proyectos,
               count(DISTINCT h) AS tecnologias_afines
        ORDER BY tecnologias_afines DESC LIMIT 5""", id=uid)


# --------------------------------------------------------------- Analítica
def aristas_usuarios():
    return run("""
        MATCH (a:Usuario)-[:CONECTA_CON]->(b:Usuario)
        RETURN a.id AS a, a.nombre AS na, b.id AS b, b.nombre AS nb""")


def grado_usuarios():
    return run("""
        MATCH (u:Usuario)
        OPTIONAL MATCH (u)-[:CONECTA_CON]-(c:Usuario)
        RETURN u.id AS id, u.nombre AS nombre, count(DISTINCT c) AS conexiones
        ORDER BY conexiones DESC""")


def resumen():
    return run("""
        RETURN COUNT { (:Usuario) } AS usuarios, COUNT { (:Empresa) } AS empresas,
               COUNT { (:Habilidad) } AS habilidades, COUNT { (:Proyecto) } AS proyectos,
               COUNT { (:Oferta) } AS ofertas, COUNT { ()-[]->() } AS relaciones""")[0]


def subgrafo_usuario(uid):
    """Vecindad de 2 saltos de un usuario, para dibujarla."""
    return run("""
        MATCH p = (:Usuario {id:$id})-[*1..2]-(x)
        UNWIND relationships(p) AS r
        WITH DISTINCT r
        RETURN elementId(startNode(r)) AS s, labels(startNode(r))[0] AS sl,
               coalesce(startNode(r).nombre, startNode(r).titulo) AS sn,
               type(r) AS rel,
               elementId(endNode(r)) AS e, labels(endNode(r))[0] AS el,
               coalesce(endNode(r).nombre, endNode(r).titulo) AS en
        LIMIT 150""", id=uid)
