import os
import json
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spec-ide-backend")

# Cargar variables de entorno desde un archivo .env si existe
def load_dotenv():
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(dotenv_path):
        logger.info("Cargando variables desde archivo .env local")
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        os.environ[key] = val

load_dotenv()

app = FastAPI(title="Spec IDE Backend")

PROJECT_FILE = "project.json"
SPECS_DIR = "specs"

class IdeaAnalysisRequest(BaseModel):
    idea: str

class NextQuestionsRequest(BaseModel):
    idea: str
    answers: Dict[str, Any]

class SaveProjectRequest(BaseModel):
    project_data: Dict[str, Any]

class DiagramRequest(BaseModel):
    diagram_type: str  # 'er', 'flow', 'architecture'
    answers: Dict[str, Any]

class CopilotRequest(BaseModel):
    prompt: str
    activeFile: str
    projectData: Dict[str, Any]

# Helper para configurar Gemini y obtener el modelo
def get_gemini_model(api_key: str):
    key_to_use = api_key.strip() if api_key else ""
    if not key_to_use:
        key_to_use = os.environ.get("GEMINI_API_KEY", "").strip()
        
    if not key_to_use:
        raise HTTPException(
            status_code=401, 
            detail="Falta la API Key de Gemini. Configúrala en la interfaz web o mediante la variable de entorno GEMINI_API_KEY."
        )
    try:
        genai.configure(api_key=key_to_use)
        # Usamos gemini-2.5-flash para velocidad y consistencia en el año 2026
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        logger.error(f"Error al configurar la API de Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de configuración de IA: {str(e)}")

# Servir archivos estáticos del frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Endpoints de la API

@app.get("/api/config")
async def get_config():
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    return {"hasApiKey": has_key}

