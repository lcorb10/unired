// Construye el documento del proyecto (Word) con el estado actual de UniRed.
//   node docs/construir_word.js  ->  Proyecto_Grafos_Red_Profesional.docx (raíz del proyecto)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, ImageRun, PageBreak, LevelFormat, BorderStyle, Footer, PageNumber,
  TableOfContents, TabStopType,
} = require("docx");

const RAIZ = path.resolve(__dirname, "..");
const IMG = path.join(__dirname, "img");
const ROJO = "C8102E", GRIS = "5F5F5F", FONDO = "F2F1EF";
const ANCHO = 9360; // 6.5 in en DXA

// ---------- texto con **negrita** y `código` ----------
function runs(texto, base = {}) {
  const partes = texto.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);
  return partes.map(p => {
    if (p.startsWith("**")) return new TextRun({ ...base, text: p.slice(2, -2), bold: true });
    if (p.startsWith("`")) return new TextRun({ ...base, text: p.slice(1, -1), font: "Consolas", size: 19, color: "9E0B23" });
    return new TextRun({ ...base, text: p });
  });
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 120, line: 288 }, ...o });
const H1 = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], pageBreakBefore: false });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = t => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const B = (t, nivel = 0) => new Paragraph({ numbering: { reference: "vinetas", level: nivel }, children: runs(t), spacing: { after: 60, line: 276 } });
const N = t => new Paragraph({ numbering: { reference: "numeros", level: 0 }, children: runs(t), spacing: { after: 60, line: 276 } });
const SALTO = () => new Paragraph({ children: [new PageBreak()] });

function codigo(texto) {
  const lineas = texto.replace(/\r/g, "").split("\n");
  return lineas.map((l, i) => new Paragraph({
    children: [new TextRun({ text: l.length ? l : " ", font: "Consolas", size: 17 })],
    shading: { type: ShadingType.CLEAR, color: "auto", fill: FONDO },
    spacing: { before: i === 0 ? 80 : 0, after: i === lineas.length - 1 ? 140 : 0, line: 240 },
    indent: { left: 120, right: 120 },
    keepLines: true,
  }));
}

function tamPng(f) { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }
let nFig = 0;
function figura(nombre, pie, anchoPx = 620) {
  const f = path.join(IMG, nombre + ".png");
  const [w, h] = tamPng(f);
  let ancho = anchoPx, alto = Math.round(anchoPx * h / w);
  if (alto > 760) { alto = 760; ancho = Math.round(760 * w / h); }
  nFig++;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: ancho, height: alto },
        altText: { title: pie, description: pie, name: nombre } })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
      children: [new TextRun({ text: `Figura ${nFig}. `, bold: true, size: 19, color: GRIS }), new TextRun({ text: pie, size: 19, color: GRIS, italics: true })] }),
  ];
}

function tabla(encabezados, filas, anchos) {
  const borde = { style: BorderStyle.SINGLE, size: 4, color: "D9D6D1" };
  const bordes = { top: borde, bottom: borde, left: borde, right: borde };
  const celda = (t, i, cab) => new TableCell({
    width: { size: anchos[i], type: WidthType.DXA }, borders: bordes,
    shading: cab ? { type: ShadingType.CLEAR, color: "auto", fill: "1E1E1E" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: runs(t, cab ? { bold: true, color: "FFFFFF", size: 19 } : { size: 19 }) })],
  });
  return new Table({
    width: { size: anchos.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: anchos,
    rows: [new TableRow({ tableHeader: true, children: encabezados.map((t, i) => celda(t, i, true)) }),
      ...filas.map(f => new TableRow({ cantSplit: true, children: f.map((t, i) => celda(t, i, false)) }))],
  });
}
const ESP = () => new Paragraph({ spacing: { after: 80 }, children: [] });
const leer = f => fs.readFileSync(path.join(RAIZ, f), "utf8");

// =============================================================== contenido
const c = [];

// ---------- portada ----------
c.push(
  new Paragraph({ spacing: { before: 1800, after: 120 }, children: [new TextRun({ text: "Bases de Datos · 202610-2497", color: GRIS, size: 24 })] }),
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Proyecto de Investigación y Desarrollo (I+D)", size: 28, bold: true })] }),
  new Paragraph({ spacing: { after: 600 }, children: [new TextRun({ text: "Bases de datos no relacionales: bases de datos orientadas a grafos", size: 24, color: GRIS })] }),
  new Paragraph({ spacing: { after: 300 }, children: [new TextRun({ text: "Diseño e implementación de una aplicación basada en base de datos de grafos para la gestión y análisis de relaciones en una red profesional", size: 40, bold: true, font: "Segoe UI Semibold" })] }),
  new Paragraph({ spacing: { after: 900 }, border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: ROJO, space: 8 } },
    children: [new TextRun({ text: "UniRed: red profesional sobre Neo4j", size: 30, color: ROJO, bold: true })] }),
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "Integrantes", bold: true, size: 22 })] }),
  ...["Mateo Gómez", "Valerie Angulo", "Sahory Blanco", "Sebastián Corbacho", "Cristian Viloria"].map(n =>
    new Paragraph({ spacing: { after: 20 }, children: [new TextRun({ text: n, size: 22 })] })),
  new Paragraph({ spacing: { before: 300, after: 40 }, children: [new TextRun({ text: "Docente: ", bold: true, size: 22 }), new TextRun({ text: "Wilson Estrada Bernal", size: 22 })] }),
  new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Fecha de entrega: ", bold: true, size: 22 }), new TextRun({ text: "10 de noviembre de 2026", size: 22 })] }),
  new Paragraph({ children: [new TextRun({ text: "Universidad del Norte · Barranquilla", size: 22, color: GRIS })] }),
  SALTO(),
  new Paragraph({ spacing: { after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ROJO, space: 4 } },
    children: [new TextRun({ text: "Contenido", size: 32, bold: true, font: "Segoe UI Semibold" })] }),
  new TableOfContents("Contenido", { hyperlink: true, headingStyleRange: "1-2" }),
  P("Para actualizar la tabla de contenido en Word: clic derecho sobre ella → **Actualizar campos**.", { spacing: { before: 200 } }),
  SALTO(),
);

