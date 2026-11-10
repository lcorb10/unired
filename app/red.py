"""Consultas Cypher de UniRed (la red social construida sobre el mismo grafo).

Modelo agregado al del enunciado:
  (:Usuario)-[:PUBLICO]->(:Publicacion)
  (:Usuario)-[:REACCIONO {tipo, fecha}]->(:Publicacion)
  (:Usuario)-[:ESCRIBIO]->(:Comentario)-[:SOBRE]->(:Publicacion)
  (:Usuario)-[:SOLICITA_CONEXION {fecha}]->(:Usuario)   -> al aceptar se vuelve CONECTA_CON
  (:Usuario)-[:ESTUDIO_EN {id, titulo, area, inicio, fin}]->(:Institucion)
  (:Usuario)-[:ENVIO]->(:Mensaje {id, texto, fecha, leido})-[:PARA]->(:Usuario)  (se borran a las 24 h)
  (:Admin)  cuenta del panel de administración, separada de los usuarios de la red.
"""
from db import nuevo_id, run

REACCIONES = {  # tipo: (nombre, ícono de Bootstrap Icons, color)
    "recomendar": ("Recomendar", "bi-hand-thumbs-up-fill", "#C8102E"),
    "celebrar": ("Celebrar", "bi-trophy-fill", "#2E8B57"),
    "apoyar": ("Apoyar", "bi-person-raised-hand", "#9C6B00"),
    "encanta": ("Me encanta", "bi-heart-fill", "#D2463A"),
    "interesante": ("Interesante", "bi-lightbulb-fill", "#6B4FBB"),
    "divertido": ("Divertido", "bi-emoji-laughing-fill", "#2F6FB5"),
}
HORAS_MENSAJES = 24


# ---------------------------------------------------------------- Cuentas
def cuenta_por_email(email):
    """Busca primero un administrador y luego un usuario de la red."""
    r = run("""
        MATCH (a:Admin {email:$e})
        RETURN a.id AS id, a.nombre AS nombre, a.clave_hash AS clave_hash, 'admin' AS rol""",
            e=email)
    if r:
        return r[0]
    r = run("""
        MATCH (u:Usuario {email:$e})
        RETURN u.id AS id, u.nombre AS nombre, u.clave_hash AS clave_hash, 'usuario' AS rol""",
            e=email)
    return r[0] if r else None


def registrar(nombre, email, clave_hash, titular, ciudad):
    return run("""
        CREATE (u:Usuario {id:$id, nombre:$nombre, email:$email, clave_hash:$clave_hash,
                           titular:$titular, ciudad:$ciudad, anios_experiencia:0,
                           creado: datetime()})
        RETURN u.id AS id""",
               id=nuevo_id("u"), nombre=nombre, email=email, clave_hash=clave_hash,
               titular=titular, ciudad=ciudad)[0]["id"]


def yo(uid):
    r = run("""
        MATCH (u:Usuario {id:$id})
        OPTIONAL MATCH (u)-[:ESTUDIO_EN]->(i:Institucion)
        WITH u, collect(i.nombre)[0] AS institucion
        RETURN u{.id, .nombre, .titular, .ciudad, .foto, .portada} AS u, institucion,
               COUNT { (u)-[:CONECTA_CON]-(:Usuario) } AS contactos,
               COUNT { (:Usuario)-[:SOLICITA_CONEXION]->(u) } AS solicitudes,
               COUNT { (m:Mensaje {leido:false})-[:PARA]->(u) } AS sin_leer,
               u.notif_visto AS notif_visto""", id=uid)
    return r[0] if r else None


# ----------------------------------------------------------- Publicaciones
_POST = """
    RETURN p.id AS id, p.texto AS texto, p.media AS media, p.tipo_media AS tipo_media,
           p.fecha AS fecha, a{.id, .nombre, .titular, .foto} AS autor,
           EXISTS { (:Usuario {id:$yo})-[:CONECTA_CON]-(a) } AS en_red,
           COLLECT { MATCH (:Usuario)-[r:REACCIONO]->(p) RETURN r.tipo } AS reacciones,
           COLLECT { MATCH (:Usuario {id:$yo})-[r:REACCIONO]->(p) RETURN r.tipo } AS mia,
           COLLECT { MATCH (c:Usuario)-[:ESCRIBIO]->(k:Comentario)-[:SOBRE]->(p)
                     RETURN {id:k.id, texto:k.texto, fecha:k.fecha,
                             autor:c{.id, .nombre, .titular, .foto}} AS x
                     ORDER BY k.fecha } AS comentarios"""


