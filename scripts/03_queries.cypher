// =====================================================================
// 03_queries.cypher  -  Consultas del proyecto (Neo4j 5.x)
// Cada consulta usa valores de ejemplo; en la app se pasan como parámetros.
// Ejecutar de a una en Neo4j Browser (http://localhost:7474).
// =====================================================================


// ---------------------------------------------------------------------
// A. CRUD
// ---------------------------------------------------------------------

// A1. Crear usuario
CREATE (u:Usuario {id:'u21', nombre:'Elena Prado', email:'elena@mail.com',
                   titular:'Ingeniera de Datos', ciudad:'Bogotá', anios_experiencia:3})
RETURN u;

// A2. Consultar usuario con su perfil completo
MATCH (u:Usuario {id:'u1'})
OPTIONAL MATCH (u)-[:TRABAJA_EN]->(e:Empresa)
OPTIONAL MATCH (u)-[th:TIENE_HABILIDAD]->(h:Habilidad)
RETURN u, e.nombre AS empresa, collect({habilidad:h.nombre, nivel:th.nivel}) AS habilidades;

// A3. Actualizar usuario
MATCH (u:Usuario {id:'u21'})
SET u.titular = 'Científica de Datos Senior', u.anios_experiencia = 4
RETURN u;

// A4. Eliminar usuario y todas sus relaciones
MATCH (u:Usuario {id:'u21'})
DETACH DELETE u;


// ---------------------------------------------------------------------
// B. Relaciones
// ---------------------------------------------------------------------

// B1. Conectar dos usuarios (MERGE evita duplicados aunque se invierta el orden)
MATCH (a:Usuario {id:'u5'}), (b:Usuario {id:'u9'})
WHERE NOT (a)-[:CONECTA_CON]-(b)
CREATE (a)-[:CONECTA_CON {desde: date()}]->(b);

// B2. Asignar habilidad a usuario
MATCH (u:Usuario {id:'u5'}), (h:Habilidad {nombre:'React'})
MERGE (u)-[t:TIENE_HABILIDAD]->(h) SET t.nivel = 3;

// B3. Vincular usuario con empresa
MATCH (u:Usuario {id:'u18'}), (e:Empresa {id:'e1'})
MERGE (u)-[t:TRABAJA_EN]->(e) SET t.cargo = 'Backend Developer', t.desde = date();

// B4. Vincular usuario con proyecto
MATCH (u:Usuario {id:'u5'}), (p:Proyecto {id:'p5'})
MERGE (u)-[:PARTICIPA_EN]->(p);

// B5. Empresa publica oferta y la ligamos con las habilidades requeridas
MATCH (e:Empresa {id:'e3'})
CREATE (o:Oferta {id:'o11', titulo:'Ingeniero SRE', ubicacion:'Bogotá',
                  salario:12000000, estado:'ABIERTA'})
CREATE (e)-[:PUBLICA]->(o)
WITH o
UNWIND ['Docker','AWS','Python'] AS hab
MATCH (h:Habilidad {nombre:hab})
CREATE (o)-[:REQUIERE]->(h)
RETURN o;

// B6. Postulación de un usuario a una oferta
MATCH (u:Usuario {id:'u4'}), (o:Oferta {id:'o9'})
MERGE (u)-[p:POSTULA_A]->(o)
  ON CREATE SET p.fecha = date(), p.estado = 'EN_REVISION'
RETURN u.nombre, o.titulo, p.estado;


// ---------------------------------------------------------------------
// C. Preguntas del enunciado
// ---------------------------------------------------------------------

// C1. ¿Qué usuarios tienen habilidades similares? (índice de Jaccard)
MATCH (a:Usuario {id:'u1'})-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(b:Usuario)
WHERE a <> b
WITH a, b, collect(h.nombre) AS compartidas
MATCH (a)-[:TIENE_HABILIDAD]->(ha:Habilidad)
WITH a, b, compartidas, collect(ha) AS habA
MATCH (b)-[:TIENE_HABILIDAD]->(hb:Habilidad)
WITH a, b, compartidas, habA, collect(hb) AS habB
RETURN b.nombre AS usuario, compartidas,
       size(compartidas) * 1.0 /
         (size(habA) + size(habB) - size(compartidas)) AS similitud
