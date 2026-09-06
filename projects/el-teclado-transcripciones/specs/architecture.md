# Arquitectura de la Aplicación "Turbo Whisper"

Este documento describe la arquitectura propuesta para la aplicación de dictado de voz y transcripciones automáticas "Turbo Whisper", basándose en la idea del proyecto y las respuestas recopiladas.

## 1. Pila Tecnológica Propuesta

### Frontend:

*   **Tecnología:** **Tauri + React/TypeScript**
*   **Justificación:**
    *   **Tauri:** Proporciona una base ligera y performante para aplicaciones de escritorio multiplataforma, aprovechando las ventajas de Rust para el backend nativo y las tecnologías web para la interfaz de usuario. Su tamaño de binario es significativamente menor que alternativas como Electron, y su enfoque en la seguridad es un punto a favor. Permite una integración robusta con el sistema operativo para las funcionalidades de bajo nivel requeridas.
    *   **React/TypeScript:** Ofrece un ecosistema maduro y flexible para el desarrollo de la interfaz de usuario, permitiendo crear experiencias interactivas y reactivas. TypeScript mejora la mantenibilidad y la robustez del código.

### Backend (Lógica de Aplicación Local):

*   **Tecnología:** **Rust** (como parte del core de Tauri)
*   **Justificación:**
    *   **Rendimiento y Seguridad:** Rust es ideal para manejar tareas críticas de rendimiento y seguridad, como la captura de audio en tiempo real, la gestión del modelo local de Whisper y la interacción a bajo nivel con las APIs del sistema operativo para la emulación del teclado. Su garantía de seguridad de memoria previene muchos errores comunes.
    *   **Integración de Sistema:** Permite una interacción eficiente con las APIs nativas del OS para el micrófono, la simulación de eventos de teclado y la detección de atajos globales, que son funcionalidades centrales del proyecto.
    *   **Integración con Modelos de IA:** Facilita la integración con bibliotecas C/C++ como `whisper.cpp` (para Turbo Whisper local) y la realización de llamadas eficientes a APIs REST externas (como Gemini API).

### Base de Datos:

*   **Tecnología:** **SQLite**
*   **Justificación:**
    *   **Local y Embedded:** SQLite es una base de datos ligera, sin servidor, y basada en archivos, lo que la hace perfecta para aplicaciones de escritorio. No requiere configuración ni administración de un servidor de base de datos separado.
    *   **Almacenamiento Estructurado:** Ideal para almacenar datos estructurados como el historial de transcripciones (fecha, texto, proveedor de IA), atajos de teclado configurados (combinación, acción) y configuraciones de usuario (claves de API, preferencias de proveedor).
    *   **Fiabilidad:** Es una base de datos robusta y ampliamente utilizada, garantizando la persistencia y la integridad de los datos locales del usuario.

### Servidor:

*   **Tecnología:** **No hay un servidor de backend tradicional**
*   **Justificación:**
    *   La aplicación está diseñada como una solución de escritorio completamente local ("Sin autenticación / Local"). Toda la lógica de negocio y el almacenamiento de datos residen en la máquina del usuario.
    *   Las interacciones con servicios externos (como la Gemini API) se realizarán directamente desde el cliente Rust, sin pasar por un servidor intermedio propietario. Esto simplifica la arquitectura, mejora la privacidad y reduce los costos operativos.

### Proveedores de IA:

*   **Tecnología:** **Turbo Whisper (Local) / Gemini API (Cloud)**
*   **Justificación:**
    *   **Flexibilidad:** Ofrece al usuario la opción de elegir entre un procesamiento local (para mayor privacidad y posible rendimiento sin conexión) y un procesamiento en la nube (para modelos potencialmente más avanzados o sin necesidad de recursos locales intensivos).
    *   **Turbo Whisper (Local):** Implicará la integración con una implementación de Whisper optimizada para ejecución local (ej., `whisper.cpp` o similar) a través de Rust FFI. Esto permite la transcripción sin conexión y mantiene los datos de audio en la máquina del usuario.
    *   **Gemini API (Cloud):** Se realizará a través de llamadas HTTP seguras desde el backend Rust a los servicios de Google, utilizando las credenciales de API proporcionadas por el usuario.

## 2. Decisiones de Diseño Clave e Infraestructura

