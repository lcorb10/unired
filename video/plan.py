"""Guion del video explicativo de UniRed (≈13 min).

Cada escena tiene un tipo visual:
  "anim"   -> animación HTML propia (video/escenas/<id>.html) grabada en tiempo real
  "app"    -> grabación de la app o de Neo4j Browser (video/grabar.py, función <id>)
y una lista de líneas de narración (texto tal como se muestra en subtítulos).
La pronunciación para la voz se ajusta con PRONUNCIA.
"""

VOZ = "9cbe708a"  # perfil «Narrador UniRed» en VoiceStudio (muestra A)

PRONUNCIA = [  # (texto en pantalla, cómo debe decirlo la voz)
    ("Neo4j", "Neo for yei"), ("Cypher", "Sáifer"), ("UniRed", "Uni Red"), ("Uninorte", "Uninorte"),
    ("CONECTA_CON", "conecta con"), ("TRABAJA_EN", "trabaja en"), ("TIENE_HABILIDAD", "tiene habilidad"),
    ("PARTICIPA_EN", "participa en"), ("POSTULA_A", "postula a"), ("USA_TECNOLOGIA", "usa tecnología"),
    ("SOLICITA_CONEXION", "solicita conexión"), ("ESTUDIO_EN", "estudió en"), ("REACCIONO", "reaccionó"),
    ("REQUIERE", "requiere"), ("PUBLICA", "publica"), ("shortestPath", "shortest path"),
    ("DETACH DELETE", "détach delít"), ("MERGE", "merch"), ("MATCH", "match"), ("JOIN", "yoin"),
    ("SQL", "ese cu ele"), ("Flask", "Flask"), ("PageRank", "Page Rank"), ("networkx", "network ex"),
    ("Jaccard", "Yacar"), ("Workbench", "Workbench"), ("localhost", "local host"), ("CSRF", "ce ese erre efe"),
    ("1.º", "primer grado"), ("2.º", "segundo grado"), ("3.º", "tercer grado"), ("24 h", "24 horas"),
    ("Cloudflare", "Cloudflare"), ("waitress", "waitress"), ("vis-network", "vis network"), ("db.schema.visualization", "de be punto esquema punto visualización"),
]

