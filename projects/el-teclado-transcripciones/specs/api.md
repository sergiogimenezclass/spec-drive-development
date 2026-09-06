# Documentación de la API RESTful de Turbo Whisper

Esta documentación describe la API RESTful para interactuar con la aplicación local Turbo Whisper, permitiendo el dictado de voz, transcripciones, gestión de proveedores de IA y atajos de teclado.

---

## 1. Protocolo de Comunicación, Autenticación y Manejo de Sesiones

### Protocolo de Comunicación

La API utiliza el protocolo **HTTP/1.1** o **HTTP/2.0** sobre TCP/IP para la comunicación. Dado que la aplicación está diseñada para funcionar localmente, la comunicación se realiza típicamente a través de `http://localhost:<PUERTO>`.

Aunque HTTPS es estándar para APIs web, en un entorno puramente local y de confianza, HTTP es suficiente para evitar la sobrecarga de cifrado ya que los datos no transitan por una red externa susceptible de intercepción maliciosa. No obstante, si se decide exponer la API a través de la red local, se recomienda encarecidamente implementar HTTPS.

### Autenticación y Autorización

La API de Turbo Whisper opera en un modelo **sin autenticación** y se asume que el entorno local donde se ejecuta la aplicación es de confianza. Esto significa que cualquier proceso o aplicación local que pueda acceder al puerto de la API tendrá acceso completo a sus funcionalidades.

Este enfoque se basa en la premisa de que la API es un componente interno de la aplicación de escritorio y no está diseñada para ser expuesta públicamente ni para ser accedida por usuarios remotos sin las capas de seguridad adicionales que la aplicación principal pueda proporcionar.

### Manejo de Sesiones

Debido a la ausencia de autenticación y la naturaleza *stateless* (sin estado) de REST, la API no gestiona sesiones de usuario. Cada petición se considera independiente y debe contener toda la información necesaria para ser procesada. El manejo del estado (como la sesión de transcripción en tiempo real) se realiza a través de identificadores específicos incluidos en las rutas de los endpoints.

---

## 2. Listado de Endpoints Clave

A continuación, se listan los endpoints más importantes de la API, incluyendo sus métodos HTTP, rutas y los payloads esperados para las peticiones y respuestas.

### 2.1. Transcripción de Voz

#### `POST /transcribe`
Procesa un archivo de audio para transcripción y devuelve el texto resultante.

*   **Descripción:** Envía un archivo de audio para una transcripción asíncrona o síncrona (dependiendo de la configuración del proveedor de IA y el tamaño del audio).
*   **Método:** `POST`
*   **Request Payload (multipart/form-data):**
    ```
    Content-Type: multipart/form-data; boundary=---boundary

    -----boundary
    Content-Disposition: form-data; name="audio"; filename="audio.wav"
    Content-Type: audio/wav

    [Datos binarios del archivo de audio]
    -----boundary
    Content-Disposition: form-data; name="config"
    Content-Type: application/json

    {
        "providerId": "uuid-del-proveedor-ia",
        "language": "es-ES",
        "format": "text",
        "enablePunctuation": true
    }
    -----boundary--
    ```
    *   `audio`: Archivo de audio en formato compatible (WAV, MP3, etc.).
    *   `config`: Objeto JSON con configuración opcional para la transcripción.
        *   `providerId` (opcional): ID del proveedor de IA a usar. Si no se especifica, se usa el proveedor activo.
        *   `language` (opcional): Idioma del audio (e.g., "es-ES", "en-US").
        *   `format` (opcional): Formato de salida (e.g., "text", "srt").
        *   `enablePunctuation` (opcional): Booleano para activar/desactivar la puntuación automática.
*   **Response Payload (200 OK):**
    ```json
    {
        "id": "uuid-de-la-transcripcion",
        "text": "Este es el texto transcrito de tu audio.",
        "language": "es-ES",
        "duration": 5.2,
        "provider": "Turbo Whisper Local",
        "timestamp": "2023-10-27T10:30:00Z",
        "confidence": 0.95
    }
    ```

#### `POST /transcribe/stream/start`
Inicia una sesión de transcripción de voz en tiempo real.

*   **Descripción:** Prepara el sistema para recibir flujos de audio continuos y transcribirlos en tiempo real.
*   **Método:** `POST`
*   **Request Payload (200 OK):**
    ```json
    {
        "providerId": "uuid-del-proveedor-ia",
        "language": "es-ES",
        "enablePunctuation": true
    }
    ```
    *   `providerId` (opcional): ID del proveedor de IA a usar.
    *   `language` (opcional): Idioma esperado del audio.
    *   `enablePunctuation` (opcional): Booleano para activar/desactivar la puntuación automática.