def feed(yo_id, solo_red=False, limite=40):
    """Publicaciones: las mías y las de mis contactos primero si solo_red."""
    return run("""
        MATCH (a:Usuario)-[:PUBLICO]->(p:Publicacion)
        WHERE NOT $solo_red OR a.id = $yo OR (:Usuario {id:$yo})-[:CONECTA_CON]-(a)
        WITH a, p ORDER BY p.fecha DESC LIMIT $lim""" + _POST,
               yo=yo_id, solo_red=solo_red, lim=limite)


def publicaciones_de(autor_id, yo_id):
    return run("""
        MATCH (a:Usuario {id:$autor})-[:PUBLICO]->(p:Publicacion)
        WITH a, p ORDER BY p.fecha DESC LIMIT 20""" + _POST, autor=autor_id, yo=yo_id)


def publicacion(pid, yo_id):
    r = run("""
        MATCH (a:Usuario)-[:PUBLICO]->(p:Publicacion {id:$id})""" + _POST, id=pid, yo=yo_id)
    return r[0] if r else None


def publicar(yo_id, texto, media=None, tipo_media=None):
    run("""
        MATCH (yo:Usuario {id:$yo})
        CREATE (yo)-[:PUBLICO]->(:Publicacion {id:$id, texto:$texto, media:$media,
                                               tipo_media:$tipo, fecha: datetime()})""",
        yo=yo_id, id=nuevo_id("p"), texto=texto, media=media, tipo=tipo_media)


def media_de_publicacion(pid):
    r = run("MATCH (p:Publicacion {id:$id}) RETURN p.media AS media", id=pid)
    return r[0]["media"] if r else None


def eliminar_publicacion(pid, autor_id=None):
    """El autor borra la suya; el administrador (autor_id=None) borra cualquiera."""
    r = run("""
        MATCH (a:Usuario)-[:PUBLICO]->(p:Publicacion {id:$id})
        WHERE $autor IS NULL OR a.id = $autor
        OPTIONAL MATCH (k:Comentario)-[:SOBRE]->(p)
        WITH p, p.media AS media, collect(k) AS ks
        FOREACH (k IN ks | DETACH DELETE k)
        DETACH DELETE p
        RETURN media""", id=pid, autor=autor_id)
    return r[0]["media"] if r else False


def reaccionar(yo_id, pid, tipo):
    """Misma reacción otra vez = quitarla. Otra distinta = cambiarla."""
    return run("""
        MATCH (yo:Usuario {id:$yo}), (p:Publicacion {id:$p})
        OPTIONAL MATCH (yo)-[r:REACCIONO]->(p)
        WITH yo, p, r, r.tipo = $tipo AS misma
        FOREACH (_ IN CASE WHEN misma THEN [1] ELSE [] END | DELETE r)
        FOREACH (_ IN CASE WHEN misma THEN [] ELSE [1] END |
            MERGE (yo)-[n:REACCIONO]->(p) SET n.tipo = $tipo, n.fecha = datetime())
        WITH p
        RETURN COLLECT { MATCH (:Usuario)-[x:REACCIONO]->(p) RETURN x.tipo } AS reacciones,
               COLLECT { MATCH (:Usuario {id:$yo})-[x:REACCIONO]->(p) RETURN x.tipo } AS mia""",
               yo=yo_id, p=pid, tipo=tipo)


def comentar(yo_id, pid, texto):
    run("""
        MATCH (yo:Usuario {id:$yo}), (p:Publicacion {id:$p})
        CREATE (yo)-[:ESCRIBIO]->(:Comentario {id:$id, texto:$texto, fecha: datetime()})
               -[:SOBRE]->(p)""", yo=yo_id, p=pid, id=nuevo_id("k"), texto=texto)


