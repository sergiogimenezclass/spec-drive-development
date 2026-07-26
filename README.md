# Spec IDE — Entorno de Ingeniería de Especificaciones Spec-First

**Spec IDE** es un entorno interactivo y visual diseñado bajo la metodología **Spec-First**. Su objetivo es permitir a desarrolladores, líderes técnicos y arquitectos de software descubrir, refinar y estructurar toda la documentación funcional y de arquitectura de una aplicación utilizando Inteligencia Artificial (**Google Gemini**), todo **antes** de escribir la primera línea de código de implementación.

El resultado es una **Fuente Única de Verdad (SSOT - Single Source of Truth)** en formato Markdown físico compatible con agentes autónomos de programación (como Cursor, Cline, Claude Code, Aider o Copilots) y lista para integrarse en tu repositorio de Git.

---

## 🌟 Características Principales

*   **🎙️ Entrevista de Descubrimiento Adaptativa:** Ingresa una idea semilla de software y la IA estructurará el dominio, tipo de producto, actores, MVP y un set de preguntas inteligentes y condicionales para refinar el diseño.
*   **⚡ Doble Camino de Generación:**
    *   *Camino 1 (Generación Directa):* Si tienes claro el proyecto, la IA escribe todas las especificaciones de inmediato a partir de tu idea.
    *   *Camino 2 (Entrevista Guiada):* Un flujo interactivo paso a paso para refinar dudas del negocio con IA antes de redactar.
*   **📂 Árbol de Especificaciones Técnicas (18 Módulos):** Genera e integra contratos de API, esquemas físicos de bases de datos, diagramas y reglas de negocio, incluyendo:
    *   `product.md` (con reglas de negocio críticas e inquebrantables).
    *   `database.md` (con esquema físico completo en sintaxis **Prisma DSL** listo para copiar).
    *   `openapi.json` (especificación de API interactiva en formato **OpenAPI 3.0** nativo).
    *   `agents.md` (instrucciones y reglas de estilos técnicos para agentes autónomos).
*   **🗺️ Fase de Planificación & Desglose de Features:** Un sub-módulo interactivo dentro del Workspace que analiza el diseño y genera fichas de historias de usuario con criterios de aceptación detallados y casos borde (edge cases) guardados en carpetas físicas temáticas (ej: `/specs/features/auth/login.md`).
*   **📊 Diagramas Dinámicos en Mermaid.js:** Visualiza flujos de usuario, diagramas de base de datos entidad-relación e infraestructura sin salir del navegador.
*   **🛡️ Linter de Consistencia e Inconsistencias:** Revisa que el diseño de tus archivos no tenga contradicciones arquitectónicas ni fallos lógicos graves.

---

## 🚀 Guía de Instalación Paso a Paso

Sigue estos pasos para instalar y ejecutar Spec IDE de forma local en tu computadora:

### 1. Prerrequisitos
Asegúrate de contar con los siguientes elementos instalados en tu sistema:
*   **Python 3.10 o superior** (compruébalo ejecutando `python3 --version` o `python --version`).
*   **Git** instalado.
*   Una conexión a internet para conectar con la API de Google Gemini.

### 2. Clonar el Repositorio
Abre tu terminal y clona el proyecto en tu máquina local:
```bash
git clone https://github.com/sergiogimenezclass/spec-drive-development.git
cd spec-drive-development
```

### 3. Crear y Activar el Entorno Virtual (Recomendado)
Es altamente recomendable aislar las dependencias utilizando un entorno virtual de Python:

*   **En Linux / macOS:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
*   **En Windows (Command Prompt):**
    ```cmd
    python -m venv .venv
    .venv\Scripts\activate
    ```
*   **En Windows (PowerShell):**
    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```

### 4. Instalar las Dependencias
Una vez activado el entorno virtual, instala los paquetes requeridos especificados en `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Guía de Configuración de la API de Gemini

Para que la IA funcione, Spec IDE necesita conectarse con los servicios de Google Gemini. Tienes dos maneras de configurar tu API Key:

### Opción A: Mediante Archivo `.env` (Recomendado y Permanente)
Esta opción te evita tener que introducir la clave en la interfaz gráfica web cada vez que inicies el servidor:

