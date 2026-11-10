# UniRed: red profesional sobre Neo4j

Proyecto de Investigación (I+D) de Bases de Datos, Universidad del Norte.
Docente: Wilson Estrada Bernal.
Equipo: Mateo Gómez, Valerie Angulo, Sahory Blanco, Sebastián Corbacho y Cristian Viloria.

UniRed es una red profesional tipo LinkedIn hecha en **Python + Flask** sobre **Neo4j** (driver oficial `neo4j`, sin Docker).
Tiene dos partes:

- **Red social** para usuarios: registro e inicio de sesión, feed con fotos y videos, 6 reacciones, comentarios, perfil con estudios, habilidades y trabajo, solicitudes de conexión, «Cómo llegas a…» (ruta más corta), empleos con % de ajuste, mensajes que se borran a las 24 h y notificaciones.
- **Panel de administrador** (`/admin`): todo lo que pide el enunciado (CRUD, relaciones, las 6 consultas, recomendaciones, analítica) más una consola Cypher de solo lectura, el grafo completo y moderación. Cada pantalla tiene el botón **Ver Cypher**, que muestra las consultas que acaba de ejecutar.

## Estructura
| Ruta | Contenido |
|---|---|
| `scripts/01_schema.cypher` | Restricciones e índices |
| `scripts/02_seed.cypher` | Datos de ejemplo (usuarios, empresas, habilidades, proyectos, ofertas) |
| `scripts/03_queries.cypher` | CRUD, relaciones, preguntas del enunciado, recomendaciones y analítica |
| `scripts/04_red_social.cypher` | Instituciones, estudios, publicaciones, reacciones, comentarios, invitaciones y mensajes |
| `app/db.py` | Consultas del enunciado (panel de administrador) |
| `app/red.py` | Consultas de la red social |
| `app/app.py`, `app/rutas_red.py`, `app/rutas_admin.py` | Rutas Flask |
| `app/cargar_datos.py` | Carga esquema y datos (`--reset` borra todo el grafo) |
| `app/servidor.py` | Servidor de producción (waitress en el puerto 8000) |
| `iniciar.bat` / `detener.bat` | Encienden/apagan Neo4j, la app y el túnel público de Cloudflare |
| `docs/` | Generador del documento Word y capturas |
| `video/` | Guion y scripts que grabaron y montaron el video explicativo |
| `Proyecto_Grafos_Red_Profesional.docx/.pdf` | Documento del proyecto |

## Cómo correrlo

### 1. Neo4j 5.x
- **Neo4j Desktop**: crea un DBMS local con la contraseña que quieras (la misma va en `NEO4J_PASSWORD` de `.env`) y dale Start. Queda en `bolt://localhost:7687`.
- **AuraDB Free**: crea una instancia en https://console.neo4j.io y copia URI, usuario y contraseña en `app/.env`.

### 2. La aplicación
```bash
cd app
python -m venv venv
venv\Scripts\activate                # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # macOS/Linux: cp .env.example .env, y edítalo
python cargar_datos.py               # esquema + datos de ejemplo
python app.py                        # http://localhost:5000
```

Entra con `admin@unired.co` y la clave que pusiste en `ADMIN_PASSWORD`, o con un usuario de ejemplo (por ejemplo `sebastian@mail.com`) y la clave que pusiste en `CLAVE_DEMO`.

### 3. Ver la base en Neo4j Browser
Abre Neo4j Browser (http://localhost:7474 o *Open* en Desktop), conéctate a `bolt://localhost:7687` y prueba:
```cypher
CALL db.schema.visualization();
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 300;
```
Las consultas del enunciado están en `scripts/03_queries.cypher`.

### Publicarla en internet (opcional)
`iniciar.bat` asume Neo4j portable en `D:\neo4j_local` con `cloudflared.exe`; abre un túnel temporal de Cloudflare y deja el link en `LINK_PUBLICO.txt`. Ajusta las rutas de `iniciar.ps1` si tu instalación está en otro lugar.