@app.post("/api/analyze-idea")
async def analyze_idea(req: IdeaAnalysisRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    
    prompt = f"""
    Eres un Staff Software Architect y Product Designer.
    Analiza la siguiente idea de software y extrae información clave estructurada en formato JSON válido.
    
    Idea del usuario: "{req.idea}"
    
    Debes devolver ÚNICAMENTE un objeto JSON con las siguientes claves (no uses markdown, no incluyas texto antes o después del JSON):
    {{
        "domain": "Dominio principal del producto (ej: E-commerce, EdTech, FinTech)",
        "productType": "Tipo de producto (ej: Web SPA, SaaS, Mobile App)",
        "actors": ["Actor 1", "Actor 2", "..."],
        "detectedFeatures": ["Funcionalidad 1", "Funcionalidad 2", "..."],
        "risks": ["Riesgo 1", "Riesgo 2", "..."],
        "uncertainties": ["Incertidumbre 1", "Incertidumbre 2", "..."],
        "questions": [
            {{
                "id": "q_auth",
                "section": "Seguridad",
                "label": "¿Qué tipo de autenticación y roles de usuario necesitas para los actores definidos?",
                "type": "select",
                "options": ["Email y Contraseña tradicional", "OAuth (Google, Github)", "Autenticación sin contraseña (Magic Links)", "Múltiples Roles complejos"]
            }},
            {{
                "id": "q_database",
                "section": "Arquitectura",
                "label": "¿Tienes alguna preferencia de base de datos?",
                "type": "select",
                "options": ["Relacional (PostgreSQL/MySQL)", "No-Relacional (MongoDB/Firestore)", "A decidir con la IA"]
            }},
            {{
                "id": "q_features_core",
                "section": "Producto",
                "label": "Describe brevemente las 2 funcionalidades más críticas que debe tener el MVP:",
                "type": "text"
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Error al analizar la idea: {str(e)}")
        # Fallback local simulado en caso de error o límite de cuota
        return {
            "domain": "Por definir",
            "productType": "Web App",
            "actors": ["Usuario final", "Administrador"],
            "detectedFeatures": ["Inicio de sesión", "Gestión básica"],
            "risks": ["Especificación incompleta"],
            "uncertainties": ["Falta definir arquitectura"],
            "questions": [
                {
                    "id": "q_fallback_1",
                    "section": "General",
                    "label": "Hubo un problema al contactar a la IA. Ingresa el objetivo principal de la app:",
                    "type": "text"
                }
            ]
        }

@app.post("/api/next-questions")
async def next_questions(req: NextQuestionsRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    
    prompt = f"""
    Eres un Tech Lead e Ingeniero de Requisitos.
    Analiza la idea del proyecto y las respuestas actuales del usuario, y genera un conjunto dinámico de 3 a 5 preguntas adicionales más profundas para completar las secciones técnicas (Arquitectura, Base de datos, API, Seguridad, UX, etc.).
    
    Idea del proyecto: "{req.idea}"
    Respuestas actuales: {json.dumps(req.answers, ensure_ascii=False)}
    
    Genera preguntas condicionales según el contexto (por ejemplo, si mencionan cobros pregunta por pasarelas, si mencionan roles pregunta por permisos, si mencionan datos masivos pregunta por escalabilidad o base de datos).
    
    Devuelve ÚNICAMENTE un objeto JSON con la siguiente estructura (sin markdown, solo el JSON):
    {{
        "questions": [
            {{
                "id": "id_pregunta_unica",
                "section": "Nombre de la sección (ej. API, Base de datos, Calidad)",
                "label": "Texto de la pregunta",
                "type": "text | select | boolean",
                "options": ["Opción 1", "Opción 2"] // Solo si el tipo es select
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error en next-questions: {str(e)}")
        return {"questions": []}

@app.post("/api/generate-diagram")
async def generate_diagram(req: DiagramRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    
    prompt = f"""
    Eres un Arquitecto de Software experto.
    Genera un diagrama en formato Mermaid.js para el tipo de diagrama '{req.diagram_type}'.
    
    Respuestas del proyecto: {json.dumps(req.answers, ensure_ascii=False)}
    
    Tipos de diagramas esperados:
    - 'er': Diagrama de Entidad Relación (erDiagram) con entidades principales, atributos y relaciones.
    - 'flow': Diagrama de Flujo del caso de uso principal (graph TD/LR).
    - 'architecture': Diagrama conceptual de arquitectura e infraestructura (servicios, cliente, base de datos).
    
    Instrucciones críticas:
    1. Devuelve únicamente el código de Mermaid listo para ser renderizado.
    2. No encierres el código en bloques de código markdown (como ```mermaid). Solo devuelve el texto del código de Mermaid directamente.
    3. Asegúrate de usar sintaxis correcta de Mermaid.
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpiar posibles bloques markdown si la IA no siguió la regla estricta
        code = response.text.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```mermaid") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines).strip()
        return {"code": code}
    except Exception as e:
        logger.error(f"Error generando diagrama Mermaid: {str(e)}")
        return {"code": "graph TD\n  A[Error al generar el diagrama] --> B[Verifica tu API Key]"}

@app.post("/api/check-consistency")
async def check_consistency(req: SaveProjectRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    
    prompt = f"""
    Eres un QA Lead y Arquitecto de Software.
    Evalúa la consistencia de las respuestas y decisiones de la especificación técnica de este proyecto.
    
    Datos del proyecto: {json.dumps(req.project_data, ensure_ascii=False)}
    
    Busca contradicciones, inconsistencias de seguridad, arquitectura o requisitos funcionales faltantes.
    Por ejemplo, si la base de datos es NoSQL pero se habla de joins complejos, o si hay pagos pero no se especifica HTTPS/seguridad.
    
    Devuelve ÚNICAMENTE una lista de advertencias en formato JSON (sin markdown):
    {{
        "warnings": [
            {{
                "severity": "critical | warning | info",
                "section": "Sección afectada (ej: Seguridad, Base de datos)",
                "message": "Descripción detallada de la inconsistencia",
                "suggestion": "Cómo solucionarlo o qué preguntar para resolverlo"
            }}
        ]
    }}
    """
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error evaluando consistencia: {str(e)}")
        return {"warnings": [{"severity": "info", "section": "Sistema", "message": "No se pudo realizar el análisis automático de consistencia.", "suggestion": "Inténtalo de nuevo más tarde."}]}

@app.post("/api/save-project")
async def save_project(req: SaveProjectRequest):
    try:
        with open(PROJECT_FILE, "w", encoding="utf-8") as f:
            json.dump(req.project_data, f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": "Proyecto guardado localmente"}
    except Exception as e:
        logger.error(f"Error al guardar proyecto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/load-project")
async def load_project():
    if not os.path.exists(PROJECT_FILE):
        return {"status": "empty", "project": None}
    try:
        with open(PROJECT_FILE, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        return {"status": "success", "project": project_data}
    except Exception as e:
        logger.error(f"Error al cargar el proyecto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export-specs")
async def export_specs(req: SaveProjectRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    
    # Creamos la carpeta de specs si no existe
    if not os.path.exists(SPECS_DIR):
        os.makedirs(SPECS_DIR)
        
    project = req.project_data
    answers = project.get("answers", {})
    metadata = project.get("metadata", {})
    idea = project.get("seedIdea", "")
    
    # Vamos a pedirle a Gemini que genere los contenidos de los archivos Markdown más críticos
    # Para ahorrar llamadas a la API, creamos plantillas base y rellenamos algunas con IA
    
    # Definimos la lista de archivos a generar
    files_to_generate = [
        "project.md", "product.md", "requirements.md", "user-stories.md",
        "architecture.md", "database.md", "api.md", "frontend.md",
        "backend.md", "security.md", "integrations.md", "roadmap.md",
        "tasks.md", "decisions.md", "glossary.md", "agents.md"
    ]
    
    generated_files = []
    
    # Hacemos una llamada grupal para obtener el esqueleto Markdown de los módulos principales
    prompt = f"""
    Eres un Staff Software Architect. Basándote en la idea: "{idea}" y las siguientes respuestas detalladas:
    {json.dumps(answers, ensure_ascii=False)}
    
    Genera el contenido en formato Markdown estructurado para los siguientes 4 archivos principales de especificaciones:
    1. product.md (Visión, Objetivos, Usuarios y Casos de uso)
    2. architecture.md (Pila tecnológica, Decisiones y Estructura)
    3. database.md (Entidades, Atributos y relaciones)
    4. api.md (Endpoints principales, autenticación y errores)
    
    Devuelve la información estructurada en el siguiente formato JSON estricto (no uses markdown en tu respuesta, solo el JSON):
    {{
        "product.md": "Contenido completo en Markdown...",
        "architecture.md": "Contenido completo en Markdown...",
        "database.md": "Contenido completo en Markdown...",
        "api.md": "Contenido completo en Markdown..."
    }}
    """
    
    ai_markdowns = {}
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        ai_markdowns = json.loads(response.text)
    except Exception as e:
        logger.error(f"Error generando contenido por IA para specs: {str(e)}")
        
    # Plantillas de fallback para los archivos
    for filename in files_to_generate:
        filepath = os.path.join(SPECS_DIR, filename)
        content = ""
        
        # Si fue generado por la IA, lo usamos
        if filename in ai_markdowns:
            content = ai_markdowns[filename]
        else:
            # Fallback o generación basada en reglas
            if filename == "project.md":
                content = f"""# Ficha Técnica del Proyecto: {project.get('name', 'Proyecto Spec-First')}

## Información General
*   **Idea Semilla:** {idea}
*   **Dominio:** {metadata.get('domain', 'No especificado')}
*   **Tipo de Producto:** {metadata.get('productType', 'No especificado')}
*   **Actores Detectados:** {", ".join(metadata.get('actors', []))}

## Resumen de Respuestas clave
{chr(10).join([f"*   **{k}:** {v}" for k, v in answers.items()])}

---
*Documento generado automáticamente por [Spec IDE](file://{os.path.abspath(__file__)}).*
"""
            elif filename == "requirements.md":
                content = f"""# Requisitos Funcionales y No Funcionales

## Requisitos Funcionales (RF)
A partir de la idea: *{idea}*
*   **RF-01 (Autenticación):** El sistema debe permitir a los actores ({", ".join(metadata.get('actors', []))}) iniciar sesión de forma segura.
*   **RF-02 (Core):** El sistema debe resolver la problemática central: "{idea}".
*   **RF-03 (Administración):** Se debe proveer un panel de control para gestionar recursos.

## Requisitos No Funcionales (RNF)
*   **RNF-01 (Seguridad):** Cifrado de datos en tránsito (TLS/HTTPS).
*   **RNF-02 (Rendimiento):** Tiempos de respuesta del backend inferiores a 300ms para endpoints CRUD.
*   **RNF-03 (Usabilidad):** Interfaz fluida y accesible que cumpla con los estándares WCAG 2.1 AA.
"""
            elif filename == "user-stories.md":
                content = f"""# Historias de Usuario (Specs)

## Historia 1: Acceso al Sistema
**Como** {metadata.get('actors', ['Usuario'])[0]}  
**Quiero** ingresar con mis credenciales al sistema  
**Para** poder acceder a mis recursos privados.

*   **Criterio de Aceptación 1:** Dado un usuario no registrado, cuando intenta ingresar, el sistema debe mostrar un error de credenciales.
*   **Criterio de Aceptación 2:** Dado un usuario registrado, cuando ingresa credenciales válidas, es redirigido al panel de control.

## Historia 2: Ejecución del Core
**Como** {metadata.get('actors', ['Usuario'])[0]}  
**Quiero** interactuar con la funcionalidad principal del software  
**Para** resolver mi necesidad de negocio.
"""
            elif filename == "frontend.md":
                content = f"""# Especificación Frontend

## Vistas del Sistema
1.  **Vista de Autenticación (Login):** Formulario limpio y accesible.
2.  **Dashboard Principal:** Vista de datos generales y accesos rápidos.
3.  **Detalle del Core:** Interfaz para interactuar con la lógica principal.

## Estándares de Estilo
*   **Tema:** Soporte de tema oscuro/claro.
*   **Alineación:** Diseño fluido y mobile-first.
"""
            elif filename == "backend.md":
                content = f"""# Especificación Backend

## Componentes y Servicios
*   **Servicio de API REST:** Procesa las solicitudes del frontend.
*   **Módulo de Base de Datos:** Capa de acceso a datos (ORM o consultas optimizadas).
*   **Capa de Autenticación:** Validación de tokens JWT / Sesiones.
"""
            elif filename == "security.md":
                content = f"""# Políticas de Seguridad y Roles

## Matriz de Control de Acceso (RBAC)
*   **Roles:** {", ".join(metadata.get('actors', ['Usuario']))}
*   **Políticas:**
    *   Cada rol tiene permisos limitados a sus propios recursos.
    *   Los administradores pueden gestionar todos los recursos.
"""
            elif filename == "integrations.md":
                content = f"""# Integraciones con Servicios de Terceros

## Servicios Identificados
*   **IA / LLM:** Google Gemini API (para flujos asistidos).
*   **Otros servicios:** A definir en las fases de desarrollo avanzadas.
"""
            elif filename == "roadmap.md":
                content = f"""# Planificación de Fases y Roadmap

## Fase 1: Producto Mínimo Viable (MVP)
*   Implementación del núcleo de la idea: "{idea}"
*   Autenticación básica de usuarios.

## Fase 2: Robustez y Escalabilidad (V1)
*   Integraciones avanzadas de seguridad y analíticas.
*   Optimización de base de datos.
"""
            elif filename == "tasks.md":
                content = f"""# Lista de Tareas de Desarrollo (TODOs)

- [ ] **Configurar Base de Datos** e infraestructura inicial.
- [ ] **Implementar Autenticación** y manejo de sesiones.
- [ ] **Desarrollar el Flujo Principal** para: *{idea}*.
- [ ] **Realizar Pruebas de Integración** y QA.
"""
            elif filename == "decisions.md":
                content = f"""# Registro de Decisiones de Arquitectura (ADR)

## ADR-01: Uso de API de Gemini para Refinamiento
*   **Estatus:** Aceptado
*   **Contexto:** Necesitamos un descubrimiento inteligente de requisitos.
*   **Decisión:** Integrar Gemini para generar preguntas condicionales y pre-escribir las specs.
*   **Consecuencias:** Mayor velocidad de diseño y consistencia técnica inicial.
"""
            elif filename == "glossary.md":
                content = f"""# Glosario de Términos

*   **MVP:** Minimum Viable Product (Producto Mínimo Viable).
*   **Spec IDE:** Entorno de especificaciones técnicas interactivas.
*   **SSOT:** Single Source of Truth (Fuente única de verdad).
"""
            elif filename == "agents.md":
                content = f"""# Instrucciones para Agentes de Código (System Prompts)

Este archivo sirve como prompt del sistema para herramientas como Cursor, Cline, Aider o Roo Code.

```text
Actúa como un desarrollador experto que va a implementar el proyecto.
Tu fuente única de verdad es la carpeta /specs del proyecto.
No escribas código que contradiga las definiciones en:
- architecture.md
- database.md
- api.md
```
"""
            else:
                content = f"# Especificación: {filename.replace('.md', '').capitalize()}\n\nContenido pendiente de refinamiento por el usuario."
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content.strip())
            generated_files.append(filename)
        except Exception as e:
            logger.error(f"Error escribiendo el archivo {filename}: {str(e)}")
            
    return {
        "status": "success",
        "message": f"Se han generado {len(generated_files)} archivos de especificación en el directorio /specs/",
        "files": generated_files
    }

@app.post("/api/copilot")
async def copilot_chat(req: CopilotRequest, x_gemini_key: str = Header(None)):
    model = get_gemini_model(x_gemini_key)
    project = req.projectData
    answers = project.get("answers", {})
    idea = project.get("seedIdea", "")
    
    prompt = f"""
    Eres el Copiloto de Spec IDE, un Staff Software Architect.
    Ayuda al usuario a estructurar su especificación técnica.
    
    Proyecto: "{project.get('name', 'Sin título')}"
    Idea Semilla: "{idea}"
    Archivo activo: "{req.activeFile}"
    Respuestas dadas en el Wizard: {json.dumps(answers, ensure_ascii=False)}
    
    Pregunta o solicitud del usuario: "{req.prompt}"
    
    Instrucciones:
    1. Responde de forma técnica, profesional, clara y directa.
    2. Si pide endpoints de API, modelos de datos o diagramas, provee la respuesta lista para copiar.
    3. No utilices introducciones largas, ve directo al grano.
    """
    
    try:
        response = model.generate_content(prompt)
        return {"reply": response.text.strip()}
    except Exception as e:
        logger.error(f"Error en chat copiloto: {str(e)}")
        return {"reply": f"Error al procesar consulta con Gemini: {str(e)}"}

# Servir index.html para todas las demás rutas no API (SPA routing fallback)
@app.get("/{rest_of_path:path}")
async def serve_spa(rest_of_path: str):
    # Si intentan acceder a un archivo estático que existe, se sirve normalmente (se monta después en la app)
    file_path = os.path.join(static_dir, rest_of_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # De lo contrario, se sirve el index.html principal
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return JSONResponse(status_code=404, content={"message": "Frontend static files not built yet"})

# Montar los estáticos al final para permitir que las rutas de la API tengan prioridad
app.mount("/", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