// ---------- 1 ----------
c.push(
  H1("1. Introducción y objetivos"),
  P("Muchas aplicaciones actuales manejan información altamente interconectada, donde las relaciones entre los datos son tan importantes como los datos mismos. Las redes profesionales (contactos, empleos, habilidades, proyectos) son un ejemplo típico. Este proyecto diseña e implementa una red profesional sobre **Neo4j**, una base de datos de grafos, y documenta el modelo, los scripts, las consultas y el análisis de cuándo conviene (y cuándo no) este paradigma frente al relacional."),
  P("El resultado es **UniRed**, una aplicación web con dos caras sobre el mismo grafo: un **panel de administración** que cubre punto por punto lo que pide el enunciado (CRUD, relaciones, consultas, recomendaciones y analítica) y una **red social** con inicio de sesión, publicaciones, reacciones, comentarios, mensajes y estudios, que muestra el modelo de grafos funcionando como lo usaría una persona real."),
  P("**Objetivos.**"),
  B("Afianzar los conocimientos de diseño y modelamiento de bases de datos no relacionales."),
  B("Demostrar la utilidad de las bases de datos de grafos en escenarios con relaciones múltiples y dinámicas, evidenciando sus ventajas frente a modelos tradicionales en análisis de redes y recomendación."),
  H2("1.1 Cumplimiento del enunciado"),
  tabla(["Requisito del enunciado", "Dónde se cumple"], [
    ["CRUD de usuarios con información personal y profesional", "Panel › Usuarios (crear, ver, editar, eliminar con `DETACH DELETE`); registro y edición de perfil en UniRed"],
    ["Relacionar usuarios con conexiones profesionales", "Panel › Relaciones (`CONECTA_CON`); en UniRed, invitaciones `SOLICITA_CONEXION` que al aceptarse crean `CONECTA_CON`"],
    ["Vincular usuarios con habilidades, empresas y proyectos", "Panel › Relaciones y Editar perfil (`TIENE_HABILIDAD`, `TRABAJA_EN`, `PARTICIPA_EN`)"],
    ["Registrar empresas y sus ofertas", "Panel › Empresas y Ofertas; en UniRed, quien trabaja en una empresa publica sus ofertas (`PUBLICA`)"],
    ["Relacionar ofertas con habilidades requeridas", "Al publicar una oferta se crean las relaciones `REQUIERE`"],
    ["Postularse a una oferta", "UniRed › Empleos y Panel › Ofertas (`POSTULA_A` con estado)"],
    ["Consultar caminos y conexiones", "Panel › Consultas (ruta más corta dibujada); perfil «Cómo llegas a…» con `shortestPath`"],
    ["Recomendaciones de contactos, empleos y colaboradores", "Panel › Recomendaciones; UniRed › «Personas que quizá conozcas» y «Empleos para ti»"],
    ["Panel de analítica: influyentes, comunidades, habilidades demandadas", "Panel › Analítica (grado + PageRank, comunidades, demanda y brecha)"],
    ["Las 6 preguntas del enunciado", "Panel › Consultas del enunciado y `03_queries.cypher` (C1–C6)"],
    ["Documento, scripts y componente de investigación", "Este documento: secciones 2–8 y anexos A–C"],
  ], [3600, 5760]),
  ESP(),
);

// ---------- 2 ----------
c.push(
  H1("2. Bases de datos de grafos"),
  H2("2.1 Concepto"),
  P("Una base de datos de grafos almacena la información como **nodos** (entidades) y **relaciones** (conexiones entre entidades). Ambos pueden tener **propiedades** en forma de pares clave-valor. Neo4j implementa el modelo de grafo de propiedades etiquetadas (labeled property graph):"),
  B("**Nodo:** entidad con una o más etiquetas (p. ej. `:Usuario`) y propiedades."),
  B("**Relación:** conexión dirigida, con un tipo obligatorio (p. ej. `:CONECTA_CON`), un nodo origen, un nodo destino y propiedades opcionales."),
  B("**Propiedad:** dato clave-valor asociado a nodos o relaciones."),
  H2("2.2 Adyacencia sin índices"),
  P("La característica diferencial de motores como Neo4j es la **adyacencia sin índice** (index-free adjacency): cada nodo guarda referencias directas a sus relaciones, de modo que recorrer una conexión cuesta lo mismo sin importar el tamaño total del grafo. El costo de una consulta depende de la porción del grafo que se recorre, no del volumen total de datos. En el modelo relacional, en cambio, cada salto equivale a un JOIN que consulta índices o recorre tablas."),
  H2("2.3 Cypher"),
  P("Cypher es el lenguaje declarativo de Neo4j. Describe patrones con una sintaxis de «arte ASCII»: los nodos van entre paréntesis y las relaciones entre corchetes, por ejemplo `(a:Usuario)-[:CONECTA_CON]->(b:Usuario)`. Soporta recorridos de longitud variable (`[*..8]`), funciones de camino como `shortestPath`, agregaciones, comprensión de listas y subconsultas `COUNT { }` / `COLLECT { }`."),
  H2("2.4 Tecnología elegida"),
  tabla(["Componente", "Elección"], [
    ["Motor de grafos", "Neo4j 5.26 Community (portable en el PC, sin instalador; también funciona con Neo4j Desktop o AuraDB)"],
    ["Lenguaje de consulta", "Cypher"],
    ["Aplicación", "Python 3 + Flask (plantillas Jinja2, Bootstrap 5) con el controlador oficial `neo4j`"],
    ["Analítica", "Cypher + networkx (PageRank, comunidades); alternativa opcional: Neo4j GDS"],
    ["Visualización", "vis-network (grafos interactivos) y Chart.js (gráficas)"],
    ["Servidor y publicación", "waitress (servidor WSGI) + Cloudflare Tunnel (enlace https público desde el PC)"],
    ["Seguridad", "Contraseñas con hash (werkzeug/PBKDF2), token CSRF, consultas parametrizadas, consola de solo lectura"],
  ], [2600, 6760]),
  ESP(),
);