def eliminar_comentario(kid, autor_id=None):
    run("""
        MATCH (a:Usuario)-[:ESCRIBIO]->(k:Comentario {id:$id})
        WHERE $autor IS NULL OR a.id = $autor
        DETACH DELETE k""", id=kid, autor=autor_id)


# ------------------------------------------------------------------ Perfil
def perfil(uid, yo_id):
    r = run("""
        MATCH (u:Usuario {id:$id})
        OPTIONAL MATCH (u)-[t:TRABAJA_EN]->(e:Empresa)
        RETURN u{.id, .nombre, .titular, .ciudad, .acerca, .foto, .anios_experiencia, .email} AS u,
               CASE WHEN e IS NULL THEN null ELSE {id:e.id, nombre:e.nombre, cargo:t.cargo,
                    desde:toString(t.desde)} END AS empresa,
               COLLECT { MATCH (u)-[s:ESTUDIO_EN]->(i:Institucion)
                         RETURN {id:s.id, institucion:i.nombre, titulo:s.titulo, area:s.area,
                                 inicio:s.inicio, fin:s.fin} AS x ORDER BY s.inicio DESC } AS estudios,
               COLLECT { MATCH (u)-[th:TIENE_HABILIDAD]->(h:Habilidad)
                         RETURN {nombre:h.nombre, nivel:th.nivel} AS x ORDER BY th.nivel DESC } AS habilidades,
               COLLECT { MATCH (u)-[:PARTICIPA_EN]->(p:Proyecto)
                         RETURN {nombre:p.nombre, descripcion:p.descripcion} } AS proyectos,
               COUNT { (u)-[:CONECTA_CON]-(:Usuario) } AS contactos,
               COLLECT { MATCH (u)-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(:Usuario {id:$yo})
                         RETURN c{.id, .nombre, .foto} } AS comunes,
               CASE WHEN EXISTS { (u)-[:CONECTA_CON]-(:Usuario {id:$yo}) } THEN 'conectado'
                    WHEN EXISTS { (:Usuario {id:$yo})-[:SOLICITA_CONEXION]->(u) } THEN 'enviada'
                    WHEN EXISTS { (u)-[:SOLICITA_CONEXION]->(:Usuario {id:$yo}) } THEN 'recibida'
                    ELSE 'ninguna' END AS estado""", id=uid, yo=yo_id)
    return r[0] if r else None


def camino_hacia(yo_id, uid):
    """Grado de conexión (1.º, 2.º, 3.º…) y el camino de contactos que nos une."""
    r = run("""
        MATCH (yo:Usuario {id:$yo}), (u:Usuario {id:$u})
        MATCH p = shortestPath((yo)-[:CONECTA_CON*..6]-(u))
        RETURN length(p) AS grado,
               [n IN nodes(p) | n{.id, .nombre, .titular, .foto}] AS nodos""", yo=yo_id, u=uid)
    return r[0] if r else None


def actualizar_perfil(uid, nombre, titular, ciudad, acerca, anios):
    run("""
        MATCH (u:Usuario {id:$id})
        SET u.nombre=$nombre, u.titular=$titular, u.ciudad=$ciudad, u.acerca=$acerca,
            u.anios_experiencia=$anios""",
        id=uid, nombre=nombre, titular=titular, ciudad=ciudad, acerca=acerca, anios=anios)


def poner_foto(uid, campo, archivo):
    assert campo in ("foto", "portada")
    r = run(f"MATCH (u:Usuario {{id:$id}}) WITH u, u.{campo} AS antes "
            f"SET u.{campo} = $f RETURN antes", id=uid, f=archivo)
    return r[0]["antes"] if r else None


def cambiar_clave(uid, clave_hash):
    run("MATCH (u:Usuario {id:$id}) SET u.clave_hash = $clave_hash", id=uid, clave_hash=clave_hash)


def instituciones():
    return [r["n"] for r in run("MATCH (i:Institucion) RETURN i.nombre AS n ORDER BY n")]