ORDER BY similitud DESC, usuario
LIMIT 10;

// C2. ¿Qué contactos en común existen entre dos profesionales?
MATCH (a:Usuario {id:'u1'})-[:CONECTA_CON]-(comun:Usuario)-[:CONECTA_CON]-(b:Usuario {id:'u8'})
RETURN comun.nombre AS contacto_en_comun, comun.titular AS titular;

// C3. ¿Cuál es la ruta más corta entre un usuario y una empresa?
//     (solo relaciones del modelo profesional: no pasa por invitaciones, publicaciones ni mensajes; máx. 8 saltos)
MATCH (u:Usuario {id:'u6'}), (e:Empresa {nombre:'CloudNine'}),
      p = shortestPath((u)-[:CONECTA_CON|TRABAJA_EN|PARTICIPA_EN|POSTULA_A|PUBLICA|REQUIERE|TIENE_HABILIDAD|USA_TECNOLOGIA*..8]-(e))
RETURN p, length(p) AS saltos,
       [n IN nodes(p) | coalesce(n.nombre, n.titulo)] AS camino;

// C3b. Variante restringida a contactos profesionales + trabajo (más "humana")
MATCH (u:Usuario {id:'u6'}), (e:Empresa {nombre:'CloudNine'}),
      p = shortestPath((u)-[:CONECTA_CON|TRABAJA_EN*..8]-(e))
RETURN [n IN nodes(p) | coalesce(n.nombre, n.titulo)] AS camino, length(p) AS saltos;

// C4. ¿Qué candidatos podrían recomendarse para una oferta según sus conexiones y competencias?
//     puntaje = 70 % cobertura de habilidades + 30 % conexiones con empleados de la empresa
MATCH (o:Oferta {id:'o3'})-[:REQUIERE]->(req:Habilidad)
WITH o, collect(req) AS requeridas
MATCH (o)<-[:PUBLICA]-(emp:Empresa)
MATCH (u:Usuario)
WHERE NOT (u)-[:TRABAJA_EN]->(emp) AND NOT (u)-[:POSTULA_A]->(o)
WITH o, emp, requeridas, u,
     [h IN requeridas WHERE (u)-[:TIENE_HABILIDAD]->(h) | h.nombre] AS cumple
WHERE size(cumple) > 0
OPTIONAL MATCH (u)-[:CONECTA_CON]-(colega:Usuario)-[:TRABAJA_EN]->(emp)
WITH u, requeridas, cumple, count(DISTINCT colega) AS conexiones_empresa
RETURN u.nombre AS candidato, cumple AS habilidades_cumplidas, conexiones_empresa,
       round(100 * (0.7 * size(cumple) / size(requeridas)
                    + 0.3 * toFloat(CASE WHEN conexiones_empresa > 3 THEN 3 ELSE conexiones_empresa END) / 3)) AS puntaje
ORDER BY puntaje DESC
LIMIT 10;

// C5. ¿Qué proyectos comparten tecnologías o miembros relacionados?
MATCH (p1:Proyecto)-[:USA_TECNOLOGIA]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(p2:Proyecto)
WHERE p1.id < p2.id
OPTIONAL MATCH (p1)<-[:PARTICIPA_EN]-(m:Usuario)-[:PARTICIPA_EN]->(p2)
RETURN p1.nombre AS proyecto_1, p2.nombre AS proyecto_2,
       collect(DISTINCT h.nombre) AS tecnologias_comunes,
       collect(DISTINCT m.nombre) AS miembros_comunes
ORDER BY size(collect(DISTINCT h.nombre)) DESC
LIMIT 10;

// C6. ¿Qué habilidades son las más demandadas en las ofertas?
MATCH (o:Oferta {estado:'ABIERTA'})-[:REQUIERE]->(h:Habilidad)
RETURN h.nombre AS habilidad, count(o) AS ofertas
ORDER BY ofertas DESC, habilidad
LIMIT 10;

