// =====================================================================
// 04_red_social.cypher  -  Datos de ejemplo de UniRed (la capa social)
// Instituciones y estudios, publicaciones, reacciones, comentarios,
// invitaciones de conexión y algunos mensajes recientes.
// Idempotente (MERGE por id). Las fechas son relativas a "ahora".
// =====================================================================

// ---------- Instituciones ----------
UNWIND ['Universidad del Norte','Universidad de los Andes','Universidad Nacional de Colombia',
        'Universidad EAFIT','Universidad del Valle','Pontificia Universidad Javeriana','SENA'] AS n
MERGE (:Institucion {nombre: n});

// ---------- Estudios: (Usuario)-[:ESTUDIO_EN]->(Institucion) ----------
UNWIND [
  ['u1','Universidad Nacional de Colombia','Ingeniería de Sistemas','Datos','2012','2017'],
  ['u2','Universidad de los Andes','Ingeniería de Software','Backend','2015','2020'],
  ['u3','Universidad EAFIT','Matemáticas Aplicadas','Estadística','2013','2018'],
  ['u4','Universidad Nacional de Colombia','Ingeniería Electrónica','Redes','2010','2015'],
  ['u5','Universidad EAFIT','Diseño Interactivo','UX','2016','2021'],
  ['u6','Universidad del Valle','Tecnología en Desarrollo de Software','Frontend','2019','2022'],
  ['u7','Universidad del Valle','Ingeniería de Sistemas','Seguridad','2013','2018'],
  ['u8','Universidad de los Andes','Ingeniería de Sistemas','Arquitectura','2008','2013'],
  ['u8','Universidad de los Andes','Maestría en Ingeniería de Software','','2016','2018'],
  ['u9','Pontificia Universidad Javeriana','Administración de Empresas','Gestión de producto','2012','2017'],
  ['u10','Universidad EAFIT','Ingeniería Matemática','Machine Learning','2015','2020'],
  ['u11','Universidad del Norte','Ingeniería Industrial','Analítica','2017','2022'],
  ['u12','Universidad del Valle','Ingeniería de Sistemas','Móvil','2016','2021'],
  ['u13','Universidad Nacional de Colombia','Ingeniería de Sistemas','Nube','2014','2019'],
  ['u14','Universidad EAFIT','Ingeniería de Sistemas','','2016','2021'],
  ['u15','Pontificia Universidad Javeriana','Ingeniería Industrial','Agilidad','2010','2015'],
  ['u16','Universidad del Norte','Ingeniería de Sistemas','Bases de datos','2020','2025'],
  ['u17','Universidad de los Andes','Doctorado en Ingeniería','Inteligencia artificial','2016','2021'],
  ['u18','SENA','Tecnólogo en Análisis y Desarrollo de Software','','2022','2024'],
  ['u19','Universidad EAFIT','Diseño Industrial','Producto digital','2016','2021'],
  ['u20','Universidad del Norte','Ingeniería de Sistemas','Ciencia de datos','2021','']
] AS r
MATCH (u:Usuario {id:r[0]}), (i:Institucion {nombre:r[1]})
MERGE (u)-[s:ESTUDIO_EN {id: 's-' + r[0] + '-' + r[4]}]->(i)
  ON CREATE SET s.titulo = r[2], s.area = r[3], s.inicio = r[4], s.fin = r[5];

// ---------- Textos de perfil ----------
UNWIND [
  ['u1','Diseño pipelines de datos y modelos de grafos. Me interesa conectar a quienes empiezan en datos con proyectos reales.'],
  ['u8','Arquitecto de software con 10 años de experiencia en sistemas distribuidos. Mentor de estudiantes de último semestre.'],
  ['u11','Analista BI en Barranquilla. Power BI, SQL y mucha curiosidad por la logística del Caribe.'],
  ['u16','Egresado de Uninorte. Trabajo con Neo4j y SQL, y me gusta explicar bases de datos con ejemplos sencillos.'],
  ['u20','Estudiante de Ingeniería de Sistemas en Uninorte. Buscando mi primera práctica en análisis de datos.']
] AS r
MATCH (u:Usuario {id:r[0]}) SET u.acerca = r[1];

// ---------- Publicaciones: (Usuario)-[:PUBLICO]->(Publicacion) ----------
UNWIND [
  ['p1','u16', 3,   'Terminamos la migración del modelo de recomendaciones a Neo4j. La consulta de "amigos de amigos" pasó de 4 JOIN a una línea de Cypher. Si alguien de Uninorte quiere ver el modelo, escríbame.'],
  ['p2','u8',  9,   'Consejo para quien está por graduarse: muestren un proyecto terminado, aunque sea pequeño, antes que diez a medias. Se nota la diferencia en una entrevista.'],
  ['p3','u20', 20,  '¡Busco práctica profesional en análisis de datos para el próximo semestre! Manejo Python, SQL y Power BI. Cualquier recomendación es bienvenida.'],
  ['p4','u13', 27,  'Nuevo artículo en el blog del equipo: cómo bajamos 40 % la factura de AWS apagando entornos de prueba por la noche. Spoiler: fue un script de 30 líneas.'],
  ['p5','u5',  35,  'En PixelWorks estamos haciendo pruebas de usabilidad con estudiantes. Si quieres participar (45 min, virtual) comenta abajo.'],
  ['p6','u11', 50,  'Primer tablero publicado en AgroSmart: precios de cosecha por municipio del Atlántico. Orgullosa del equipo.'],
  ['p7','u10', 72,  'Comparto el material del taller de Machine Learning que dimos en Medellín. Incluye los cuadernos y el conjunto de datos.'],
  ['p8','u7',  96,  'Recordatorio: la autenticación de dos factores no es opcional. Esta semana vimos tres cuentas comprometidas por reutilizar contraseñas.'],
  ['p9','u15', 130, 'Retro del sprint: menos reuniones, más tablero. Pasamos de 6 h a 2 h semanales de ceremonias y la velocidad del equipo subió.'],
  ['p10','u3', 170, 'Hoy cumplo 5 años como científica de datos. Gracias a todos los que me ayudaron a cambiar de las matemáticas puras a la industria.']
] AS r
MATCH (a:Usuario {id:r[1]})
MERGE (p:Publicacion {id:r[0]})
  ON CREATE SET p.texto = r[3], p.fecha = datetime() - duration({hours: r[2]})