### Decisiones de Diseño:

1.  **Aplicación de Escritorio Nativa/Híbrida (Tauri/Rust):** Se opta por una aplicación de escritorio para tener acceso privilegiado a las APIs del sistema operativo, esencial para la captura de audio del micrófono y la emulación precisa de eventos de teclado para el dictado en "cualquier aplicación".
2.  **Integración de Teclado Virtual (Emulación de Entrada):** La funcionalidad central de enviar texto transcrito a la aplicación activa se implementará mediante el uso de APIs de bajo nivel del sistema operativo (p. ej., `SendInput` en Windows, `CGEventPost` en macOS, `xdotool` o equivalentes en Linux). Esto es crítico y representa uno de los desafíos técnicos principales.
3.  **Gestión de Audio en Tiempo Real:** El backend de Rust manejará la captura continua de audio con baja latencia, procesando el flujo en búferes pequeños para permitir la transcripción incremental y la detección de pausas o final de frase, optimizando la experiencia de dictado.
4.  **Sistema de Proveedores de IA Modular:** Se diseñará una interfaz de abstracción para los motores de transcripción (p. ej., `ITranscriptionProvider`), permitiendo al usuario cambiar entre Turbo Whisper local y Gemini API de manera transparente y extensible para futuros proveedores.
5.  **Persistencia de Datos Local con SQLite:** Todas las configuraciones, el historial de transcripciones y los atajos de teclado se almacenarán localmente en una base de datos SQLite para garantizar la privacidad del usuario, el acceso sin conexión y la persistencia de los datos.
6.  **No Autenticación Centralizada:** La ausencia de un sistema de autenticación en la nube simplifica la arquitectura y el modelo de seguridad, enfocándose en la privacidad y el control de datos por parte del usuario.
7.  **Hotkeys Globales:** La aplicación deberá escuchar y reaccionar a combinaciones de teclas globales (incluso cuando no esté en foco) para iniciar/detener el dictado o activar atajos personalizados.

### Conceptos de Despliegue:

*   **Paquetes Binarios Nativos:** La aplicación se distribuirá como instaladores nativos para las principales plataformas (Windows: `MSI`/`EXE`, macOS: `DMG`/`APP`, Linux: `DEB`/`RPM`/`AppImage`). Los instaladores incluirán la aplicación Tauri compilada para cada plataforma.
*   **Modelos de IA (Turbo Whisper):** El modelo base de Turbo Whisper puede ser incluido en el instalador (para modelos pequeños) o ser una descarga opcional post-instalación gestionada por la aplicación (para modelos más grandes), para reducir el tamaño inicial del instalador.
*   **Actualizaciones Automáticas:** Se implementará un mecanismo de actualización automática para el cliente, utilizando las capacidades de actualización integradas de Tauri o una solución personalizada, para asegurar que los usuarios siempre tengan la última versión y parches de seguridad.

## 3. Estructura de Módulos del Sistema y Flujo de Datos

### Estructura de Módulos Principales:

1.  **Módulo de Interfaz de Usuario (UI - Tauri Frontend - React/TypeScript):**
    *   **Componentes de Configuración:** Gestión de proveedores de IA, claves API, rutas de modelos locales.
    *   **Historial de Transcripciones:** Visualización, búsqueda y gestión de transcripciones pasadas.
    *   **Gestor de Atajos:** Interfaz para crear, editar y eliminar atajos de teclado personalizados.
    *   **Controles de Dictado:** Botones para iniciar/detener la escucha, modos de dictado.
    *   **Feedback Visual:** Indicadores de estado (ej., "Escuchando...", "Procesando..."), visualización del texto transcrito en tiempo real.
    *   **Comunicación:** Interactúa con el Módulo Core (Rust) a través de las capacidades de FFI (Foreign Function Interface) de Tauri para invocar comandos nativos y recibir eventos.