// ---------- 3 ----------
c.push(
  H1("3. Modelo de datos"),
  P("El modelo parte de las entidades y relaciones sugeridas en el enunciado. Se añadió `USA_TECNOLOGIA` (Proyecto → Habilidad), necesaria para responder «¿qué proyectos comparten tecnologías?», y una **capa social** (publicaciones, reacciones, comentarios, invitaciones, estudios y mensajes) que convierte la red en una aplicación usable sin alterar el núcleo pedido."),
  ...figura("modelo", "Modelo del grafo de UniRed. En gris, las relaciones del enunciado; en rojo punteado, la capa social."),
  H2("3.1 Nodos"),
  tabla(["Etiqueta", "Descripción", "Propiedades"], [
    ["Usuario", "Persona registrada", "id (único), nombre, email (único), clave_hash, titular, ciudad, anios_experiencia, acerca, foto, portada"],
    ["Empresa", "Organización o compañía", "id (único), nombre, sector, ciudad"],
    ["Habilidad", "Competencia o conocimiento", "nombre (único)"],
    ["Proyecto", "Trabajo o iniciativa", "id (único), nombre, descripcion"],
    ["Oferta", "Vacante laboral", "id (único), titulo, ubicacion, salario, estado (ABIERTA/CERRADA)"],
    ["Institucion", "Universidad o centro de estudios", "nombre (único)"],
    ["Publicacion", "Publicación del feed", "id (único), texto, media, tipo_media (imagen/video), fecha"],
    ["Comentario", "Comentario a una publicación", "id (único), texto, fecha"],
    ["Mensaje", "Mensaje privado entre contactos (dura 24 h)", "id (único), texto, fecha, leido"],
    ["Admin", "Cuenta del panel de administración", "id, email (único), nombre, clave_hash"],
  ], [1500, 2700, 5160]),
  ESP(),
  H2("3.2 Relaciones"),
  tabla(["Relación", "Dirección", "Propiedades"], [
    ["CONECTA_CON", "Usuario → Usuario", "desde (fecha). Se consulta sin dirección"],
    ["TRABAJA_EN", "Usuario → Empresa", "cargo, desde"],
    ["TIENE_HABILIDAD", "Usuario → Habilidad", "nivel (1 a 5)"],
    ["PARTICIPA_EN", "Usuario → Proyecto", "—"],
    ["PUBLICA", "Empresa → Oferta", "—"],
    ["REQUIERE", "Oferta → Habilidad", "—"],
    ["POSTULA_A", "Usuario → Oferta", "fecha, estado (EN_REVISION, ENTREVISTA, SELECCIONADO, DESCARTADO)"],
    ["USA_TECNOLOGIA", "Proyecto → Habilidad", "—"],
    ["SOLICITA_CONEXION", "Usuario → Usuario", "fecha. Al aceptarse se borra y se crea CONECTA_CON"],
    ["ESTUDIO_EN", "Usuario → Institucion", "id, titulo, area, inicio, fin"],
    ["PUBLICO", "Usuario → Publicacion", "—"],
    ["REACCIONO", "Usuario → Publicacion", "tipo (recomendar, celebrar, apoyar, encanta, interesante, divertido), fecha"],
    ["ESCRIBIO / SOBRE", "Usuario → Comentario → Publicacion", "—"],
    ["ENVIO / PARA", "Usuario → Mensaje → Usuario", "—"],
  ], [2300, 3000, 4060]),
  ESP(),
  H2("3.3 Decisiones de diseño"),
  B("**Habilidad como nodo, no como propiedad.** Al ser nodo, conecta usuarios, ofertas y proyectos; permite descubrir similitudes y demanda recorriendo el grafo en lugar de comparar listas de texto."),
  B("**Los datos que pertenecen a la relación van en la relación.** El nivel de dominio vive en `TIENE_HABILIDAD`, el estado de la postulación en `POSTULA_A` y el tipo de reacción en `REACCIONO`."),
  B("**CONECTA_CON se guarda en un solo sentido y se consulta sin dirección.** Evita duplicar aristas; las consultas usan `-[:CONECTA_CON]-`."),
  B("**La invitación es una relación distinta.** `SOLICITA_CONEXION` representa una conexión que todavía no existe. Por eso las consultas de caminos del enunciado solo recorren las relaciones profesionales: una invitación pendiente no es un camino real."),
  B("**Institución como nodo.** «Estudió en la misma universidad» se vuelve un patrón de dos saltos que alimenta las recomendaciones de contactos."),
  B("**Las notificaciones no se guardan.** Se calculan con una consulta `UNION ALL` sobre las reacciones, comentarios e invitaciones que apuntan al usuario, así no hay datos duplicados que mantener."),
  B("**Los mensajes vencen a las 24 horas.** Un proceso de la app ejecuta cada 10 minutos `MATCH (m:Mensaje) WHERE m.fecha < datetime() - duration({hours: 24}) DETACH DELETE m`, para no llenar la base."),
  B("**Admin separado de Usuario.** La cuenta del panel tiene su propia etiqueta, así no aparece en recomendaciones, analítica ni caminos."),
  B("**Restricciones de unicidad.** Cada nodo tiene una clave única (y `email` en Usuario); además crean índices que aceleran los `MATCH` por id. Hay índices en `Oferta.estado`, `Publicacion.fecha` y `Mensaje.fecha`."),
);

// ---------- 4 ----------
c.push(
  H1("4. Scripts de la base de datos"),
  P("Los scripts están en la carpeta `scripts/` y se ejecutan en orden con `python cargar_datos.py` (o pegándolos en Neo4j Browser). Los datos se cargan con `MERGE`, de modo que ejecutarlos varias veces no duplica información. El contenido completo está en los **anexos A, B y C**."),
  tabla(["Archivo", "Contenido"], [
    ["01_schema.cypher", "Restricciones de unicidad e índices (incluye los nodos de la capa social)"],
    ["02_seed.cypher", "Datos de ejemplo: 20 usuarios, 6 empresas, 16 habilidades, 8 proyectos, 10 ofertas, conexiones, habilidades, proyectos y postulaciones"],
    ["03_queries.cypher", "CRUD, creación de relaciones, preguntas del enunciado, recomendaciones y analítica"],
    ["04_red_social.cypher", "7 instituciones y estudios, 10 publicaciones, reacciones, comentarios, invitaciones y mensajes recientes"],
  ], [2600, 6760]),
  ESP(),
  H2("4.1 Esquema"),
  ...codigo("CREATE CONSTRAINT usuario_id   IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.id IS UNIQUE;\nCREATE CONSTRAINT usuario_mail IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.email IS UNIQUE;\nCREATE CONSTRAINT habilidad_nm IF NOT EXISTS FOR (h:Habilidad) REQUIRE h.nombre IS UNIQUE;\n// ... empresa, proyecto, oferta, publicacion, comentario, mensaje, institucion y admin\nCREATE INDEX oferta_estado     IF NOT EXISTS FOR (o:Oferta)      ON (o.estado);\nCREATE INDEX mensaje_fecha     IF NOT EXISTS FOR (m:Mensaje)     ON (m.fecha);"),
  H2("4.2 Carga de datos (fragmentos)"),
  ...codigo("UNWIND [\n  {id:'u1', nombre:'Ana Torres', email:'ana@mail.com',\n   titular:'Ingeniera de Datos', ciudad:'Bogotá', anios:6}, ...\n] AS r\nMERGE (u:Usuario {id:r.id})\nSET u.nombre=r.nombre, u.email=r.email, u.titular=r.titular,\n    u.ciudad=r.ciudad, u.anios_experiencia=r.anios;"),
  ...codigo("// Estudios: (Usuario)-[:ESTUDIO_EN]->(Institucion)\nUNWIND [['u16','Universidad del Norte','Ingeniería de Sistemas','Bases de datos','2020','2025'], ...] AS r\nMATCH (u:Usuario {id:r[0]}), (i:Institucion {nombre:r[1]})\nMERGE (u)-[s:ESTUDIO_EN {id: 's-' + r[0] + '-' + r[4]}]->(i)\n  ON CREATE SET s.titulo = r[2], s.area = r[3], s.inicio = r[4], s.fin = r[5];"),
  P("Las contraseñas no se escriben en los scripts: `cargar_datos.py` asigna a los usuarios de ejemplo un hash de la clave de demostración y crea la cuenta de administrador con la clave definida en el archivo `.env`."),
);