MERGE (a)-[:PUBLICO]->(p);

// ---------- Reacciones: (Usuario)-[:REACCIONO {tipo}]->(Publicacion) ----------
UNWIND [
  ['u1','p1','recomendar'],['u20','p1','celebrar'],['u11','p1','interesante'],['u8','p1','recomendar'],['u2','p1','encanta'],
  ['u16','p2','recomendar'],['u20','p2','apoyar'],['u14','p2','recomendar'],['u9','p2','interesante'],
  ['u16','p3','apoyar'],['u11','p3','apoyar'],['u1','p3','recomendar'],
  ['u4','p4','celebrar'],['u8','p4','interesante'],
  ['u19','p5','encanta'],['u6','p5','recomendar'],
  ['u16','p6','celebrar'],['u20','p6','celebrar'],['u1','p6','encanta'],
  ['u17','p7','recomendar'],['u3','p7','encanta'],
  ['u12','p8','recomendar'],['u4','p8','apoyar'],
  ['u9','p9','divertido'],['u2','p9','recomendar'],
  ['u10','p10','celebrar'],['u17','p10','celebrar'],['u1','p10','encanta']
] AS r
MATCH (u:Usuario {id:r[0]}), (p:Publicacion {id:r[1]})
MERGE (u)-[x:REACCIONO]->(p)
  ON CREATE SET x.tipo = r[2], x.fecha = p.fecha + duration({minutes: 20});

// ---------- Comentarios: (Usuario)-[:ESCRIBIO]->(Comentario)-[:SOBRE]->(Publicacion) ----------
UNWIND [
  ['k1','u20','p1','¡Me interesa mucho! Estoy viendo grafos en Bases de Datos este semestre.', 1],
  ['k2','u1','p1','Muy buen resultado. ¿Usaron restricciones de unicidad desde el inicio?', 2],
  ['k3','u16','p3','Te escribo por mensaje, en mi equipo abren prácticas en enero.', 18],
  ['k4','u11','p3','Revisa también las ofertas de AgroSmart, buscan perfiles de datos.', 15],
  ['k5','u19','p5','¡Cuenta conmigo!', 30],
  ['k6','u14','p2','Totalmente de acuerdo, el portafolio pesa más que el promedio.', 7]
] AS r
MATCH (u:Usuario {id:r[1]}), (p:Publicacion {id:r[2]})
MERGE (k:Comentario {id:r[0]})
  ON CREATE SET k.texto = r[3], k.fecha = datetime() - duration({hours: r[4]})
MERGE (u)-[:ESCRIBIO]->(k)
MERGE (k)-[:SOBRE]->(p);

// ---------- Invitaciones pendientes: (Usuario)-[:SOLICITA_CONEXION]->(Usuario) ----------
UNWIND [['u20','u8'],['u18','u16'],['u6','u16'],['u17','u20']] AS par
MATCH (a:Usuario {id:par[0]}), (b:Usuario {id:par[1]})
WHERE NOT (a)-[:CONECTA_CON]-(b)
MERGE (a)-[s:SOLICITA_CONEXION]->(b) ON CREATE SET s.fecha = datetime() - duration({hours: 5});

// ---------- Algunas conexiones nuevas entre egresados de Uninorte ----------
UNWIND [['u16','u20'],['u1','u16'],['u11','u20'],['u11','u16']] AS par
MATCH (a:Usuario {id:par[0]}), (b:Usuario {id:par[1]})
WHERE NOT (a)-[:CONECTA_CON]-(b)
CREATE (a)-[:CONECTA_CON {desde: date()}]->(b);

// ---------- Mensajes (se borran solos a las 24 h) ----------
UNWIND [
  ['m1','u16','u20','Hola Tomás, vi tu publicación. ¿Me mandas tu hoja de vida?', 180],
  ['m2','u20','u16','¡Claro! Te la envío hoy mismo. Muchas gracias.', 170],
  ['m3','u16','u20','Perfecto, la paso al líder del equipo de datos.', 160],
  ['m4','u1','u16','¿Nos vemos el jueves para revisar el modelo del grafo?', 45]
] AS r
MATCH (a:Usuario {id:r[1]}), (b:Usuario {id:r[2]})
WHERE (a)-[:CONECTA_CON]-(b)
MERGE (m:Mensaje {id:r[0]})
  ON CREATE SET m.texto = r[3], m.fecha = datetime() - duration({minutes: r[4]}), m.leido = false
MERGE (a)-[:ENVIO]->(m)
MERGE (m)-[:PARA]->(b);
