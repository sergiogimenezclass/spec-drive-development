# Spec IDE — Ingeniería de Especificaciones Spec-First

**Spec IDE** es un entorno interactivo diseñado para la metodología **Spec-First**. Su objetivo es permitir a desarrolladores, líderes técnicos y arquitectos de software descubrir, refinar y estructurar las especificaciones técnicas y funcionales de un proyecto de software utilizando Inteligencia Artificial (**Google Gemini**), todo **antes** de escribir la primera línea de código. 

De esta manera, el proyecto genera una *Fuente Única de Verdad (SSOT - Single Source of Truth)* en formato Markdown compatible con agentes autónomos de programación (como Cursor, Cline, Aider o Copilots).

---

## 🌟 Características Principales

*   **🎙️ Entrevista de Descubrimiento (Wizard):** Ingresa una idea semilla de software y la IA extraerá automáticamente el dominio, tipo de producto, actores, funcionalidades MVP, riesgos y un set de preguntas adaptativas.
*   **📂 Árbol de Especificaciones Modulares:** Genera y exporta 16 documentos Markdown técnicos interconectados en el directorio `/specs/` (ej. `product.md`, `architecture.md`, `database.md`, `api.md`, `security.md`, `user-stories.md`, `decisions.md` (ADRs), y `agents.md` para guiar a los agentes de IA).
*   **📊 Diagramas Dinámicos con Mermaid.js:** Generación instantánea mediante IA de diagramas de Entidad-Relación (Base de Datos), diagramas de Flujo de Usuario y diagramas conceptuales de Arquitectura.
*   **🛡️ Linter de Consistencia Técnica:** Un analizador inteligente que evalúa tus especificaciones en busca de contradicciones o vulnerabilidades de seguridad (ej. inconsistencias de base de datos o pasarelas de pago desprotegidas).
*   **🤖 Copiloto de Arquitectura Integrado:** Chat contextual en tiempo real con un *Staff Software Architect* para refinar el archivo de especificación activo o diseñar endpoints y modelos de datos.

---

## 🛠️ Tecnologías Utilizadas

### Backend
*   **FastAPI:** Framework de alto rendimiento para servir la API REST y rutas estáticas.
*   **Uvicorn:** Servidor web ASGI para producción y desarrollo.
*   **Google Generative AI SDK:** Integración con la API de Gemini (modelo `gemini-1.5-flash` para velocidad y consistencia).
*   **Pydantic:** Validación de esquemas y estructuras JSON.

### Frontend
*   **HTML5, Vanilla CSS y JavaScript (ES6+):** SPA (Single Page Application) responsiva con tema oscuro/claro y efectos visuales modernos (glassmorphic orbs, micro-animaciones).
*   **Mermaid.js:** Renderizado interactivo de diagramas directamente en el navegador.

---

## 🚀 Cómo Iniciar el Proyecto Localmente

### Prerrequisitos
*   Python 3.10 o superior instalado.
*   Una API Key de Google AI Studio (Gemini).

### Pasos
1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/sergiogimenezclass/spec-drive-development.git
    cd spec-drive-development
    ```

2.  **Configurar el entorno virtual y activarlo:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # En Linux/macOS
    # .venv\Scripts\activate   # En Windows
    ```

3.  **Instalar las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Iniciar el servidor:**
    ```bash
    python app.py
    ```

5.  **Abrir en el navegador:**
    Accede a [http://127.0.0.1:8000](http://127.0.0.1:8000) e ingresa tu Gemini API Key en el campo correspondiente del header para comenzar el descubrimiento de tu idea de software.

---

## 📂 Estructura de Archivos del Proyecto

*   `app.py`: Lógica principal del backend FastAPI y conexión con Gemini.
*   `requirements.txt`: Dependencias del sistema.
*   `static/`: Código frontend (HTML, CSS, JS).
    *   `index.html`: Estructura e interfaz principal del IDE.
    *   `styles.css`: Estilos visuales del editor y el wizard.
    *   `app.js`: Controlador de eventos, renderizado Mermaid, llamadas a la API y sincronización.
*   `specs/` *(Generado tras exportar)*: Directorio donde se consolidan todos los archivos `.md` de especificación.
*   `project.json` *(Generado tras guardar)*: Estado de las respuestas del usuario y metadatos del proyecto.
