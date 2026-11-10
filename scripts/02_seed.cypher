// =====================================================================
// 02_seed.cypher  -  Datos de ejemplo de la red profesional
// 20 usuarios, 6 empresas, 16 habilidades, 8 proyectos, 10 ofertas.
// Es idempotente (usa MERGE): se puede ejecutar varias veces.
// =====================================================================

// ---------- Habilidades ----------
UNWIND ['Python','Java','JavaScript','SQL','Neo4j','Docker','AWS','React',
        'Machine Learning','Data Analysis','Scrum','UX Design','Kotlin',
        'Cybersecurity','Node.js','Power BI'] AS nombre
MERGE (:Habilidad {nombre: nombre});

// ---------- Empresas ----------
UNWIND [
  {id:'e1', nombre:'TechNova',     sector:'Software',     ciudad:'Bogotá'},
  {id:'e2', nombre:'DataBridge',   sector:'Analítica',    ciudad:'Medellín'},
  {id:'e3', nombre:'CloudNine',    sector:'Nube',         ciudad:'Bogotá'},
  {id:'e4', nombre:'FinSecure',    sector:'Fintech',      ciudad:'Cali'},
  {id:'e5', nombre:'PixelWorks',   sector:'Diseño',       ciudad:'Medellín'},
  {id:'e6', nombre:'AgroSmart',    sector:'Agrotech',     ciudad:'Barranquilla'}
] AS r
MERGE (e:Empresa {id:r.id})
SET e.nombre=r.nombre, e.sector=r.sector, e.ciudad=r.ciudad;

// ---------- Usuarios ----------
UNWIND [
  {id:'u1',  nombre:'Ana Torres',      email:'ana@mail.com',      titular:'Ingeniera de Datos',        ciudad:'Bogotá',       anios:6},
  {id:'u2',  nombre:'Luis Gómez',      email:'luis@mail.com',     titular:'Desarrollador Backend',     ciudad:'Bogotá',       anios:4},
  {id:'u3',  nombre:'Marta Ríos',      email:'marta@mail.com',    titular:'Científica de Datos',       ciudad:'Medellín',     anios:5},
  {id:'u4',  nombre:'Carlos Peña',     email:'carlos@mail.com',   titular:'DevOps Engineer',           ciudad:'Bogotá',       anios:7},
  {id:'u5',  nombre:'Sofía Vargas',    email:'sofia@mail.com',    titular:'Diseñadora UX',             ciudad:'Medellín',     anios:3},
  {id:'u6',  nombre:'Diego Ramírez',   email:'diego@mail.com',    titular:'Desarrollador Frontend',    ciudad:'Cali',         anios:2},
  {id:'u7',  nombre:'Laura Mejía',     email:'laura@mail.com',    titular:'Analista de Seguridad',     ciudad:'Cali',         anios:5},
  {id:'u8',  nombre:'Andrés Castro',   email:'andres@mail.com',   titular:'Arquitecto de Software',    ciudad:'Bogotá',       anios:10},
  {id:'u9',  nombre:'Paula Herrera',   email:'paula@mail.com',    titular:'Product Owner',             ciudad:'Bogotá',       anios:6},
  {id:'u10', nombre:'Julián Ortiz',    email:'julian@mail.com',   titular:'Ingeniero ML',              ciudad:'Medellín',     anios:4},
  {id:'u11', nombre:'Camila Duarte',   email:'camila@mail.com',   titular:'Analista BI',               ciudad:'Barranquilla', anios:3},
  {id:'u12', nombre:'Felipe Salazar',  email:'felipe@mail.com',   titular:'Desarrollador Móvil',       ciudad:'Cali',         anios:3},
  {id:'u13', nombre:'Valentina Cruz',  email:'valentina@mail.com',titular:'Ingeniera Cloud',           ciudad:'Bogotá',       anios:5},
  {id:'u14', nombre:'Mateo Núñez',     email:'mateo@mail.com',    titular:'Desarrollador Full Stack',  ciudad:'Medellín',     anios:4},
  {id:'u15', nombre:'Isabela León',    email:'isabela@mail.com',  titular:'Scrum Master',              ciudad:'Bogotá',       anios:8},
  {id:'u16', nombre:'Sebastián Mora',  email:'sebastian@mail.com',titular:'Ingeniero de Datos',        ciudad:'Barranquilla', anios:2},
  {id:'u17', nombre:'Daniela Pardo',   email:'daniela@mail.com',  titular:'Investigadora en IA',       ciudad:'Bogotá',       anios:6},
  {id:'u18', nombre:'Nicolás Rojas',   email:'nicolas@mail.com',  titular:'Desarrollador Backend',     ciudad:'Cali',         anios:1},
  {id:'u19', nombre:'Gabriela Soto',   email:'gabriela@mail.com', titular:'Diseñadora de Producto',    ciudad:'Medellín',     anios:4},
  {id:'u20', nombre:'Tomás Aguirre',   email:'tomas@mail.com',    titular:'Analista de Datos',         ciudad:'Barranquilla', anios:2}
] AS r
MERGE (u:Usuario {id:r.id})
SET u.nombre=r.nombre, u.email=r.email, u.titular=r.titular,
    u.ciudad=r.ciudad, u.anios_experiencia=r.anios;