// ---------- 5 ----------
c.push(
  H1("5. Consultas"),
  P("Las siguientes consultas están en `03_queries.cypher` y se invocan desde la aplicación con parámetros (`$id`, `$o`…). En la app, el botón **Ver Cypher** muestra la consulta exacta y sus parámetros en cada pantalla (figura 12)."),
  H2("5.1 CRUD y relaciones"),
  ...codigo("CREATE (u:Usuario {id:'u21', nombre:'Elena Prado', email:'elena@mail.com',\n                   titular:'Ingeniera de Datos', ciudad:'Bogotá', anios_experiencia:3})\nRETURN u;\n\nMATCH (u:Usuario {id:'u21'})\nSET u.titular = 'Científica de Datos Senior', u.anios_experiencia = 4\nRETURN u;\n\nMATCH (u:Usuario {id:'u21'})\nDETACH DELETE u;"),
  P("`DETACH DELETE` elimina el nodo junto con todas sus relaciones; sin `DETACH`, Neo4j rechaza borrar un nodo que aún tiene conexiones. En la app, antes se borran los nodos que solo existen por ese usuario (sus publicaciones con sus comentarios, sus comentarios y sus mensajes)."),
  ...codigo("MATCH (u:Usuario {id:'u4'}), (o:Oferta {id:'o9'})\nMERGE (u)-[p:POSTULA_A]->(o)\n  ON CREATE SET p.fecha = date(), p.estado = 'EN_REVISION'\nRETURN u.nombre, o.titulo, p.estado;"),
  H2("5.2 ¿Qué usuarios tienen habilidades similares?"),
  ...codigo("MATCH (a:Usuario {id:'u1'})-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(b:Usuario)\nWHERE a <> b\nWITH a, b, collect(h.nombre) AS compartidas\nMATCH (a)-[:TIENE_HABILIDAD]->(ha:Habilidad)\nWITH a, b, compartidas, collect(ha) AS habA\nMATCH (b)-[:TIENE_HABILIDAD]->(hb:Habilidad)\nWITH a, b, compartidas, habA, collect(hb) AS habB\nRETURN b.nombre AS usuario, compartidas,\n       size(compartidas) * 1.0 / (size(habA) + size(habB) - size(compartidas)) AS similitud\nORDER BY similitud DESC, usuario LIMIT 10;"),
  P("Se recorre Usuario → Habilidad ← Usuario para hallar las habilidades compartidas y se calcula el **índice de Jaccard** (compartidas / unión de habilidades de ambos)."),
  ...figura("admin_consulta_similares", "Consulta C1 en el panel: usuarios con habilidades similares a Ana Torres."),
  H2("5.3 ¿Qué contactos en común existen entre dos profesionales?"),
  ...codigo("MATCH (a:Usuario {id:'u1'})-[:CONECTA_CON]-(comun:Usuario)-[:CONECTA_CON]-(b:Usuario {id:'u8'})\nRETURN comun.nombre AS contacto_en_comun, comun.titular AS titular;"),
  P("Un patrón de dos saltos con un nodo intermedio. En SQL requeriría un auto-JOIN de la tabla de conexiones."),
  H2("5.4 ¿Cuál es la ruta más corta entre un usuario y una empresa?"),
  ...codigo("MATCH (u:Usuario {id:'u6'}), (e:Empresa {nombre:'CloudNine'}),\n      p = shortestPath((u)-[:CONECTA_CON|TRABAJA_EN|PARTICIPA_EN|POSTULA_A|PUBLICA|REQUIERE|TIENE_HABILIDAD|USA_TECNOLOGIA*..8]-(e))\nRETURN p, length(p) AS saltos,\n       [n IN nodes(p) | coalesce(n.nombre, n.titulo)] AS camino;"),
  P("`shortestPath` busca el camino mínimo (hasta 8 saltos) sobre las relaciones del modelo profesional: puede pasar por contactos, empleos, proyectos, ofertas o habilidades, pero no por invitaciones pendientes, publicaciones ni mensajes. La variante C3b limita el recorrido a contactos y empleos."),
  ...figura("admin_consulta_ruta", "Ruta más corta dibujada en el panel: Ana Torres llega a AgroSmart en 2 saltos."),
  H2("5.5 ¿Qué candidatos podrían recomendarse para una oferta?"),
  ...codigo("MATCH (o:Oferta {id:'o3'})-[:REQUIERE]->(req:Habilidad)\nWITH o, collect(req) AS requeridas\nMATCH (o)<-[:PUBLICA]-(emp:Empresa)\nMATCH (u:Usuario)\nWHERE NOT (u)-[:TRABAJA_EN]->(emp) AND NOT (u)-[:POSTULA_A]->(o)\nWITH o, emp, requeridas, u,\n     [h IN requeridas WHERE (u)-[:TIENE_HABILIDAD]->(h) | h.nombre] AS cumple\nWHERE size(cumple) > 0\nOPTIONAL MATCH (u)-[:CONECTA_CON]-(colega:Usuario)-[:TRABAJA_EN]->(emp)\nWITH u, requeridas, cumple, count(DISTINCT colega) AS conexiones_empresa\nRETURN u.nombre AS candidato, cumple AS habilidades_cumplidas, conexiones_empresa,\n       round(100 * (0.7 * size(cumple) / size(requeridas)\n                    + 0.3 * toFloat(CASE WHEN conexiones_empresa > 3 THEN 3 ELSE conexiones_empresa END) / 3)) AS puntaje\nORDER BY puntaje DESC LIMIT 10;"),
  P("Combina contenido y estructura social: 70 % de cobertura de las habilidades requeridas y 30 % de contactos que el candidato tiene dentro de la empresa (tope de 3). Se excluyen empleados actuales y quienes ya se postularon."),
  ...figura("admin_consulta_candidatos", "Candidatos recomendados para una oferta, con su puntaje."),
  H2("5.6 ¿Qué proyectos comparten tecnologías o miembros?"),
  ...codigo("MATCH (p1:Proyecto)-[:USA_TECNOLOGIA]->(h:Habilidad)<-[:USA_TECNOLOGIA]-(p2:Proyecto)\nWHERE p1.id < p2.id\nOPTIONAL MATCH (p1)<-[:PARTICIPA_EN]-(m:Usuario)-[:PARTICIPA_EN]->(p2)\nRETURN p1.nombre AS proyecto_1, p2.nombre AS proyecto_2,\n       collect(DISTINCT h.nombre) AS tecnologias_comunes,\n       collect(DISTINCT m.nombre) AS miembros_comunes\nORDER BY size(collect(DISTINCT h.nombre)) DESC LIMIT 10;"),
  H2("5.7 ¿Qué habilidades son las más demandadas?"),
  ...codigo("MATCH (o:Oferta {estado:'ABIERTA'})-[:REQUIERE]->(h:Habilidad)\nRETURN h.nombre AS habilidad, count(o) AS ofertas\nORDER BY ofertas DESC, habilidad LIMIT 10;"),
  P("Agregación sobre las ofertas abiertas. La variante C6b contrasta la demanda con la cantidad de profesionales que tienen cada habilidad (brecha de talento)."),
  H2("5.8 Recomendaciones"),
  P("**Contactos (amigos de amigos):**"),
  ...codigo("MATCH (yo:Usuario {id:'u1'})-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(sug:Usuario)\nWHERE sug <> yo AND NOT (yo)-[:CONECTA_CON]-(sug)\nRETURN sug.nombre AS sugerido, sug.titular AS titular, count(*) AS contactos_comunes\nORDER BY contactos_comunes DESC LIMIT 5;"),
  P("**Empleos** (ofertas abiertas con más habilidades del usuario) y **colaboradores** (personas en proyectos con tecnologías afines) completan las consultas D2 y D3 del script."),
  ...figura("admin_recomendaciones", "Recomendaciones de contactos, empleos y colaboradores para un usuario."),
  H2("5.9 Analítica"),
  ...codigo("MATCH (u:Usuario)\nOPTIONAL MATCH (u)-[:CONECTA_CON]-(c:Usuario)\nRETURN u.nombre AS usuario, count(DISTINCT c) AS conexiones\nORDER BY conexiones DESC LIMIT 10;"),
  P("En la aplicación se complementa con **PageRank** y detección de **comunidades** (modularidad voraz de networkx) sobre las aristas `CONECTA_CON` leídas desde Neo4j. Con el plugin Graph Data Science se obtienen los mismos resultados con `gds.pageRank` y `gds.louvain`; el script lo incluye comentado."),
  ...figura("admin_analitica", "Panel de analítica: usuarios más influyentes y habilidades más demandadas."),
  H2("5.10 Consultas de la capa social"),
  P("**Personas que quizá conozcas.** Un puntaje que suma contactos en común (×3), instituciones compartidas (×2) y habilidades compartidas (×1), todo calculado recorriendo el grafo:"),
  ...codigo("MATCH (yo:Usuario {id:$yo}), (s:Usuario)\nWHERE s <> yo AND NOT (yo)-[:CONECTA_CON|SOLICITA_CONEXION]-(s)\nWITH yo, s,\n     COUNT { (yo)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(s) } AS comunes,\n     COLLECT { MATCH (yo)-[:ESTUDIO_EN]->(i:Institucion)<-[:ESTUDIO_EN]-(s) RETURN DISTINCT i.nombre } AS instituciones,\n     COUNT { (yo)-[:TIENE_HABILIDAD]->(:Habilidad)<-[:TIENE_HABILIDAD]-(s) } AS habilidades\nWITH s, comunes, instituciones, habilidades, comunes * 3 + size(instituciones) * 2 + habilidades AS puntaje\nWHERE puntaje > 0\nRETURN s.nombre, comunes, instituciones, habilidades, puntaje ORDER BY puntaje DESC LIMIT 12;"),
  P("**Grado de conexión y «Cómo llegas a…».** El perfil de otra persona muestra si es contacto de 1.º, 2.º o 3.er grado y el camino real de contactos:"),
  ...codigo("MATCH (yo:Usuario {id:$yo}), (u:Usuario {id:$u})\nMATCH p = shortestPath((yo)-[:CONECTA_CON*..6]-(u))\nRETURN length(p) AS grado, [n IN nodes(p) | n.nombre] AS camino;"),
  P("**Aceptar una invitación** convierte la relación pendiente en una conexión real:"),
  ...codigo("MATCH (o:Usuario {id:$o})-[s:SOLICITA_CONEXION]->(yo:Usuario {id:$yo})\nDELETE s\nWITH o, yo WHERE $aceptar AND NOT (o)-[:CONECTA_CON]-(yo)\nCREATE (o)-[:CONECTA_CON {desde: date()}]->(yo);"),
  P("**Mensajes que vencen.** Solo se puede escribir a un contacto (el `MATCH` exige `CONECTA_CON`) y la limpieza borra lo que tenga más de 24 horas:"),
  ...codigo("MATCH (yo:Usuario {id:$yo})-[:CONECTA_CON]-(o:Usuario {id:$o})\nCREATE (yo)-[:ENVIO]->(m:Mensaje {id:$id, texto:$texto, fecha: datetime(), leido:false})-[:PARA]->(o);\n\nMATCH (m:Mensaje) WHERE m.fecha < datetime() - duration({hours: 24})\nDETACH DELETE m;"),
);

