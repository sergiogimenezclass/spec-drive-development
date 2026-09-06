# Spec IDE — Entorno de Ingeniería de Especificaciones Spec-First

**Spec IDE** es un entorno interactivo y visual diseñado bajo la metodología **Spec-First**. Su objetivo es permitir a desarrolladores, líderes técnicos y arquitectos de software descubrir, refinar y estructurar toda la documentación funcional y de arquitectura de una aplicación utilizando Inteligencia Artificial (**Google Gemini**), todo **antes** de escribir la primera línea de código de implementación.

El resultado es una **Fuente Única de Verdad (SSOT - Single Source of Truth)** en formato Markdown físico compatible con agentes autónomos de programación (como Cursor, Cline, Claude Code, Aider o Copilots) y lista para integrarse en tu repositorio de Git.

---

## 🌟 Características Principales

*   **💬 Modo 1: Explore Chat + Wizard Inteligente (Recomendado):**
    *   Mantén una charla informal y libre con el **Spec Copilot** sobre la idea de tu software antes de redactar especificaciones.
    *   Con un solo clic en **`[ 📋 Revisar Cuestionario & Redactar Specs ]`**, la IA extrae automáticamente las decisiones de arquitectura (`/api/explore-extract-answers`) y pre-llena el Cuestionario Técnico en 30 segundos.
*   **⚡ Modo 2: Generación Directa (Sin Chat):**
    *   Si tienes claro el alcance, omite la conversación e ingresa directamente al cuestionario o genera las especificaciones de inmediato.
*   **📁 Gestión Multi-Proyecto e Aislamiento Físico:**
    *   Creación automática de carpetas dedicadas por proyecto (ej: `./projects/mi-sistema/`) o especificación de rutas personalizadas en cualquier parte de tu disco duro.
    *   Persistencia automática del proyecto activo (`.active_project.json`) y panel de navegación de proyectos recientes (`/api/recent-projects`) para alternar fácilmente entre proyectos sin perder datos.
    *   Persistencia del historial conversacional conversando con **Spec Copilot** en `chat_history.json` dentro de cada carpeta de proyecto.
*   **📂 Árbol de Especificaciones Técnicas (17 Módulos):** Genera e integra contratos de API, esquemas físicos de bases de datos, diagramas y reglas de negocio:
    *   `product.md` (con reglas de negocio críticas e inquebrantables).
    *   `database.md` (con esquema físico completo en sintaxis **Prisma DSL** listo para copiar).
    *   `openapi.json` (especificación de API interactiva en formato **OpenAPI 3.0** nativo).
    *   `agents.md` (instrucciones y reglas de estilos técnicos para agentes autónomos).
*   **🗺️ Planificación & Desglose de Features:** Analiza el diseño general y genera fichas de historias de usuario con criterios de aceptación detallados y casos borde (edge cases) en carpetas físicas temáticas (ej: `/specs/features/auth/login.md`).
*   **🤖 Spec Copilot Integrado & Pantalla Completa:** Asistente conversacional de IA conectado directamente a las especificaciones activas del proyecto, expandible a modo pantalla completa.

---

## 🚀 Guía de Instalación Paso a Paso

### 1. Prerrequisitos
Asegúrate de contar con los siguientes elementos instalados en tu sistema:
*   **Python 3.10 o superior** (compruébalo ejecutando `python3 --version` o `python --version`).
*   **Git** instalado.
*   Una API Key de **Google Gemini** ([Google AI Studio](https://aistudio.google.com/)).

### 2. Clonar el Repositorio
Abre tu terminal y clona el proyecto en tu máquina local:
```bash
git clone https://github.com/sergiogimenezclass/spec-drive-development.git
cd spec-drive-development
```

### 3. Crear y Activar el Entorno Virtual
```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (CMD)
python -m venv .venv
.venv\Scripts\activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 4. Instalar las Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Configuración de la API Key de Gemini

Tienes dos alternativas para configurar tu clave de Google AI Studio:

### Opción A: Archivo `.env` (Recomendado)
Crea un archivo `.env` en la raíz del proyecto:
```env
GEMINI_API_KEY=AIzaSy...tu_clave_api_real...
```

### Opción B: Desde el Header de la Interfaz Web
Ingresa tu clave en el campo **Gemini API Key...** en la esquina superior derecha del header y presiona **Guardar**.

---

## 💻 Guía de Uso del Sistema

### 1. Iniciar el Servidor Local
```bash
python app.py
```
Abre tu navegador en **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

### 2. Crear un Proyecto y Seleccionar Metodología
1. Ingresa el **Nombre del Proyecto** y la **Carpeta Destino** (opcional, por defecto creará `./projects/{slug}`).
2. Describe tu **Idea Semilla**.
3. Selecciona la Metodología:
   - **Modo 1 (Explore Chat + Wizard Inteligente)**: Abre el Spec Copilot para conversar y explorar. Al finalizar presiona `[ 📋 Revisar Cuestionario & Redactar Specs ]` para pre-llenar las opciones y generar las especificaciones.
   - **Modo 2 (Generación Directa)**: Redacta las especificaciones o completa el cuestionario inmediatamente sin charla previa.

### 3. Navegación en el Workspace IDE
- **Panel Izquierdo**: Explora los 17 archivos de especificación, agrega features y presiona **Exportar** para escribir los archivos Markdown en disco (`/specs/`).
- **Panel Central**: Previsualiza el contenido renderizado en Markdown HTML.
- **Panel Derecho (Spec Copilot)**: Chatea con el copiloto sobre las especificaciones del proyecto o expande el panel a pantalla completa.

---

## 📡 Endpoints Principales de la API REST

| Endpoint | Método | Descripción |
| :--- | :---: | :--- |
| `/api/set-project-path` | `POST` | Configura y persiste la carpeta destino del proyecto en `.active_project.json`. |
| `/api/recent-projects` | `GET` | Lista todos los proyectos escaneados en disco y cuál está activo. |
| `/api/explore-extract-answers` | `POST` | Extrae decisiones de arquitectura en formato JSON a partir del chat de Explore. |
| `/api/analyze-idea` | `POST` | Abstrae la idea semilla en dominio, actores y cuestionario adaptativo. |
| `/api/export-specs` | `POST` | Genera y exporta físicamente todos los módulos `.md` y `openapi.json` a la carpeta `/specs/`. |
| `/api/copilot-chat` | `POST` | Endpoint conversacional para el Spec Copilot con persistencia en `chat_history.json`. |
| `/api/open-specs-folder` | `POST` | Abre la carpeta de especificaciones del proyecto en el explorador de archivos del SO. |nerados por la IA.
8.  Al presionar **Exportar**, las carpetas temáticas y archivos se escribirán físicamente en disco bajo la ruta `/specs/features/[modulo]/[nombre].md`.