// ---------- Proyectos ----------
UNWIND [
  {id:'p1', nombre:'Plataforma de Analítica',   descripcion:'Dashboards en tiempo real'},
  {id:'p2', nombre:'Motor de Recomendación',    descripcion:'Sistema de recomendación con ML'},
  {id:'p3', nombre:'App Móvil Bancaria',        descripcion:'Aplicación móvil de pagos'},
  {id:'p4', nombre:'Migración a la Nube',       descripcion:'Migración de servicios a AWS'},
  {id:'p5', nombre:'Portal de Empleo',          descripcion:'Portal web de vacantes'},
  {id:'p6', nombre:'Sistema Antifraude',        descripcion:'Detección de fraude'},
  {id:'p7', nombre:'Rediseño de Marca Digital', descripcion:'Nueva experiencia web'},
  {id:'p8', nombre:'Monitoreo de Cultivos',     descripcion:'Sensores y analítica agrícola'}
] AS r
MERGE (p:Proyecto {id:r.id})
SET p.nombre=r.nombre, p.descripcion=r.descripcion;

// ---------- Conexiones entre usuarios (se guardan en un sentido, se consultan sin dirección) ----------
UNWIND [
  ['u1','u2'],['u1','u3'],['u1','u4'],['u1','u9'],
  ['u2','u4'],['u2','u8'],['u2','u14'],
  ['u3','u10'],['u3','u17'],['u3','u11'],
  ['u4','u13'],['u4','u8'],
  ['u5','u19'],['u5','u6'],['u5','u14'],
  ['u6','u12'],['u6','u14'],
  ['u7','u12'],['u7','u18'],['u7','u4'],
  ['u8','u9'],['u8','u13'],['u8','u15'],
  ['u9','u15'],
  ['u10','u17'],['u10','u1'],
  ['u11','u16'],['u11','u20'],
  ['u16','u20'],['u16','u1'],
  ['u12','u18'],
  ['u13','u15'],
  ['u19','u9']
] AS par
MATCH (a:Usuario {id:par[0]}), (b:Usuario {id:par[1]})
MERGE (a)-[c:CONECTA_CON]->(b)
  ON CREATE SET c.desde = date('2024-01-01');

// ---------- Usuario trabaja en empresa ----------
UNWIND [
  ['u1','e2','Ingeniera de Datos'],   ['u2','e1','Backend Developer'],
  ['u3','e2','Científica de Datos'],  ['u4','e3','DevOps'],
  ['u5','e5','Diseñadora UX'],        ['u6','e5','Frontend Developer'],
  ['u7','e4','Analista de Seguridad'],['u8','e1','Arquitecto'],
  ['u9','e1','Product Owner'],        ['u10','e2','Ingeniero ML'],
  ['u11','e6','Analista BI'],         ['u12','e4','Desarrollador Móvil'],
  ['u13','e3','Ingeniera Cloud'],     ['u14','e5','Full Stack'],
  ['u15','e1','Scrum Master'],        ['u16','e6','Ingeniero de Datos'],
  ['u17','e2','Investigadora IA'],    ['u18','e4','Backend Developer'],
  ['u19','e5','Diseñadora'],          ['u20','e6','Analista de Datos']
] AS r
MATCH (u:Usuario {id:r[0]}), (e:Empresa {id:r[1]})
MERGE (u)-[t:TRABAJA_EN]->(e)
  ON CREATE SET t.cargo = r[2], t.desde = date('2022-01-01');