def agregar_estudio(uid, institucion, titulo, area, inicio, fin):
    run("""
        MATCH (u:Usuario {id:$u})
        MERGE (i:Institucion {nombre:$inst})
        CREATE (u)-[:ESTUDIO_EN {id:$id, titulo:$titulo, area:$area, inicio:$inicio, fin:$fin}]->(i)""",
        u=uid, inst=institucion, id=nuevo_id("s"), titulo=titulo, area=area, inicio=inicio, fin=fin)


def quitar_estudio(uid, sid):
    run("MATCH (:Usuario {id:$u})-[s:ESTUDIO_EN {id:$s}]->() DELETE s", u=uid, s=sid)


def quitar_habilidad(uid, nombre):
    run("MATCH (:Usuario {id:$u})-[t:TIENE_HABILIDAD]->(:Habilidad {nombre:$h}) DELETE t",
        u=uid, h=nombre)


def trabajo_actual(uid, empresa_nombre, cargo):
    """Vincula con una empresa existente o la crea por nombre (MERGE)."""
    run("""
        MATCH (u:Usuario {id:$u})
        OPTIONAL MATCH (u)-[old:TRABAJA_EN]->()
        DELETE old
        WITH DISTINCT u
        MERGE (e:Empresa {nombre:$n})
          ON CREATE SET e.id = $eid, e.sector = '', e.ciudad = u.ciudad
        CREATE (u)-[:TRABAJA_EN {cargo:$c, desde: date()}]->(e)""",
        u=uid, n=empresa_nombre, eid=nuevo_id("e"), c=cargo)


def quitar_trabajo(uid):
    run("MATCH (:Usuario {id:$u})-[t:TRABAJA_EN]->() DELETE t", u=uid)


# ---------------------------------------------------------------- Mi red
def invitaciones(yo_id):
    return run("""
        MATCH (o:Usuario)-[s:SOLICITA_CONEXION]->(:Usuario {id:$yo})
        RETURN o{.id, .nombre, .titular, .foto} AS u, s.fecha AS fecha,
               COUNT { (o)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(:Usuario {id:$yo}) } AS comunes
        ORDER BY fecha DESC""", yo=yo_id)


def enviadas(yo_id):
    return run("""
        MATCH (:Usuario {id:$yo})-[s:SOLICITA_CONEXION]->(o:Usuario)
        RETURN o{.id, .nombre, .titular, .foto} AS u, s.fecha AS fecha ORDER BY fecha DESC""",
               yo=yo_id)


def contactos(yo_id):
    return run("""
        MATCH (:Usuario {id:$yo})-[c:CONECTA_CON]-(o:Usuario)
        RETURN o{.id, .nombre, .titular, .foto} AS u, toString(c.desde) AS desde
        ORDER BY o.nombre""", yo=yo_id)


def sugerencias(yo_id, limite=12):
    """Personas que quizá conozcas: contactos en común (x3), misma institución (x2)
    y habilidades compartidas (x1). Todo sale de recorrer el grafo."""
    return run("""
        MATCH (yo:Usuario {id:$yo}), (s:Usuario)
        WHERE s <> yo AND NOT (yo)-[:CONECTA_CON|SOLICITA_CONEXION]-(s)
        WITH yo, s,
             COUNT { (yo)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(s) } AS comunes,
             COLLECT { MATCH (yo)-[:ESTUDIO_EN]->(i:Institucion)<-[:ESTUDIO_EN]-(s)
                       RETURN DISTINCT i.nombre } AS instituciones,
             COUNT { (yo)-[:TIENE_HABILIDAD]->(:Habilidad)<-[:TIENE_HABILIDAD]-(s) } AS habilidades
        WITH s, comunes, instituciones, habilidades,
             comunes * 3 + size(instituciones) * 2 + habilidades AS puntaje
        WHERE puntaje > 0
        RETURN s{.id, .nombre, .titular, .foto} AS u, comunes, instituciones, habilidades, puntaje
        ORDER BY puntaje DESC, s.nombre LIMIT $lim""", yo=yo_id, lim=limite)