*   **Response Payload (200 OK):**
    ```json
    {
        "sessionId": "uuid-de-la-sesion-de-transcripcion"
    }
    ```

#### `POST /transcribe/stream/{sessionId}/audio`
Envía un fragmento de audio a una sesión de transcripción en tiempo real.

*   **Descripción:** Recibe un fragmento de audio binario para procesarlo en la sesión activa.
*   **Método:** `POST`
*   **Parámetros de Ruta:**
    *   `sessionId`: El ID de la sesión obtenido de `/transcribe/stream/start`.
*   **Request Payload (audio/opus o application/octet-stream):**
    ```
    [Datos binarios del fragmento de audio]
    ```
    *   Se recomienda enviar audio en formatos optimizados para streaming como Opus o PCM sin formato.
*   **Response Payload (200 OK):**
    ```json
    {
        "sessionId": "uuid-de-la-sesion-de-transcripcion",
        "partialText": "Este es un texto parcialmente transcrito...",
        "isFinal": false,
        "confidence": 0.88
    }
    ```
    *   `isFinal`: `true` si este fragmento de texto se considera finalizado y no cambiará, `false` si es provisional.

#### `POST /transcribe/stream/{sessionId}/stop`
Finaliza una sesión de transcripción en tiempo real.

*   **Descripción:** Detiene la sesión de transcripción y devuelve cualquier texto final pendiente.
*   **Método:** `POST`
*   **Parámetros de Ruta:**
    *   `sessionId`: El ID de la sesión a detener.
*   **Request Payload:** `None`
*   **Response Payload (200 OK):**
    ```json
    {
        "sessionId": "uuid-de-la-sesion-de-transcripcion",
        "finalText": "Este es el texto completo y final de la transcripción.",
        "language": "es-ES",
        "duration": 60.5,
        "provider": "Gemini API",
        "timestamp": "2023-10-27T10:35:00Z"
    }
    ```

### 2.2. Gestión de Proveedores de IA

#### `GET /ai-providers`
Obtiene la lista de todos los proveedores de IA configurados.

*   **Descripción:** Retorna un array con los detalles de cada proveedor de IA, incluyendo cuál está activo.
*   **Método:** `GET`
*   **Request Payload:** `None`
*   **Response Payload (200 OK):**
    ```json
    [
        {
            "id": "uuid-del-proveedor-whisper-local",
            "name": "Turbo Whisper Local",
            "type": "local",
            "isActive": true
        },
        {
            "id": "uuid-del-proveedor-gemini",
            "name": "Gemini API",
            "type": "cloud",
            "isActive": false,
            "config": {
                "apiKey": "****************"
            }
        }
    ]
    ```
    *   `config.apiKey` mostrará un valor ofuscado por seguridad.

#### `POST /ai-providers`
Añade un nuevo proveedor de IA.

*   **Descripción:** Permite configurar y añadir un nuevo servicio de transcripción (e.g., Gemini API).
*   **Método:** `POST`
*   **Request Payload (application/json):**
    ```json
    {
        "name": "Gemini API",
        "type": "cloud",
        "config": {
            "apiKey": "TU_API_KEY_DE_GEMINI",
            "model": "gemini-pro"
        }
    }
    ```
    *   `name`: Nombre descriptivo para el proveedor.
    *   `type`: Tipo de proveedor ("local" o "cloud").
    *   `config`: Objeto con las credenciales o configuraciones específicas del proveedor.
*   **Response Payload (201 Created):**
    ```json
    {
        "id": "uuid-del-nuevo-proveedor",
        "name": "Gemini API",
        "type": "cloud",
        "isActive": false,
        "config": {
            "apiKey": "****************",
            "model": "gemini-pro"
        }
    }
    ```

#### `PUT /ai-providers/{providerId}`
Actualiza la configuración de un proveedor de IA existente.

*   **Descripción:** Modifica los detalles de un proveedor de IA específico.
*   **Método:** `PUT`
*   **Parámetros de Ruta:**
    *   `providerId`: ID del proveedor de IA a actualizar.
*   **Request Payload (application/json):**
    ```json
    {
        "name": "Gemini API (personal)",
        "config": {
            "apiKey": "NUEVA_API_KEY_DE_GEMINI",
            "model": "gemini-pro-vision"
        }
    }
    ```
    *   Se pueden enviar solo los campos a modificar.
*   **Response Payload (200 OK):**
    ```json
    {
        "id": "uuid-del-proveedor-gemini",
        "name": "Gemini API (personal)",
        "type": "cloud",
        "isActive": false,
        "config": {
            "apiKey": "****************",
            "model": "gemini-pro-vision"
        }
    }
    ```