// ---------- 6 ----------
c.push(
  H1("6. Aplicación UniRed"),
  P("La aplicación web está construida con Flask y se conecta a Neo4j mediante el controlador oficial. Los datos de conexión (URI, usuario y contraseña) se leen de un archivo `.env`, de modo que el mismo código funciona con Neo4j local, Neo4j Desktop o AuraDB. Todas las consultas Cypher están en los módulos `db.py` (enunciado) y `red.py` (capa social), y siempre reciben parámetros, nunca texto concatenado, lo que evita la inyección de Cypher."),
  H2("6.1 Arquitectura"),
  tabla(["Archivo", "Responsabilidad"], [
    ["app.py", "Arranque de Flask, inicio de sesión y registro, protección CSRF, registro de consultas para «Ver Cypher», limpieza de mensajes cada 10 min"],
    ["db.py", "Conexión a Neo4j y todas las consultas del enunciado; consola de solo lectura"],
    ["red.py", "Consultas de la capa social (feed, reacciones, perfil, red, empleos, mensajes, notificaciones)"],
    ["rutas_admin.py / rutas_red.py", "Pantallas del panel de administración y de UniRed"],
    ["cargar_datos.py", "Ejecuta los scripts 01, 02 y 04, asigna claves de demostración y crea el administrador"],
    ["servidor.py", "Servidor de producción (waitress) que se publica con el túnel"],
  ], [2800, 6560]),
  ESP(),
  H2("6.2 Inicio de sesión y registro"),
  P("Cualquier persona puede crear una cuenta con nombre, correo, contraseña (mínimo 8 caracteres), titular, ciudad y dónde estudia; eso crea el nodo `Usuario` y su relación `ESTUDIO_EN`. Las contraseñas se guardan como hash, nunca en texto plano. El mismo formulario sirve a los administradores, que llegan directamente al panel. Al entrar se muestra una pantalla de carga con el logo animado."),
  ...figura("app_entrar", "Pantalla de inicio de sesión de UniRed."),
  H2("6.3 Feed, publicaciones y reacciones"),
  P("El feed muestra las publicaciones (todas o solo las de mi red) con texto, foto o video. Cada publicación admite seis reacciones (recomendar, celebrar, apoyar, me encanta, interesante y divertido) que se guardan como la propiedad `tipo` de la relación `REACCIONO`, y comentarios (`ESCRIBIO` → `SOBRE`). A los lados aparecen la tarjeta del usuario, «Personas que quizá conozcas» y las habilidades más pedidas en las ofertas."),
  ...figura("app_feed", "Feed de UniRed con publicaciones, sugerencias de contactos y habilidades más pedidas."),
  ...figura("app_reacciones", "Paleta de reacciones; la elegida se guarda en la relación REACCIONO.", 520),
  H2("6.4 Perfil, estudios y «Cómo llegas a…»"),
  P("El perfil reúne experiencia (`TRABAJA_EN`), educación (`ESTUDIO_EN`), habilidades con nivel (`TIENE_HABILIDAD`), proyectos y publicaciones. Si es el perfil de otra persona, muestra el grado de conexión y el camino más corto de contactos para llegar a ella, además de los contactos en común."),
  ...figura("app_perfil", "Perfil de Tomás Aguirre visto por Sebastián: grado de conexión, camino y contactos en común."),
  H2("6.5 Mi red, empleos y mensajes"),
  P("**Mi red** muestra las invitaciones recibidas y enviadas, los contactos y las sugerencias con el motivo (contactos en común, misma institución, habilidades). **Empleos** ordena las ofertas abiertas por porcentaje de ajuste con las habilidades del usuario, resalta las que ya tiene y cuenta cuántos contactos trabajan en la empresa; quien trabaja en una empresa puede publicar ofertas y cambiar el estado de los postulantes. **Mensajes** permite conversar en vivo solo con contactos; los mensajes se borran a las 24 horas."),
  ...figura("app_empleos", "Empleos para ti: ajuste por habilidades y contactos que trabajan en la empresa."),
  ...figura("app_mensajes", "Mensajería entre contactos con aviso de borrado a las 24 horas."),
  H2("6.6 Panel de administración"),
  tabla(["Sección", "Funcionalidad"], [
    ["Inicio y vecindad", "Contadores del grafo y visualización interactiva de la vecindad de 2 saltos de un usuario"],
    ["Base de datos", "Nodos por etiqueta, relaciones por tipo con su origen y destino, consola Cypher de solo lectura, grafo completo y restricciones"],
    ["Usuarios", "Listar, ver perfil, crear, editar y eliminar usuarios"],
    ["Relaciones", "Conectar usuarios; asignar habilidades; vincular con empresa y proyecto; crear habilidades y proyectos"],
    ["Empresas, ofertas y postulaciones", "Registrar empresas, publicar ofertas con habilidades requeridas, postular candidatos"],
    ["Publicaciones y mensajes", "Moderar publicaciones y comentarios; contar mensajes (no se leen) y forzar la limpieza de 24 h"],
    ["Consultas del enunciado", "Las seis preguntas; la ruta más corta se dibuja"],
    ["Recomendaciones y analítica", "Contactos, empleos y colaboradores; influyentes, habilidades demandadas y brecha, comunidades"],
  ], [2800, 6560]),
  ESP(),
  ...figura("admin_base", "Panel › Base de datos: conteos por etiqueta y tipo de relación, consola y grafo completo."),
  ...figura("admin_consola", "Consola Cypher de solo lectura: el resultado se muestra como tabla y como grafo.", 560),
  H2("6.7 «Ver Cypher»"),
  P("Un botón flotante en todas las pantallas abre un panel con las consultas Cypher que se enviaron a Neo4j para construir la página y las de la última acción (por ejemplo, publicar o reaccionar), con sus parámetros. Las contraseñas aparecen ocultas. Sirve para explicar en la demostración qué hace la base de datos detrás de cada clic."),
  ...figura("app_ver_cypher", "Panel «Ver Cypher» con las consultas reales del feed."),
  H2("6.8 Seguridad"),
  B("Contraseñas con hash (PBKDF2) y bloqueo temporal tras 8 intentos fallidos de inicio de sesión."),
  B("Token CSRF en todos los formularios; la sesión expira a los 7 días."),
  B("Consultas siempre parametrizadas; la consola del panel abre la sesión en modo **solo lectura**, así que Neo4j rechaza `CREATE`, `SET` o `DELETE` desde allí."),
  B("Reglas de negocio en el propio patrón Cypher: solo se escribe a contactos, solo el autor borra su publicación y solo quien trabaja en la empresa ve a sus postulantes."),
  B("Archivos subidos con nombre aleatorio, extensiones permitidas (imágenes y videos) y tamaño máximo de 80 MB."),
  H2("6.9 Versión móvil"),
  P("La interfaz se adapta al celular: la barra de secciones pasa a la parte inferior y las columnas se apilan. En pantallas táctiles, mantener presionado «Recomendar» abre la paleta de reacciones."),
  ...figura("app_movil", "UniRed en un celular.", 260),
  H2("6.10 Puesta en marcha y publicación"),
  P("No se usan contenedores. En el PC del equipo, Neo4j Community 5.26 corre en modo portable desde `D:\\neo4j_local` con su propio Java 21. Para encender todo:"),
  N("Doble clic en `iniciar.bat` (carpeta del proyecto). Enciende Neo4j, la aplicación (waitress en el puerto 8000) y un túnel de Cloudflare."),
  N("El script muestra el **enlace público https** (también queda copiado y guardado en `LINK_PUBLICO.txt`). Con él se entra desde cualquier computador o celular. El enlace cambia cada vez que se enciende."),
  N("`detener.bat` apaga todo. Para reiniciar los datos de ejemplo: `python cargar_datos.py --reset`."),
  P("Instalación desde cero en otro equipo: `pip install -r requirements.txt`, copiar `.env.example` como `.env` con la URI, el usuario y la contraseña de Neo4j (y `ADMIN_PASSWORD`), ejecutar `python cargar_datos.py` y luego `python app.py` (desarrollo) o `python servidor.py` (producción)."),
  H2("6.11 Ver la base de datos en Neo4j Browser"),
  P("Neo4j Browser cumple el papel que tiene MySQL Workbench en el modelo relacional. Con Neo4j encendido se abre `http://localhost:7474` y se conecta con la URL `neo4j://localhost:7687`, el usuario `neo4j` y la contraseña configurada. Las consultas se escriben en la barra superior y se ejecutan con Ctrl+Enter; cada resultado puede verse como **Graph**, **Table** o **Text**."),
  tabla(["En Workbench (MySQL)", "En Neo4j Browser"], [
    ["Ver las tablas", "Ícono de base de datos: etiquetas, tipos de relación y propiedades (clic para consultarlas)"],
    ["SELECT * FROM usuario", "`MATCH (u:Usuario) RETURN u`"],
    ["Diagrama EER", "`CALL db.schema.visualization()`"],
    ["Ver todo", "`MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 150`"],
  ], [3200, 6160]),
  ESP(),
  ...figura("neo4j_esquema", "CALL db.schema.visualization() en Neo4j Browser: el modelo real guardado en la base."),
  ...figura("neo4j_tabla", "Consulta en Neo4j Browser con resultado en tabla y la red de contactos como grafo."),
);