1.  Crea un archivo de texto llamado `.env` en la raíz del proyecto (junto a `app.py`).
2.  Escribe el siguiente contenido reemplazando con tu clave real obtenida de [Google AI Studio](https://aistudio.google.com/):
    ```env
    GEMINI_API_KEY=AIzaSy...tu_clave_api_aqui...
    ```
3.  El servidor de FastAPI leerá y aplicará esta clave automáticamente al iniciarse.

### Opción B: Directamente desde el Navegador (Temporal)
1.  Inicia el servidor (ver sección siguiente).
2.  Una vez cargada la aplicación en tu navegador, localiza el campo **API Key de Gemini** en la esquina superior derecha del header.
3.  Pega tu clave y presiona el botón **Guardar**. Esta clave se guardará en el `localStorage` de tu navegador.

---

## 💻 Guía de Uso del Sistema

### Paso 1: Inicialización del Proyecto
1.  Inicia el servidor local de desarrollo ejecutando:
    ```bash
    python app.py
    ```
2.  Abre tu navegador e ingresa a la dirección: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.
3.  Verás el Dashboard principal de Spec IDE. Completa los dos campos iniciales:
    *   **Nombre del Proyecto:** Ej: `MediciReserve`
    *   **Idea Semilla:** Describe detalladamente la funcionalidad principal (ej: *"Una aplicación para la reserva de turnos médicos en línea con recordatorios por correo, asignación de médicos según especialidad y módulo de administración"*).

### Paso 2: Elegir tu Metodología (Selector de Caminos)
En la parte inferior de la tarjeta del Dashboard, selecciona cómo proceder:
*   **Camino 1: Generación Directa (Directa):** Ideal si quieres que la IA procese la idea de inmediato y cree todo el set de especificaciones técnicas.
*   **Camino 2: Entrevista Guiada (Wizard):** La IA te hará preguntas adaptativas una a una. Una vez que decidas terminar o completes el cuestionario, se generarán las especificaciones basándose en tus respuestas.

Presiona el botón de acción para iniciar el proceso. Al terminar la redacción de la IA, el sistema abrirá el **Workspace del IDE**.

### Paso 3: Trabajando en el Workspace del IDE
Una vez dentro del IDE, cuentas con tres paneles principales:

#### A. Panel Lateral Izquierdo (Estructura de Specs)
*   Visualiza todos los módulos técnicos creados (`product.md`, `database.md`, `openapi.json`, etc.).
*   Los elementos marcados con un punto verde ya cuentan con información generada.
*   Haz clic en cualquier archivo para cargarlo en el panel central de edición.
*   Presiona el botón **Exportar** en la esquina superior para guardar físicamente todos los archivos Markdown en el directorio `/specs/` de tu repositorio local.

#### B. Panel Central (Editor y Visualizador)
*   **Pestaña Respuestas Guía:** Muestra los campos del formulario asociados a esa especificación para que modifiques o añadas respuestas personalizadas.
*   **Pestaña Visualizar Markdown:** Carga el código Markdown raw para edición directa y muestra una previsualización de HTML a la derecha.
*   **Boton "Completar con IA":** Si seleccionas una sección vacía, presiona este botón para que Gemini redacte esa especificación basándose en el contexto global del proyecto.
*   **Boton "Guardar":** Guarda manualmente el estado actual del proyecto en el archivo `project.json` en disco.

#### C. Panel Derecho (Herramientas del Inspector)
*   **Diagramas:** Genera automáticamente diagramas de flujo de usuario, entidad-relación de base de datos o arquitectura en Mermaid.js a partir de tus especificaciones.
*   **Linter IA:** Ejecuta auditorías sobre tus especificaciones para que la IA identifique vacíos o inconsistencias críticas.
*   **Copiloto:** Chatea con un arquitecto de software virtual de IA que comprende el contexto de tus especificaciones abiertas.

---

## 🗺️ Uso de la Fase de Planificación & Desglose de Features

Una de las características más avanzadas es la capacidad de desglose granular en módulos de desarrollo (historias de usuario concretas):

1.  Una vez generadas tus especificaciones base (Producto, Base de datos, etc.), presiona el botón **Desglosar Features con IA** ubicado al final de la barra lateral izquierda.
2.  Se abrirá un modal flotante. Haz clic en **Analizar Proyecto y Proponer Features**.
3.  La IA leerá tus especificaciones base y te sugerirá una lista de 8 a 10 features y módulos necesarios (ej: *Autenticación, Gestión de Turnos, Panel de Control, Notificaciones*).
4.  Utiliza los checkboxes para seleccionar qué módulos deseas documentar y presiona **Generar Seleccionadas**.
5.  Verás una barra de progreso y una consola con el log de escritura asíncrona de los archivos de feature.
6.  Al finalizar, cierra el modal. Verás que en la barra lateral izquierda aparece una nueva sección jerárquica llamada **Features & Módulos** con carpetas y archivos individuales (ej. `features/auth/login`).
7.  Al seleccionar uno de estos archivos, el editor se ajustará automáticamente a modo Markdown para que revises y edites la **User Story**, los **Criterios de Aceptación** y los **Casos Borde (Edge cases)** generados por la IA.
8.  Al presionar **Exportar**, las carpetas temáticas y archivos se escribirán físicamente en disco bajo la ruta `/specs/features/[modulo]/[nombre].md`.