def solicitar(yo_id, otro):
    """Si el otro ya me había invitado, se conecta directamente."""
    r = run("""
        MATCH (yo:Usuario {id:$yo}), (o:Usuario {id:$o})
        WHERE yo <> o AND NOT (yo)-[:CONECTA_CON]-(o)
        OPTIONAL MATCH (o)-[inv:SOLICITA_CONEXION]->(yo)
        FOREACH (_ IN CASE WHEN inv IS NULL THEN [1] ELSE [] END |
            MERGE (yo)-[s:SOLICITA_CONEXION]->(o) ON CREATE SET s.fecha = datetime())
        FOREACH (_ IN CASE WHEN inv IS NULL THEN [] ELSE [1] END |
            DELETE inv CREATE (o)-[:CONECTA_CON {desde: date()}]->(yo))
        RETURN inv IS NOT NULL AS conectados""", yo=yo_id, o=otro)
    return r[0]["conectados"] if r else None


def responder(yo_id, otro, aceptar):
    run("""
        MATCH (o:Usuario {id:$o})-[s:SOLICITA_CONEXION]->(yo:Usuario {id:$yo})
        DELETE s
        WITH o, yo WHERE $aceptar AND NOT (o)-[:CONECTA_CON]-(yo)
        CREATE (o)-[:CONECTA_CON {desde: date()}]->(yo)""", yo=yo_id, o=otro, aceptar=aceptar)


def cancelar_solicitud(yo_id, otro):
    run("MATCH (:Usuario {id:$yo})-[s:SOLICITA_CONEXION]->(:Usuario {id:$o}) DELETE s",
        yo=yo_id, o=otro)


def desconectar(yo_id, otro):
    run("MATCH (:Usuario {id:$yo})-[c:CONECTA_CON]-(:Usuario {id:$o}) DELETE c", yo=yo_id, o=otro)


# ----------------------------------------------------------------- Empleos
def empleos(yo_id, texto=""):
    return run("""
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {estado:'ABIERTA'})
        WHERE $q = '' OR toLower(o.titulo) CONTAINS toLower($q)
              OR toLower(e.nombre) CONTAINS toLower($q) OR toLower(o.ubicacion) CONTAINS toLower($q)
        WITH e, o, COLLECT { MATCH (o)-[:REQUIERE]->(h:Habilidad) RETURN h.nombre } AS requeridas,
             COLLECT { MATCH (o)-[:REQUIERE]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(:Usuario {id:$yo})
                       RETURN h.nombre } AS tengo
        RETURN o{.id, .titulo, .ubicacion, .salario} AS o, e{.id, .nombre} AS empresa,
               requeridas, tengo,
               CASE WHEN size(requeridas) = 0 THEN 0
                    ELSE toInteger(round(100.0 * size(tengo) / size(requeridas))) END AS ajuste,
               EXISTS { (:Usuario {id:$yo})-[:POSTULA_A]->(o) } AS postulado,
               COUNT { (:Usuario {id:$yo})-[:CONECTA_CON]-(:Usuario)-[:TRABAJA_EN]->(e) } AS conocidos
        ORDER BY postulado, ajuste DESC, o.titulo""", yo=yo_id, q=texto)


def mis_postulaciones(yo_id):
    return run("""
        MATCH (:Usuario {id:$yo})-[p:POSTULA_A]->(o:Oferta)<-[:PUBLICA]-(e:Empresa)
        RETURN o.id AS id, o.titulo AS oferta, e.nombre AS empresa, e.id AS empresa_id,
               toString(p.fecha) AS fecha, p.estado AS estado, o.estado AS estado_oferta
        ORDER BY p.fecha DESC""", yo=yo_id)


def retirar_postulacion(yo_id, oid):
    run("MATCH (:Usuario {id:$yo})-[p:POSTULA_A]->(:Oferta {id:$o}) DELETE p", yo=yo_id, o=oid)


def empresa(eid, yo_id):
    r = run("""
        MATCH (e:Empresa {id:$id})
        RETURN e{.id, .nombre, .sector, .ciudad} AS e,
               COLLECT { MATCH (u:Usuario)-[t:TRABAJA_EN]->(e)
                         RETURN {u: u{.id, .nombre, .titular, .foto}, cargo: t.cargo,
                                 contacto: EXISTS { (u)-[:CONECTA_CON]-(:Usuario {id:$yo}) }} } AS empleados,
               COLLECT { MATCH (e)-[:PUBLICA]->(o:Oferta)
                         RETURN o{.id, .titulo, .ubicacion, .salario, .estado} AS x
                         ORDER BY o.estado, o.titulo } AS ofertas,
               EXISTS { (:Usuario {id:$yo})-[:TRABAJA_EN]->(e) } AS trabajo_aqui""", id=eid, yo=yo_id)
    return r[0] if r else None