2.  **Módulo Core (Rust Backend - Tauri Core):**
    *   **Módulo de Captura de Audio:**
        *   Utiliza APIs del sistema operativo para acceder al micrófono.
        *   Gestiona el búfer de audio en tiempo real, aplicando preprocesamiento básico si es necesario (ej., reducción de ruido).
    *   **Módulo de Gestión de Transcripción:**
        *   **Interfaz `ITranscriptionProvider`:** Abstracción para diferentes motores de IA.
        *   **Implementación `TurboWhisperLocalProvider`:** Carga dinámica del modelo Whisper (ej., a través de `whisper.cpp`), procesamiento de audio, devuelve texto transcrito.
        *   **Implementación `GeminiAPIProvider`:** Envío de flujos de audio a la API de Google Gemini, gestión de la respuesta y errores.
        *   Lógica para la detección de final de frase, manejo de pausas y reintentos.
    *   **Módulo de Simulación de Teclado (Virtual Keyboard):**
        *   Utiliza APIs de bajo nivel del sistema operativo para emular pulsaciones de teclas.
        *   Recibe texto transcrito y lo "escribe" en la aplicación activa, con consideración de velocidad y posibles caracteres especiales.
    *   **Módulo de Gestión de Atajos (Hotkey Listener):**
        *   Registra y escucha atajos de teclado globales a nivel del sistema operativo.
        *   Mapea los atajos detectados a acciones internas de la aplicación (iniciar/detener dictado, insertar texto predefinido).
    *   **Módulo de Almacenamiento (SQLite Manager):**
        *   Interfaz para la base de datos SQLite.
        *   CRUD para el historial de transcripciones.
        *   CRUD para las configuraciones de atajos de teclado.
        *   CRUD para las preferencias de usuario y claves API.
    *   **Módulo de Notificaciones y Bandeja del Sistema:** Controla el icono de la bandeja del sistema, muestra notificaciones y gestiona el estado de la aplicación en segundo plano.

### Flujo de Datos Típico (Dictado por Voz):

1.  **Inicio del Dictado:**
    *   El usuario activa el dictado a través de un atajo de teclado global o un botón en la UI.
    *   El **Módulo UI** (o **Módulo de Gestión de Atajos**) envía una solicitud "Iniciar Dictado" al **Módulo Core (Rust)**.
2.  **Captura de Audio:**
    *   El **Módulo Core** activa el **Módulo de Captura de Audio**, que comienza a grabar audio del micrófono.
    *   Los datos de audio se envían en pequeños búferes al **Módulo de Gestión de Transcripción**.
3.  **Transcripción:**
    *   El **Módulo de Gestión de Transcripción** procesa los búferes de audio utilizando el proveedor de IA configurado (ej., **`TurboWhisperLocalProvider`** o **`GeminiAPIProvider`**).
    *   Se genera texto transcrito (parcial o final).
4.  **Almacenamiento y Visualización (Opcional):**
    *   El texto transcrito se envía al **Módulo de Almacenamiento**, que lo guarda en SQLite junto con metadatos (fecha, proveedor, etc.).
    *   El **Módulo Core** envía el texto transcrito (y el estado de la transcripción) de vuelta al **Módulo UI** para su visualización en tiempo real.
5.  **Emulación de Teclado:**
    *   El texto transcrito (o partes del mismo) se envía al **Módulo de Simulación de Teclado**.
    *   Este módulo simula las pulsaciones de teclas para "escribir" el texto en la aplicación activa del usuario.
6.  **Fin del Dictado:**
    *   El usuario detiene el dictado (por atajo o UI).
    *   El **Módulo Core** detiene la captura de audio y finaliza cualquier procesamiento de transcripción pendiente.
    *   El **Módulo de Almacenamiento** guarda la transcripción final.

### Flujo de Datos (Activación de Atajo de Teclado Personalizado):

1.  **Atajo Activado:**
    *   El usuario pulsa una combinación de teclas global previamente configurada.
    *   El **Módulo de Gestión de Atajos (Rust)** detecta la pulsación y la compara con los atajos almacenados en SQLite.
2.  **Acción Asociada:**
    *   Si hay una coincidencia, el **Módulo de Gestión de Atajos** ejecuta la acción asociada (ej., "Insertar texto '¡Hola Mundo!'").
3.  **Emulación de Teclado:**
    *   Si la acción implica insertar texto, este se envía al **Módulo de Simulación de Teclado**, que lo escribe en la aplicación activa.

Esta arquitectura busca equilibrar el rendimiento nativo con una experiencia de desarrollo moderna y la flexibilidad necesaria para integrar diversas tecnologías de IA, todo ello centrado en la privacidad y la experiencia de usuario de una aplicación de escritorio local.