// C6b. Brecha: demanda vs. oferta de talento
MATCH (h:Habilidad)
OPTIONAL MATCH (o:Oferta {estado:'ABIERTA'})-[:REQUIERE]->(h)
WITH h, count(DISTINCT o) AS demanda
OPTIONAL MATCH (u:Usuario)-[:TIENE_HABILIDAD]->(h)
RETURN h.nombre AS habilidad, demanda, count(DISTINCT u) AS profesionales,
       demanda - count(DISTINCT u) AS brecha
ORDER BY brecha DESC;


// ---------------------------------------------------------------------
// D. Recomendaciones
// ---------------------------------------------------------------------

// D1. Contactos sugeridos: amigos de amigos (aún no conectados)
MATCH (yo:Usuario {id:'u1'})-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(sug:Usuario)
WHERE sug <> yo AND NOT (yo)-[:CONECTA_CON]-(sug)
RETURN sug.nombre AS sugerido, sug.titular AS titular, count(*) AS contactos_comunes
ORDER BY contactos_comunes DESC
LIMIT 5;

// D2. Empleos sugeridos: ofertas abiertas con más habilidades del usuario
MATCH (yo:Usuario {id:'u14'})
MATCH (o:Oferta {estado:'ABIERTA'})-[:REQUIERE]->(h:Habilidad)
WHERE NOT (yo)-[:POSTULA_A]->(o)
WITH yo, o, collect(h) AS requeridas
WITH yo, o, requeridas,
     [x IN requeridas WHERE (yo)-[:TIENE_HABILIDAD]->(x) | x.nombre] AS cumple
WHERE size(cumple) > 0
MATCH (o)<-[:PUBLICA]-(emp:Empresa)
RETURN o.titulo AS oferta, emp.nombre AS empresa, cumple AS coincidencias,
       size(cumple) AS n, size(requeridas) AS total,
       round(100.0 * size(cumple) / size(requeridas)) AS porcentaje
ORDER BY porcentaje DESC, n DESC
LIMIT 5;

// D3. Colaboradores sugeridos: personas con habilidades en proyectos afines a los míos
MATCH (yo:Usuario {id:'u1'})-[:PARTICIPA_EN]->(:Proyecto)-[:USA_TECNOLOGIA]->(h:Habilidad)
      <-[:USA_TECNOLOGIA]-(p2:Proyecto)<-[:PARTICIPA_EN]-(col:Usuario)
WHERE col <> yo AND NOT (yo)-[:PARTICIPA_EN]->(p2)
RETURN col.nombre AS colaborador, collect(DISTINCT p2.nombre) AS proyectos,
       count(DISTINCT h) AS tecnologias_afines
ORDER BY tecnologias_afines DESC
LIMIT 5;


// ---------------------------------------------------------------------
// E. Analítica
// ---------------------------------------------------------------------

// E1. Usuarios más influyentes (centralidad de grado)
MATCH (u:Usuario)
OPTIONAL MATCH (u)-[:CONECTA_CON]-(c:Usuario)
RETURN u.nombre AS usuario, count(DISTINCT c) AS conexiones
ORDER BY conexiones DESC
LIMIT 10;

// E2. Empresas con más postulaciones
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)<-[:POSTULA_A]-(u:Usuario)
RETURN e.nombre AS empresa, count(u) AS postulaciones
ORDER BY postulaciones DESC;

// E3. Comunidades con Graph Data Science (OPCIONAL: requiere el plugin GDS)
//     La aplicación calcula comunidades en Python (networkx) para no depender del plugin.
// CALL gds.graph.project('red', 'Usuario', {CONECTA_CON:{orientation:'UNDIRECTED'}});
// CALL gds.louvain.stream('red')
// YIELD nodeId, communityId
// RETURN communityId, collect(gds.util.asNode(nodeId).nombre) AS miembros
// ORDER BY size(miembros) DESC;
// CALL gds.pageRank.stream('red') YIELD nodeId, score
// RETURN gds.util.asNode(nodeId).nombre AS usuario, score ORDER BY score DESC LIMIT 10;