def mi_empresa(yo_id):
    r = run("MATCH (:Usuario {id:$yo})-[:TRABAJA_EN]->(e:Empresa) RETURN e.id AS id, e.nombre AS nombre",
            yo=yo_id)
    return r[0] if r else None


def postulantes(eid, yo_id):
    """Solo quien trabaja en la empresa ve a los postulantes de sus ofertas."""
    return run("""
        MATCH (:Usuario {id:$yo})-[:TRABAJA_EN]->(e:Empresa {id:$e})-[:PUBLICA]->(o:Oferta)
              <-[p:POSTULA_A]-(u:Usuario)
        RETURN o.id AS oferta_id, o.titulo AS oferta, u{.id, .nombre, .titular, .foto} AS u,
               p.estado AS estado, toString(p.fecha) AS fecha,
               COUNT { (o)-[:REQUIERE]->(:Habilidad)<-[:TIENE_HABILIDAD]-(u) } AS cumple,
               COUNT { (o)-[:REQUIERE]->(:Habilidad) } AS requeridas
        ORDER BY oferta, cumple DESC""", e=eid, yo=yo_id)


def cambiar_estado_postulacion(yo_id, oid, uid, estado):
    run("""
        MATCH (:Usuario {id:$yo})-[:TRABAJA_EN]->(:Empresa)-[:PUBLICA]->(o:Oferta {id:$o})
              <-[p:POSTULA_A]-(:Usuario {id:$u})
        SET p.estado = $estado""", yo=yo_id, o=oid, u=uid, estado=estado)


def cerrar_oferta(yo_id, oid, abierta):
    run("""
        MATCH (:Usuario {id:$yo})-[:TRABAJA_EN]->(:Empresa)-[:PUBLICA]->(o:Oferta {id:$o})
        SET o.estado = CASE WHEN $abierta THEN 'ABIERTA' ELSE 'CERRADA' END""",
        yo=yo_id, o=oid, abierta=abierta)


# ---------------------------------------------------------------- Mensajes
def limpiar_mensajes():
    """Borra los mensajes con más de 24 horas para no llenar la base."""
    r = run("""
        MATCH (m:Mensaje) WHERE m.fecha < datetime() - duration({hours: $h})
        WITH m LIMIT 5000
        DETACH DELETE m
        RETURN count(*) AS borrados""", h=HORAS_MENSAJES)
    return r[0]["borrados"] if r else 0


def conversaciones(yo_id):
    """Último mensaje con cada persona + contactos sin conversación."""
    return run("""
        MATCH (yo:Usuario {id:$yo})
        MATCH (yo)-[:CONECTA_CON]-(o:Usuario)
        OPTIONAL MATCH (a:Usuario)-[:ENVIO]->(m:Mensaje)-[:PARA]->(b:Usuario)
          WHERE (a = yo AND b = o) OR (a = o AND b = yo)
        WITH o, m ORDER BY m.fecha DESC
        WITH o, collect(m)[0] AS ultimo,
             COUNT { (o)-[:ENVIO]->(x:Mensaje {leido:false})-[:PARA]->(:Usuario {id:$yo}) } AS sin_leer
        RETURN o{.id, .nombre, .titular, .foto} AS u,
               ultimo.texto AS texto, ultimo.fecha AS fecha, sin_leer
        ORDER BY fecha IS NULL, fecha DESC, o.nombre""", yo=yo_id)


def puede_escribir(yo_id, otro):
    return bool(run("MATCH (:Usuario {id:$yo})-[:CONECTA_CON]-(o:Usuario {id:$o}) RETURN 1 AS ok",
                    yo=yo_id, o=otro))