ESCENAS = [
    {"id": "s01_intro", "tipo": "anim", "lineas": [
        "Esto es UniRed: una red profesional construida sobre Neo4j, una base de datos orientada a grafos.",
        "Es nuestro proyecto de investigación y desarrollo para Bases de Datos en la Universidad del Norte.",
        "En los próximos minutos vamos a explicar qué es una base de datos de grafos, cómo modelamos la red, qué scripts y consultas usamos, y cómo se ve todo funcionando.",
    ]},
    {"id": "s02_reto", "tipo": "anim", "lineas": [
        "El enunciado pedía una aplicación para gestionar una red profesional: usuarios, empresas, habilidades, proyectos y ofertas laborales.",
        "La aplicación debía permitir el CRUD de usuarios, conectarlos entre sí, vincularlos con habilidades, empresas y proyectos, publicar ofertas y postularse a ellas.",
        "Además debía consultar caminos entre usuarios y empresas, generar recomendaciones y mostrar un panel de analítica con los usuarios más influyentes, las comunidades y las habilidades más demandadas.",
        "Y como componente de investigación, explicar en qué casos el modelo de grafos supera al relacional y en cuáles no.",
    ]},
    {"id": "s03_grafos", "tipo": "anim", "lineas": [
        "Una base de datos de grafos guarda la información como nodos y relaciones.",
        "Los nodos son las entidades, por ejemplo un usuario o una empresa, y llevan una etiqueta y propiedades.",
        "Las relaciones conectan dos nodos, tienen dirección, un tipo, y también pueden tener propiedades, como la fecha desde la que dos personas se conocen.",
        "Lo que hace especial a Neo4j es la adyacencia sin índices: cada nodo apunta directamente a sus relaciones. Recorrer una conexión cuesta lo mismo sin importar cuántos datos haya en total.",
        "Para consultarla se usa Cypher, un lenguaje que dibuja el patrón que buscas: los nodos van entre paréntesis y las relaciones entre corchetes, con una flecha que indica la dirección.",
    ]},
    {"id": "s04_modelo", "tipo": "anim", "lineas": [
        "Este es nuestro modelo. En el centro está el Usuario.",
        "Del enunciado tomamos las cinco entidades: Usuario, Empresa, Habilidad, Proyecto y Oferta, con sus relaciones: CONECTA_CON, TRABAJA_EN, TIENE_HABILIDAD, PARTICIPA_EN, PUBLICA, REQUIERE y POSTULA_A.",
        "Agregamos USA_TECNOLOGIA, entre proyecto y habilidad, para poder responder qué proyectos comparten tecnologías.",
        "Y encima construimos una capa social, en rojo: publicaciones, reacciones, comentarios, invitaciones de conexión, estudios en instituciones y mensajes.",
        "Algunas decisiones importantes: la habilidad es un nodo y no un texto, así conecta usuarios, ofertas y proyectos. El nivel de una habilidad o el estado de una postulación viven en la relación, porque pertenecen al vínculo y no a uno de los nodos.",
        "Y una invitación pendiente es una relación distinta de una conexión: solo cuando se acepta se convierte en CONECTA_CON.",
    ]},
    {"id": "s05_scripts", "tipo": "anim", "lineas": [
        "La base se crea con cuatro scripts en Cypher.",
        "El primero define las restricciones de unicidad: el id de cada nodo y el correo del usuario no se pueden repetir. Eso además crea índices que aceleran las búsquedas.",
        "El segundo carga los datos de ejemplo: veinte usuarios, seis empresas, dieciséis habilidades, ocho proyectos y diez ofertas, con todas sus relaciones.",
        "El tercero reúne todas las consultas: el CRUD, las relaciones, las seis preguntas del enunciado, las recomendaciones y la analítica.",
        "Y el cuarto carga la capa social. Todo usa MERGE, así que se puede ejecutar varias veces sin duplicar nada.",
    ]},
    {"id": "s06_browser", "tipo": "app", "lineas": [
        "Para ver la base de datos usamos Neo4j Browser, que cumple el papel que tiene Workbench en MySQL.",
        "Se abre en localhost, puerto siete cuatro siete cuatro, y nos conectamos con el usuario neo4j y su contraseña.",
        "Con db.schema.visualization vemos el modelo real guardado en la base: las etiquetas y los tipos de relación que existen.",
        "Y con un MATCH podemos traer datos. Aquí, la red de contactos: cada círculo es un usuario y cada flecha, una relación CONECTA_CON.",
        "El mismo resultado se puede ver como tabla. Por ejemplo, los usuarios que estudiaron en la Universidad del Norte.",
        "Igual que en Workbench cuando abrimos una tabla, en el panel de la izquierda podemos hacer clic en cualquier etiqueta o tipo de relación para consultarla.",
    ]},
    {"id": "s07_arquitectura", "tipo": "anim", "lineas": [
        "La aplicación está hecha en Python con Flask, y se conecta a Neo4j con el controlador oficial.",
        "Todas las consultas reciben parámetros; nunca se pega texto del usuario dentro de la consulta, y eso evita la inyección de Cypher.",
        "Las contraseñas se guardan con hash, todos los formularios llevan un token CSRF, y los mensajes privados se borran solos a las veinticuatro horas para no llenar la base.",
        "Para publicarla, la servimos desde nuestro propio computador con waitress, y un túnel de Cloudflare nos da un enlace seguro que se abre desde cualquier celular.",
        "Para ponerla en marcha basta un doble clic en iniciar: enciende Neo4j, la aplicación y el túnel, y muestra el enlace público. Los datos de ejemplo se cargan con el script cargar datos, y con la opción reset se empieza de cero.",
    ]},
    {"id": "s08_feed", "tipo": "app", "lineas": [
        "Entremos como un usuario. Cualquiera puede crear su cuenta, y al iniciar sesión aparece la animación del logo mientras carga su red.",
        "Este es el inicio. A la izquierda, la tarjeta del usuario; en el centro, el feed con publicaciones de texto, fotos y videos; y a la derecha, personas que quizá conozcas y las habilidades más pedidas en las ofertas.",
        "Cada publicación admite seis reacciones. Al elegir una, se guarda como la propiedad tipo de la relación REACCIONO entre el usuario y la publicación.",
        "También podemos comentar: el comentario es un nodo que se conecta con quien lo escribió y con la publicación.",
        "Para publicar escribimos un texto y adjuntamos una foto o un video. La publicación queda conectada con su autor por la relación PUBLICO, y el archivo se guarda en el servidor.",
        "Y en cualquier pantalla, el botón Ver Cypher muestra las consultas reales que se ejecutaron, con sus parámetros. Aquí vemos la que armó este feed.",
    ]},
    {"id": "s09_perfil", "tipo": "app", "lineas": [
        "En el perfil vemos la experiencia, los estudios, las habilidades con su nivel y los proyectos.",
        "El perfil propio se edita desde aquí: los datos, la foto, los estudios, las habilidades con su nivel y la experiencia actual. Si la empresa no existe todavía, se crea con MERGE.",
        "Lo más interesante está en el perfil de otra persona: UniRed calcula en qué grado de conexión está, y el camino exacto de contactos que nos une, usando shortestPath sobre CONECTA_CON.",
        "En Mi red están las invitaciones. Al aceptar una, la relación SOLICITA_CONEXION se borra y se crea una CONECTA_CON.",
        "Y las sugerencias salen de recorrer el grafo: contactos en común, la misma universidad o habilidades compartidas, cada una con su peso.",
    ]},
    {"id": "s10_empleos", "tipo": "app", "lineas": [
        "En Empleos, las ofertas abiertas se ordenan por ajuste: qué porcentaje de las habilidades que pide la oferta tiene el usuario. Las que ya tiene aparecen resaltadas.",
        "También indica cuántos de sus contactos trabajan en esa empresa. Postularse crea la relación POSTULA_A con el estado en revisión.",
        "Y quien trabaja en una empresa puede publicar ofertas desde la página de la empresa, elegir las habilidades requeridas y ver a sus postulantes.",
        "Las notificaciones tampoco se guardan aparte: se calculan con una sola consulta que une las reacciones, los comentarios y las invitaciones que apuntan al usuario.",
    ]},
    {"id": "s11_mensajes", "tipo": "app", "lineas": [
        "Los mensajes funcionan en vivo, solo entre contactos: la consulta exige que exista la relación CONECTA_CON para poder escribir.",
        "Cuando el otro responde, el mensaje aparece sin recargar la página.",
        "Y cada diez minutos la aplicación borra los mensajes con más de veinticuatro horas.",
    ]},
    {"id": "s12_admin_base", "tipo": "app", "lineas": [
        "Ahora el panel de administración, donde está todo lo que pide el enunciado.",
        "La sección Base de datos muestra cuántos nodos hay de cada etiqueta y cuántas relaciones de cada tipo, con su origen y su destino.",
        "Tiene una consola Cypher de solo lectura: podemos ejecutar consultas y, si el resultado trae nodos, también se dibuja. Si alguien intenta borrar o crear algo, Neo4j lo rechaza.",
        "Y más abajo, el grafo completo de la red, que se puede mover y explorar.",
    ]},
    {"id": "s13_admin_crud", "tipo": "app", "lineas": [
        "En Usuarios está el CRUD: crear, consultar, editar y eliminar.",
        "Al eliminar se usa DETACH DELETE, que borra el nodo junto con todas sus relaciones.",
        "En Relaciones se conectan usuarios y se les asignan habilidades, empresas y proyectos. Y en Ofertas se publican vacantes con sus habilidades requeridas.",
    ]},
    {"id": "s14_consultas", "tipo": "app", "lineas": [
        "Estas son las seis preguntas del enunciado.",
        "Primera: usuarios con habilidades similares. Recorremos usuario, habilidad, usuario, y calculamos el índice de Jaccard: habilidades compartidas sobre el total de ambos.",
        "Fíjense en el panel Ver Cypher: es exactamente la consulta del script de consultas, con los identificadores pasados como parámetros.",
        "Segunda: contactos en común entre dos profesionales, un patrón de dos saltos con un nodo en el medio.",
        "Tercera: la ruta más corta entre un usuario y una empresa, que además se dibuja. Solo recorre relaciones profesionales; una invitación pendiente no cuenta como camino.",
        "Cuarta: candidatos para una oferta. El puntaje combina setenta por ciento de habilidades cumplidas y treinta por ciento de contactos dentro de la empresa.",
        "Quinta: proyectos que comparten tecnologías o miembros. Y sexta: las habilidades más demandadas en las ofertas abiertas, comparadas con cuántos profesionales las tienen.",
    ]},
    {"id": "s15_analitica", "tipo": "app", "lineas": [
        "En Recomendaciones, para cualquier usuario, vemos contactos sugeridos por amigos en común, empleos según sus habilidades y colaboradores que trabajan con tecnologías parecidas.",
        "Y la analítica muestra los usuarios más influyentes, por número de conexiones y por PageRank, las habilidades más demandadas con su brecha de talento, y las comunidades detectadas en la red de contactos con networkx.",
        "Las comunidades se calculan leyendo las relaciones CONECTA_CON desde Neo4j y buscando grupos muy conectados entre sí. Con el complemento Graph Data Science, lo mismo se haría con el algoritmo de Louvain dentro de la base.",
    ]},
    {"id": "s16_relacional", "tipo": "anim", "lineas": [
        "Ahora, el componente de investigación: ¿cuándo conviene un grafo y cuándo no?",
        "Si queremos los amigos de los amigos de los amigos en SQL, necesitamos un JOIN por cada nivel, y la consulta crece con la profundidad. En Cypher, la profundidad es solo un número dentro del patrón.",
        "Por eso el grafo gana en recorridos de profundidad variable, en relaciones muchos a muchos, en recomendaciones por estructura y en análisis de redes. Además, el esquema es flexible: agregamos toda la capa social sin migrar nada.",
        "Pero el relacional sigue ganando en agregaciones masivas, como reportes contables, en datos tabulares sin relaciones importantes, en integridad transaccional estricta y en escalado horizontal.",
        "Por eso, en un sistema real, lo mejor suele ser combinar ambos: relacional para lo transaccional y grafos para la capa de relaciones y recomendaciones.",
    ]},
    {"id": "s17_cierre", "tipo": "anim", "lineas": [
        "En resumen: modelamos la red profesional como un grafo, respondimos las seis preguntas del enunciado con Cypher, y construimos UniRed, una aplicación completa que lo muestra funcionando.",
        "Y aprendimos algo clave: modelar bien el significado de cada relación es tan importante como los datos. Una invitación no es una conexión, y una reacción guarda su tipo en el vínculo.",
        "Este fue el proyecto de Mateo Gómez, Valerie Angulo, Sahory Blanco, Sebastián Corbacho y Cristian Viloria, para la clase del profesor Wilson Estrada Bernal. Gracias por vernos.",
    ]},
]


def para_voz(texto):
    for a, b in PRONUNCIA:
        texto = texto.replace(a, b)
    return texto


if __name__ == "__main__":
    palabras = sum(len(l.split()) for e in ESCENAS for l in e["lineas"])
    print(len(ESCENAS), "escenas,", sum(len(e["lineas"]) for e in ESCENAS), "líneas,", palabras, "palabras ≈",
          round(palabras / 160, 1), "min de voz")