// ---------- 7 ----------
c.push(
  H1("7. Componente de investigación: grafos frente a relacional"),
  H2("7.1 El problema de los JOIN"),
  P("En un esquema relacional, la red de contactos se modela con una tabla de usuarios y una tabla intermedia `conexion(usuario_a, usuario_b)`. Obtener «los contactos de mis contactos» exige un auto-JOIN, y cada nivel adicional agrega otro:"),
  ...codigo("-- Amigos de amigos de amigos (3 niveles) en SQL\nSELECT DISTINCT u3.nombre\nFROM conexion c1\nJOIN conexion c2 ON c2.usuario_a = c1.usuario_b\nJOIN conexion c3 ON c3.usuario_a = c2.usuario_b\nJOIN usuario  u3 ON u3.id = c3.usuario_b\nWHERE c1.usuario_a = 1;"),
  ...codigo("// Mismo problema en Cypher: la profundidad es un parámetro\nMATCH (:Usuario {id:'u1'})-[:CONECTA_CON*3]-(x:Usuario)\nRETURN DISTINCT x.nombre;"),
  P("El número de filas intermedias en SQL crece de forma combinatoria con la profundidad y la consulta debe reescribirse para cada nivel. Para el camino más corto sin límite conocido se necesita una consulta recursiva (`WITH RECURSIVE`), más difícil de escribir, de optimizar y de leer. En el grafo, `shortestPath` es una operación nativa. En UniRed esto se nota en «Cómo llegas a…», que se calcula en cada visita a un perfil."),
  H2("7.2 Cuándo el modelo de grafos supera al relacional"),
  tabla(["Escenario", "Por qué el grafo gana"], [
    ["Recorridos de profundidad variable (amigos de amigos, rutas, dependencias)", "Recorrer una relación es un salto de puntero; el costo depende del subgrafo visitado, no del tamaño total"],
    ["Relaciones muchos-a-muchos y heterogéneas (usuario–habilidad–oferta–empresa)", "Cada tipo de relación es de primera clase, sin tablas intermedias ni JOIN encadenados"],
    ["Recomendación y similitud basadas en estructura", "Los patrones (triángulos, vecinos compartidos) se expresan directamente"],
    ["Análisis de redes: centralidad, comunidades, caminos", "Existen algoritmos y librerías (GDS) que operan sobre la estructura nativa"],
    ["Esquema cambiante", "Agregar un tipo de relación o de propiedad no exige migraciones (ALTER TABLE). La capa social de UniRed se añadió sin tocar los nodos del enunciado"],
    ["Consultas «exploratorias» con el patrón visual", "Cypher describe el patrón que se dibuja en la pizarra"],
  ], [3800, 5560]),
  ESP(),
  H2("7.3 Cuándo no conviene (o el relacional es mejor)"),
  tabla(["Escenario", "Por qué el relacional gana"], [
    ["Agregaciones masivas sobre toda la tabla (sumas, promedios, reportes contables)", "Los motores relacionales y columnares están optimizados para escaneos y GROUP BY a gran escala"],
    ["Datos tabulares sin relaciones relevantes (inventario, nómina)", "El grafo no aporta; añade complejidad"],
    ["Transacciones con integridad muy estricta entre muchas entidades", "El modelo relacional ofrece claves foráneas, CHECK y normalización con garantías declarativas maduras (Neo4j Community solo ofrece unicidad)"],
    ["Escalado horizontal (sharding) de grandes volúmenes", "Particionar un grafo es difícil porque las consultas cruzan particiones"],
    ["Ecosistema y habilidades del equipo", "SQL es un estándar con mayor soporte de herramientas, BI y personal"],
    ["Consultas que tocan casi todo el grafo", "Si cada consulta recorre la mayoría de los nodos, la ventaja de la adyacencia se pierde"],
  ], [3800, 5560]),
  ESP(),
  H2("7.4 Aplicado a este proyecto"),
  P("En la red profesional las preguntas centrales (contactos en común, rutas hacia una empresa, candidatos según competencias y conexiones, proyectos relacionados, personas que quizá conozcas) son recorridos sobre relaciones múltiples, justo donde el grafo es natural. En cambio, un reporte como «salario promedio por ciudad y mes» sería una agregación tabular en la que un motor relacional rendiría igual o mejor. Algo parecido ocurre con los mensajes: son registros temporales que se consultan por fecha y se borran en lote, y un motor relacional los manejaría con la misma comodidad. En un sistema real la elección puede ser híbrida (persistencia políglota): relacional para datos transaccionales y contables, y grafo para la capa de relaciones y recomendación."),
  H2("7.5 Comparación breve"),
  tabla(["Criterio", "Grafos (Neo4j)", "Relacional (SQL)"], [
    ["Modelo", "Nodos y relaciones con propiedades", "Tablas, filas y claves foráneas"],
    ["Relaciones", "Primera clase, sin JOIN", "Se reconstruyen con JOIN"],
    ["Consulta de caminos", "Nativa (shortestPath, [*n..m])", "WITH RECURSIVE, costosa"],
    ["Esquema", "Flexible", "Rígido (migraciones)"],
    ["Agregaciones masivas", "Aceptables", "Muy optimizadas"],
    ["Integridad", "Restricciones básicas", "Muy completa y declarativa"],
    ["Escalado horizontal", "Complejo", "Variable, madura en muchos motores"],
  ], [2400, 3480, 3480]),
  ESP(),
  P("Nota: la comparación es cualitativa. No se realizó un benchmark de tiempos; puede medirse cargando un grafo sintético grande y comparando una consulta de 3 a 5 niveles en Cypher frente a su equivalente en SQL."),
);