def hilo(yo_id, otro, desde=None):
    filas = run("""
        MATCH (yo:Usuario {id:$yo}), (o:Usuario {id:$o})
        MATCH (a:Usuario)-[:ENVIO]->(m:Mensaje)-[:PARA]->(b:Usuario)
        WHERE ((a = yo AND b = o) OR (a = o AND b = yo))
              AND ($desde IS NULL OR m.fecha > datetime($desde))
        RETURN m.id AS id, m.texto AS texto, m.fecha AS fecha, a = yo AS mio
        ORDER BY m.fecha""", yo=yo_id, o=otro, desde=desde)
    run("""
        MATCH (:Usuario {id:$o})-[:ENVIO]->(m:Mensaje {leido:false})-[:PARA]->(:Usuario {id:$yo})
        SET m.leido = true""", yo=yo_id, o=otro)
    return filas


def enviar(yo_id, otro, texto):
    r = run("""
        MATCH (yo:Usuario {id:$yo})-[:CONECTA_CON]-(o:Usuario {id:$o})
        CREATE (yo)-[:ENVIO]->(m:Mensaje {id:$id, texto:$texto, fecha: datetime(), leido:false})
               -[:PARA]->(o)
        RETURN m.id AS id, m.texto AS texto, m.fecha AS fecha, true AS mio""",
            yo=yo_id, o=otro, id=nuevo_id("m"), texto=texto)
    return r[0] if r else None


# ---------------------------------------------------------- Notificaciones
def notificaciones(yo_id):
    return run("""
        CALL () {
            MATCH (yo:Usuario {id:$yo})-[:PUBLICO]->(p:Publicacion)<-[r:REACCIONO]-(o:Usuario)
            WHERE o <> yo
            RETURN 'reaccion' AS tipo, o{.id, .nombre, .foto} AS quien, r.fecha AS fecha,
                   p.id AS ref, r.tipo AS extra, left(p.texto, 70) AS texto
          UNION ALL
            MATCH (yo:Usuario {id:$yo})-[:PUBLICO]->(p:Publicacion)<-[:SOBRE]-(k:Comentario)
                  <-[:ESCRIBIO]-(o:Usuario)
            WHERE o <> yo
            RETURN 'comentario' AS tipo, o{.id, .nombre, .foto} AS quien, k.fecha AS fecha,
                   p.id AS ref, null AS extra, left(k.texto, 70) AS texto
          UNION ALL
            MATCH (o:Usuario)-[s:SOLICITA_CONEXION]->(:Usuario {id:$yo})
            RETURN 'solicitud' AS tipo, o{.id, .nombre, .foto} AS quien, s.fecha AS fecha,
                   o.id AS ref, null AS extra, o.titular AS texto
        }
        RETURN tipo, quien, fecha, ref, extra, texto
        ORDER BY fecha DESC LIMIT 40""", yo=yo_id)


def marcar_notificaciones(yo_id):
    run("MATCH (u:Usuario {id:$yo}) SET u.notif_visto = datetime()", yo=yo_id)


def notificaciones_nuevas(yo_id):
    r = run("""
        MATCH (yo:Usuario {id:$yo})
        WITH yo, coalesce(yo.notif_visto, datetime('2000-01-01T00:00:00Z')) AS visto
        RETURN COUNT { (yo)-[:PUBLICO]->(:Publicacion)<-[r:REACCIONO]-(o:Usuario)
                       WHERE o <> yo AND r.fecha > visto }
             + COUNT { (yo)-[:PUBLICO]->(:Publicacion)<-[:SOBRE]-(k:Comentario)<-[:ESCRIBIO]-(o:Usuario)
                       WHERE o <> yo AND k.fecha > visto }
             + COUNT { (:Usuario)-[s:SOLICITA_CONEXION]->(yo) WHERE s.fecha > visto } AS n""",
            yo=yo_id)
    return r[0]["n"] if r else 0