#### `DELETE /ai-providers/{providerId}`
Elimina un proveedor de IA.

*   **Descripción:** Elimina un proveedor de IA de la configuración. No se puede eliminar el proveedor activo.
*   **Método:** `DELETE`
*   **Parámetros de Ruta:**
    *   `providerId`: ID del proveedor de IA a eliminar.
*   **Request Payload:** `None`
*   **Response Payload (204 No Content):** `None`

#### `PUT /ai-providers/active`
Establece el proveedor de IA activo.

*   **Descripción:** Designa qué proveedor de IA se utilizará por defecto para las transcripciones.
*   **Método:** `PUT`
*   **Request Payload (application/json):**
    ```json
    {
        "providerId": "uuid-del-proveedor-a-activar"
    }
    ```
*   **Response Payload (200 OK):**
    ```json
    {
        "message": "Proveedor de IA activo establecido correctamente.",
        "activeProviderId": "uuid-del-proveedor-activado"
    }
    ```

### 2.3. Gestión de Atajos de Teclado (Hotkeys)

#### `GET /hotkeys`
Obtiene la lista de todos los atajos de teclado configurados.

*   **Descripción:** Retorna un array con todos los atajos de teclado y sus acciones asociadas.
*   **Método:** `GET`
*   **Request Payload:** `None`
*   **Response Payload (200 OK):**
    ```json
    [
        {
            "id": "uuid-del-atajo-1",
            "name": "Iniciar/Detener Transcripción",
            "action": "toggle_transcription",
            "keyCombination": ["Control", "Shift", "T"],
            "isEnabled": true
        },
        {
            "id": "uuid-del-atajo-2",
            "name": "Enviar al Portapapeles",
            "action": "copy_to_clipboard",
            "keyCombination": ["Control", "Shift", "C"],
            "isEnabled": false
        }
    ]
    ```
    *   `keyCombination`: Array de cadenas representando las teclas y modificadores (e.g., "Control", "Alt", "Shift", "T", "F1").

#### `POST /hotkeys`
Crea un nuevo atajo de teclado.

*   **Descripción:** Configura un nuevo atajo de teclado para realizar una acción específica.
*   **Método:** `POST`
*   **Request Payload (application/json):**
    ```json
    {
        "name": "Abrir Historial",
        "action": "open_history",
        "keyCombination": ["Alt", "H"],
        "isEnabled": true
    }
    ```
*   **Response Payload (201 Created):**
    ```json
    {
        "id": "uuid-del-nuevo-atajo",
        "name": "Abrir Historial",
        "action": "open_history",
        "keyCombination": ["Alt", "H"],
        "isEnabled": true
    }
    ```

#### `PUT /hotkeys/{hotkeyId}`
Actualiza un atajo de teclado existente.

*   **Descripción:** Modifica los detalles de un atajo de teclado específico.
*   **Método:** `PUT`
*   **Parámetros de Ruta:**
    *   `hotkeyId`: ID del atajo de teclado a actualizar.
*   **Request Payload (application/json):**
    ```json
    {
        "keyCombination": ["Control", "Shift", "G"],
        "isEnabled": false
    }
    ```
*   **Response Payload (200 OK):**
    ```json
    {
        "id": "uuid-del-atajo-1",
        "name": "Iniciar/Detener Transcripción",
        "action": "toggle_transcription",
        "keyCombination": ["Control", "Shift", "G"],
        "isEnabled": false
    }
    ```

#### `DELETE /hotkeys/{hotkeyId}`
Elimina un atajo de teclado.

*   **Descripción:** Elimina un atajo de teclado de la configuración.
*   **Método:** `DELETE`
*   **Parámetros de Ruta:**
    *   `hotkeyId`: ID del atajo de teclado a eliminar.
*   **Request Payload:** `None`
*   **Response Payload (204 No Content):** `None`

### 2.4. Historial de Transcripciones

#### `GET /history`
Obtiene el historial de transcripciones.

*   **Descripción:** Retorna una lista paginada y/o filtrada de transcripciones previas.
*   **Método:** `GET`
*   **Parámetros de Consulta (Query Parameters):**
    *   `limit` (opcional): Número máximo de resultados a devolver (por defecto: 20).
    *   `offset` (opcional): Número de resultados a saltar (para paginación).
    *   `search` (opcional): Cadena de texto para buscar dentro de las transcripciones.
    *   `from` (opcional): Fecha de inicio para filtrar (formato ISO 8601).
    *   `to` (opcional): Fecha de fin para filtrar (formato ISO 8601).