// ---------- 8, 9 ----------
c.push(
  H1("8. Guion de la demostración (15 min)"),
  tabla(["Minutos", "Segmento", "Qué mostrar"], [
    ["0–2", "Contexto y modelo", "Logo animado; figura del modelo; por qué un grafo"],
    ["2–4", "Base de datos", "Neo4j Browser: `CALL db.schema.visualization()` y el grafo; Panel › Base de datos"],
    ["4–8", "UniRed como usuario", "Sebastián Mora: feed, reaccionar, comentar, publicar, aceptar invitación, perfil con «Cómo llegas a…», empleos, chat en vivo con Tomás"],
    ["8–12", "Panel de administración", "CRUD de un usuario; las seis consultas (ruta más corta, candidatos); recomendaciones; analítica. «Ver Cypher» en cada paso"],
    ["12–15", "Grafos vs. relacional", "Amigos de amigos en SQL frente a Cypher; cuándo no usar grafos; conclusiones"],
  ], [1300, 2600, 5460]),
  ESP(),
  P("Recomendación: encender con `iniciar.bat` antes de la presentación, ensayar con un reinicio limpio de los datos y tener Neo4j Browser abierto en otra pestaña. Las cuentas de la demo están en un documento aparte de uso interno del equipo."),
  H1("9. Conclusiones"),
  B("El modelo de grafo de propiedades permitió representar de forma directa las cinco entidades y las relaciones del enunciado, y las consultas de caminos, similitud y recomendación se expresan con patrones breves."),
  B("La capa social (publicaciones, reacciones, comentarios, invitaciones, estudios y mensajes) se agregó sin modificar el núcleo del modelo, lo que muestra la flexibilidad de esquema del grafo."),
  B("Cypher reduce la complejidad de las consultas de profundidad variable frente a los JOIN encadenados o recursivos de SQL; funciones como `shortestPath` y las subconsultas `COUNT { }` resuelven en una consulta lo que en SQL requiere varias."),
  B("Modelar bien el significado de cada relación importa: una invitación pendiente no es una conexión, y por eso los recorridos se restringen a los tipos de relación que tienen sentido para cada pregunta."),
  B("El grafo no sustituye al modelo relacional en agregaciones masivas ni en integridad transaccional compleja; una arquitectura híbrida suele ser la mejor opción."),
  B("Pendientes recomendados: pruebas de rendimiento con un grafo mayor, notificaciones en tiempo real y uso de GDS para analítica a mayor escala."),
  H1("Referencias"),
  B("Neo4j. Cypher Manual. https://neo4j.com/docs/cypher-manual/current/"),
  B("Neo4j. Operations Manual: constraints and indexes. https://neo4j.com/docs/"),
  B("Robinson, I., Webber, J., Eifrem, E. (2015). Graph Databases (2.ª ed.). O'Reilly Media."),
  B("Hagberg, A., Schult, D., Swart, P. NetworkX documentation. https://networkx.org/"),
  B("Pallets. Flask documentation. https://flask.palletsprojects.com/"),
);