# ------------------------------------------------------------------ Buscar
def buscar(q):
    return {
        "personas": run("""
            MATCH (u:Usuario)
            WHERE toLower(u.nombre) CONTAINS toLower($q) OR toLower(u.titular) CONTAINS toLower($q)
               OR EXISTS { (u)-[:TIENE_HABILIDAD]->(h:Habilidad) WHERE toLower(h.nombre) = toLower($q) }
            RETURN u{.id, .nombre, .titular, .ciudad, .foto} AS u ORDER BY u.nombre LIMIT 20""", q=q),
        "empresas": run("""
            MATCH (e:Empresa) WHERE toLower(e.nombre) CONTAINS toLower($q)
               OR toLower(e.sector) CONTAINS toLower($q)
            RETURN e{.id, .nombre, .sector, .ciudad} AS e ORDER BY e.nombre LIMIT 10""", q=q),
        "empleos": run("""
            MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {estado:'ABIERTA'})
            WHERE toLower(o.titulo) CONTAINS toLower($q)
               OR EXISTS { (o)-[:REQUIERE]->(h:Habilidad) WHERE toLower(h.nombre) = toLower($q) }
            RETURN o{.id, .titulo, .ubicacion} AS o, e{.id, .nombre} AS empresa LIMIT 10""", q=q),
    }


def habilidades_en_demanda(limite=6):
    return run("""
        MATCH (o:Oferta {estado:'ABIERTA'})-[:REQUIERE]->(h:Habilidad)
        RETURN h.nombre AS nombre, count(o) AS ofertas ORDER BY ofertas DESC, nombre LIMIT $lim""",
               lim=limite)


# ---------------------------------------------------------- Administración
def resumen_red():
    return run("""
        RETURN COUNT { (:Publicacion) } AS publicaciones, COUNT { (:Comentario) } AS comentarios,
               COUNT { ()-[:REACCIONO]->() } AS reacciones, COUNT { (:Mensaje) } AS mensajes,
               COUNT { ()-[:SOLICITA_CONEXION]->() } AS solicitudes,
               COUNT { (:Institucion) } AS instituciones""")[0]


def moderacion(limite=60):
    return run("""
        MATCH (a:Usuario)-[:PUBLICO]->(p:Publicacion)
        RETURN p.id AS id, a.nombre AS autor, a.id AS autor_id, p.texto AS texto,
               p.tipo_media AS tipo_media, p.media AS media, p.fecha AS fecha,
               COUNT { (:Usuario)-[:REACCIONO]->(p) } AS reacciones,
               COLLECT { MATCH (c:Usuario)-[:ESCRIBIO]->(k:Comentario)-[:SOBRE]->(p)
                         RETURN {id:k.id, autor:c.nombre, texto:k.texto} } AS comentarios
        ORDER BY p.fecha DESC LIMIT $lim""", lim=limite)


def conteo_etiquetas():
    return run("""
        CALL db.labels() YIELD label
        CALL (label) { MATCH (n) WHERE label IN labels(n) RETURN count(n) AS total }
        RETURN label AS etiqueta, total ORDER BY total DESC""")


def conteo_relaciones():
    return run("""
        CALL db.relationshipTypes() YIELD relationshipType AS tipo
        CALL (tipo) { MATCH ()-[r]->() WHERE type(r) = tipo RETURN count(r) AS total }
        RETURN tipo, total ORDER BY total DESC""")


def esquema():
    """Qué etiqueta se conecta con cuál y por qué tipo de relación (el modelo real en la base)."""
    return run("""
        MATCH (a)-[r]->(b)
        WITH labels(a)[0] AS desde, type(r) AS rel, labels(b)[0] AS hacia, count(*) AS total
        RETURN desde, rel, hacia, total ORDER BY desde, rel""")


def grafo_completo(limite=600):
    return run("""
        MATCH (a)-[r]->(b)
        WHERE NOT a:Mensaje AND NOT b:Mensaje
        RETURN elementId(a) AS s, labels(a)[0] AS sl, coalesce(a.nombre, a.titulo, left(a.texto, 24)) AS sn,
               type(r) AS rel,
               elementId(b) AS e, labels(b)[0] AS el, coalesce(b.nombre, b.titulo, left(b.texto, 24)) AS en
        LIMIT $lim""", lim=limite)


def restricciones():
    return run("SHOW CONSTRAINTS YIELD name, labelsOrTypes, properties RETURN name, labelsOrTypes, properties")