*   **Request Payload:** `None`
*   **Response Payload (200 OK):**
    ```json
    {
        "total": 50,
        "limit": 20,
        "offset": 0,
        "items": [
            {
                "id": "uuid-historial-1",
                "text": "Esta es la primera transcripción guardada.",
                "timestamp": "2023-10-26T14:00:00Z",
                "language": "es-ES",
                "provider": "Turbo Whisper Local"
            },
            {
                "id": "uuid-historial-2",
                "text": "Aquí tenemos una segunda entrada en el historial.",
                "timestamp": "2023-10-27T09:15:00Z",
                "language": "es-ES",
                "provider": "Gemini API"
            }
        ]
    }
    ```

#### `GET /history/{entryId}`
Obtiene una entrada específica del historial.

*   **Descripción:** Recupera los detalles completos de una transcripción del historial.
*   **Método:** `GET`
*   **Parámetros de Ruta:**
    *   `entryId`: ID de la entrada del historial.
*   **Request Payload:** `None`
*   **Response Payload (200 OK):**
    ```json
    {
        "id": "uuid-historial-1",
        "text": "Esta es la primera transcripción guardada.",
        "timestamp": "2023-10-26T14:00:00Z",
        "language": "es-ES",
        "provider": "Turbo Whisper Local",
        "audioPath": "/path/to/local/audio/file.wav" // Opcional, si se guarda el audio
    }
    ```

#### `DELETE /history/{entryId}`
Elimina una entrada específica del historial.

*   **Descripción:** Elimina una transcripción del historial.
*   **Método:** `DELETE`
*   **Parámetros de Ruta:**
    *   `entryId`: ID de la entrada del historial a eliminar.
*   **Request Payload:** `None`
*   **Response Payload (204 No Content):** `None`

#### `DELETE /history`
Elimina todo el historial de transcripciones.

*   **Descripción:** Vacía por completo el historial de transcripciones.
*   **Método:** `DELETE`
*   **Request Payload:** `None`
*   **Response Payload (204 No Content):** `None`

### 2.5. Estado del Servicio

#### `GET /health`
Comprueba el estado de la API.

*   **Descripción:** Un endpoint simple para verificar si la API está en funcionamiento.
*   **Método:** `GET`
*   **Request Payload:** `None`
*   **Response Payload (200 OK):**
    ```json
    {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": "2023-10-27T10:45:00Z"
    }
    ```

---

## 3. Estructura de Errores Comunes

La API utiliza códigos de estado HTTP estándar para indicar el resultado de una petición (2xx para éxito, 4xx para errores del cliente, 5xx para errores del servidor). En caso de un error (cualquier código de estado HTTP que no sea 2xx), la respuesta incluirá un cuerpo JSON con detalles sobre el problema.

### Estructura del Payload de Error

```json
{
    "code": "CODIGO_DE_ERROR_INTERNO",
    "message": "Descripción legible del error.",
    "details": "Detalles técnicos o adicionales sobre la causa del error."
}
```

*   `code`: Un identificador único y constante para el tipo de error (útil para el procesamiento programático).
*   `message`: Una descripción breve y legible del error.
*   `details` (opcional): Información más específica que pueda ayudar a depurar o entender el error.

### Ejemplos de Errores Comunes

| Código HTTP | Código Interno         | Mensaje Sugerido                                    | Detalles                                                  |
| :---------- | :--------------------- | :-------------------------------------------------- | :-------------------------------------------------------- |
| `400 Bad Request` | `INVALID_PAYLOAD`      | La estructura de la petición es inválida.           | "El campo 'name' es obligatorio." o "Formato de audio no soportado." |
| `400 Bad Request` | `INVALID_PARAM`        | Parámetro de consulta o ruta inválido.              | "El 'limit' debe ser un número positivo."                   |
| `404 Not Found`   | `RESOURCE_NOT_FOUND`   | El recurso solicitado no fue encontrado.            | "No se encontró el proveedor de IA con ID 'xyz'."         |
| `409 Conflict`    | `RESOURCE_CONFLICT`    | Conflicto con el estado actual del recurso.         | "No se puede eliminar el proveedor de IA activo."         |
| `422 Unprocessable Content` | `VALIDATION_ERROR`     | La petición contiene datos semánticamente inválidos. | "La API Key de Gemini proporcionada no es válida."         |
| `500 Internal Server Error` | `INTERNAL_SERVER_ERROR`| Ha ocurrido un error inesperado en el servidor.     | "Fallo al inicializar el modelo de Whisper."                |
| `503 Service Unavailable` | `AI_PROVIDER_ERROR`    | El proveedor de IA externo no está disponible.      | "Gemini API no responde o ha excedido los límites de cuota." |