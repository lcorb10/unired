// =====================================================================
// 01_schema.cypher  -  Restricciones e índices (Neo4j 5.x)
// Ejecutar una sola vez antes de cargar datos.
// =====================================================================

CREATE CONSTRAINT usuario_id   IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT usuario_mail IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.email IS UNIQUE;
CREATE CONSTRAINT empresa_id   IF NOT EXISTS FOR (e:Empresa)   REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT habilidad_nm IF NOT EXISTS FOR (h:Habilidad) REQUIRE h.nombre IS UNIQUE;
CREATE CONSTRAINT proyecto_id  IF NOT EXISTS FOR (p:Proyecto)  REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT oferta_id    IF NOT EXISTS FOR (o:Oferta)    REQUIRE o.id IS UNIQUE;

CREATE INDEX usuario_nombre IF NOT EXISTS FOR (u:Usuario) ON (u.nombre);
CREATE INDEX empresa_nombre IF NOT EXISTS FOR (e:Empresa) ON (e.nombre);
CREATE INDEX oferta_estado  IF NOT EXISTS FOR (o:Oferta)  ON (o.estado);

// ---------- Red social (UniRed) ----------
CREATE CONSTRAINT admin_email       IF NOT EXISTS FOR (a:Admin)       REQUIRE a.email IS UNIQUE;
CREATE CONSTRAINT publicacion_id    IF NOT EXISTS FOR (p:Publicacion) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT comentario_id     IF NOT EXISTS FOR (k:Comentario)  REQUIRE k.id IS UNIQUE;
CREATE CONSTRAINT mensaje_id        IF NOT EXISTS FOR (m:Mensaje)     REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT institucion_nm    IF NOT EXISTS FOR (i:Institucion) REQUIRE i.nombre IS UNIQUE;

CREATE INDEX publicacion_fecha IF NOT EXISTS FOR (p:Publicacion) ON (p.fecha);
CREATE INDEX mensaje_fecha     IF NOT EXISTS FOR (m:Mensaje)     ON (m.fecha);