// ---------- Usuario tiene habilidad (nivel 1-5) ----------
UNWIND [
  ['u1','Python',5],['u1','SQL',5],['u1','Data Analysis',4],['u1','Neo4j',3],
  ['u2','Java',5],['u2','SQL',4],['u2','Docker',3],['u2','Node.js',3],
  ['u3','Python',5],['u3','Machine Learning',5],['u3','Data Analysis',4],
  ['u4','Docker',5],['u4','AWS',5],['u4','Python',3],
  ['u5','UX Design',5],['u5','JavaScript',2],
  ['u6','JavaScript',4],['u6','React',4],['u6','UX Design',3],
  ['u7','Cybersecurity',5],['u7','Python',3],['u7','SQL',3],
  ['u8','Java',5],['u8','AWS',4],['u8','Docker',4],['u8','SQL',4],['u8','Neo4j',3],
  ['u9','Scrum',4],['u9','Data Analysis',3],
  ['u10','Python',4],['u10','Machine Learning',5],['u10','Docker',3],
  ['u11','Power BI',5],['u11','SQL',4],['u11','Data Analysis',4],
  ['u12','Kotlin',5],['u12','Java',4],
  ['u13','AWS',5],['u13','Docker',4],['u13','Python',3],
  ['u14','JavaScript',5],['u14','React',4],['u14','Node.js',4],['u14','SQL',3],
  ['u15','Scrum',5],
  ['u16','Python',3],['u16','SQL',4],['u16','Neo4j',2],['u16','Data Analysis',3],
  ['u17','Machine Learning',5],['u17','Python',5],
  ['u18','Java',3],['u18','Node.js',2],['u18','SQL',3],
  ['u19','UX Design',4],['u19','Scrum',2],
  ['u20','Power BI',3],['u20','SQL',3],['u20','Data Analysis',3]
] AS r
MATCH (u:Usuario {id:r[0]}), (h:Habilidad {nombre:r[1]})
MERGE (u)-[t:TIENE_HABILIDAD]->(h)
  ON CREATE SET t.nivel = r[2];

// ---------- Usuario participa en proyecto ----------
UNWIND [
  ['u1','p1'],['u3','p1'],['u11','p1'],['u16','p1'],
  ['u3','p2'],['u10','p2'],['u17','p2'],
  ['u12','p3'],['u7','p3'],['u18','p3'],
  ['u4','p4'],['u13','p4'],['u8','p4'],
  ['u2','p5'],['u14','p5'],['u9','p5'],['u6','p5'],
  ['u7','p6'],['u1','p6'],
  ['u5','p7'],['u19','p7'],['u6','p7'],
  ['u11','p8'],['u20','p8'],['u16','p8']
] AS r
MATCH (u:Usuario {id:r[0]}), (p:Proyecto {id:r[1]})
MERGE (u)-[:PARTICIPA_EN]->(p);

// ---------- Tecnologías usadas por proyecto ----------
UNWIND [
  ['p1','Python'],['p1','SQL'],['p1','Power BI'],['p1','Data Analysis'],
  ['p2','Python'],['p2','Machine Learning'],['p2','Neo4j'],
  ['p3','Kotlin'],['p3','Java'],['p3','Cybersecurity'],
  ['p4','AWS'],['p4','Docker'],
  ['p5','React'],['p5','Node.js'],['p5','SQL'],['p5','JavaScript'],
  ['p6','Python'],['p6','Machine Learning'],['p6','Cybersecurity'],
  ['p7','UX Design'],['p7','React'],
  ['p8','Python'],['p8','Data Analysis'],['p8','Power BI']
] AS r
MATCH (p:Proyecto {id:r[0]}), (h:Habilidad {nombre:r[1]})
MERGE (p)-[:USA_TECNOLOGIA]->(h);