// ---------- anexos ----------
const anexos = [
  ["Anexo A. 01_schema.cypher", "scripts/01_schema.cypher"],
  ["Anexo B. 02_seed.cypher", "scripts/02_seed.cypher"],
  ["Anexo C. 03_queries.cypher", "scripts/03_queries.cypher"],
  ["Anexo D. 04_red_social.cypher", "scripts/04_red_social.cypher"],
];
for (const [titulo, f] of anexos) c.push(SALTO(), H1(titulo), ...codigo(leer(f)));

// =============================================================== documento
const doc = new Document({
  creator: "Equipo UniRed", title: "Proyecto I+D: red profesional sobre Neo4j (UniRed)",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: "1E1E1E", font: "Segoe UI Semibold" },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0, keepNext: true,
          border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ROJO, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: ROJO, font: "Segoe UI Semibold" },
        paragraph: { spacing: { before: 260, after: 100 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, color: "1E1E1E" }, paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: "vinetas", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 270 } } } }, { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 1080, hanging: 270 } } } }] },
    { reference: "numeros", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "UniRed · Proyecto I+D Bases de Datos · ", size: 17, color: GRIS }),
        new TextRun({ children: [PageNumber.CURRENT], size: 17, color: GRIS })] })] }) },
    children: c,
  }],
});
const salida = path.join(RAIZ, "Proyecto_Grafos_Red_Profesional.docx");
Packer.toBuffer(doc).then(b => { fs.writeFileSync(salida, b); console.log("ok", salida, b.length); });