// ---------- Ofertas laborales (publicadas por empresas) ----------
UNWIND [
  {id:'o1', empresa:'e1', titulo:'Desarrollador Backend Senior', ubicacion:'Bogotá',       salario:9000000,  estado:'ABIERTA'},
  {id:'o2', empresa:'e2', titulo:'Científico de Datos',          ubicacion:'Medellín',     salario:10000000, estado:'ABIERTA'},
  {id:'o3', empresa:'e3', titulo:'Ingeniero DevOps',             ubicacion:'Bogotá',       salario:11000000, estado:'ABIERTA'},
  {id:'o4', empresa:'e4', titulo:'Analista de Ciberseguridad',   ubicacion:'Cali',         salario:8500000,  estado:'ABIERTA'},
  {id:'o5', empresa:'e5', titulo:'Diseñador UX/UI',              ubicacion:'Medellín',     salario:7000000,  estado:'ABIERTA'},
  {id:'o6', empresa:'e6', titulo:'Analista BI',                  ubicacion:'Barranquilla', salario:6500000,  estado:'ABIERTA'},
  {id:'o7', empresa:'e1', titulo:'Desarrollador Full Stack',     ubicacion:'Bogotá',       salario:8000000,  estado:'ABIERTA'},
  {id:'o8', empresa:'e2', titulo:'Ingeniero de Datos',           ubicacion:'Medellín',     salario:9500000,  estado:'ABIERTA'},
  {id:'o9', empresa:'e3', titulo:'Arquitecto Cloud',             ubicacion:'Bogotá',       salario:13000000, estado:'ABIERTA'},
  {id:'o10',empresa:'e4', titulo:'Desarrollador Móvil Kotlin',   ubicacion:'Cali',         salario:8000000,  estado:'CERRADA'}
] AS r
MATCH (e:Empresa {id:r.empresa})
MERGE (o:Oferta {id:r.id})
SET o.titulo=r.titulo, o.ubicacion=r.ubicacion, o.salario=r.salario, o.estado=r.estado
MERGE (e)-[:PUBLICA]->(o);

// ---------- Habilidades requeridas por oferta ----------
UNWIND [
  ['o1','Java'],['o1','SQL'],['o1','Docker'],
  ['o2','Python'],['o2','Machine Learning'],['o2','Data Analysis'],
  ['o3','Docker'],['o3','AWS'],['o3','Python'],
  ['o4','Cybersecurity'],['o4','Python'],['o4','SQL'],
  ['o5','UX Design'],['o5','JavaScript'],
  ['o6','Power BI'],['o6','SQL'],['o6','Data Analysis'],
  ['o7','JavaScript'],['o7','React'],['o7','Node.js'],['o7','SQL'],
  ['o8','Python'],['o8','SQL'],['o8','Neo4j'],
  ['o9','AWS'],['o9','Docker'],['o9','Java'],
  ['o10','Kotlin'],['o10','Java']
] AS r
MATCH (o:Oferta {id:r[0]}), (h:Habilidad {nombre:r[1]})
MERGE (o)-[:REQUIERE]->(h);

// ---------- Postulaciones ----------
UNWIND [
  ['u2','o1','2026-10-01','EN_REVISION'],['u8','o1','2026-10-02','EN_REVISION'],
  ['u3','o2','2026-10-03','EN_REVISION'],['u17','o2','2026-10-04','ENTREVISTA'],
  ['u10','o2','2026-10-05','EN_REVISION'],
  ['u4','o3','2026-10-06','EN_REVISION'],['u13','o3','2026-10-06','ENTREVISTA'],
  ['u7','o4','2026-10-07','EN_REVISION'],
  ['u5','o5','2026-10-08','EN_REVISION'],['u19','o5','2026-10-09','EN_REVISION'],
  ['u11','o6','2026-10-10','EN_REVISION'],['u20','o6','2026-10-11','EN_REVISION'],
  ['u14','o7','2026-10-12','EN_REVISION'],['u6','o7','2026-10-12','EN_REVISION'],
  ['u1','o8','2026-10-13','ENTREVISTA'],['u16','o8','2026-10-14','EN_REVISION'],
  ['u13','o9','2026-10-15','EN_REVISION'],['u8','o9','2026-10-15','EN_REVISION']
] AS r
MATCH (u:Usuario {id:r[0]}), (o:Oferta {id:r[1]})
MERGE (u)-[p:POSTULA_A]->(o)
  ON CREATE SET p.fecha = date(r[2]), p.estado = r[3];
