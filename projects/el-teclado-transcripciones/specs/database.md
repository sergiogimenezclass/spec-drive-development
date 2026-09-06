# Diseño de Base de Datos para Turbo Whisper

Este documento detalla el diseño conceptual y físico de la base de datos para la aplicación "Turbo Whisper", una herramienta de dictado por voz y transcripción automática. La base de datos será local, utilizando SQLite como motor.

## 1. Diseño Conceptual del Modelo de Datos

El modelo de datos se centra en almacenar las configuraciones de la aplicación, el historial de transcripciones y los ajustes de los proveedores de IA. Se han identificado las siguientes entidades principales:

*   **ConfiguracionGeneral**: Almacena las preferencias globales y ajustes de la aplicación, como el idioma predeterminado y el proveedor de IA por defecto. Dada la naturaleza local de la aplicación sin autenticación de usuarios, se asume una única fila en esta tabla.
*   **ProveedorIA**: Gestiona los diferentes motores de inteligencia artificial que pueden ser utilizados para la transcripción (ej., Turbo Whisper local, Gemini API). Cada proveedor tiene sus propios parámetros de configuración.
*   **AtajoTeclado**: Permite al usuario definir y almacenar atajos de teclado personalizados que insertarán texto predefinido o ejecutarán acciones específicas.
*   **Transcripcion**: Guarda un registro de todas las transcripciones de voz realizadas, incluyendo el texto, la fecha y el proveedor de IA utilizado.

## 2. Listado de Entidades principales con sus atributos (tipos de datos) y relaciones

### Entidad: `ConfiguracionGeneral`
Esta entidad contiene los ajustes generales de la aplicación. Se espera que contenga una única fila.

*   `id`: `Int` - Clave primaria, autoincremental.
*   `idiomaPredeterminado`: `String` - Idioma principal para la transcripción (ej. "es-ES", "en-US").
*   `activacionMicrofono`: `String` - Atajo de teclado o método para activar/desactivar el micrófono (ej. "CTRL+SHIFT+M", "PushToTalk").
*   `proveedorIApredeterminadoId`: `Int?` - ID del `ProveedorIA` seleccionado por defecto para nuevas transcripciones (Relación opcional a `ProveedorIA`).

### Entidad: `ProveedorIA`
Configuración de los diferentes servicios de inteligencia artificial disponibles.

*   `id`: `Int` - Clave primaria, autoincremental.
*   `nombre`: `String` - Nombre único del proveedor (ej. "Turbo Whisper Local", "Gemini API").
*   `tipo`: `String` - Tipo de proveedor (ej. "LOCAL", "API").
*   `apiKey`: `String?` - Clave de API si es un proveedor externo (opcional).
*   `modelo`: `String?` - Modelo específico a usar (ej. "small", "base", "gemini-pro").
*   `urlBase`: `String?` - URL base para APIs externas (opcional).
*   `activo`: `Boolean` - Indica si el proveedor está habilitado para su uso.
*   `orden`: `Int` - Orden de visualización en la interfaz de usuario.

### Entidad: `AtajoTeclado`
Almacena combinaciones de teclas personalizadas y el texto asociado.

*   `id`: `Int` - Clave primaria, autoincremental.
*   `nombre`: `String` - Nombre descriptivo del atajo (ej. "Firma email", "Saludo").
*   `combinacionTeclas`: `String` - La combinación de teclas real (ej. "Ctrl+Alt+S"). Debe ser única.
*   `textoAsociado`: `String` - El texto que se insertará cuando se active el atajo.
*   `activo`: `Boolean` - Indica si el atajo está habilitado.
*   `fechaCreacion`: `DateTime` - Marca de tiempo de cuándo se creó el atajo.
*   `fechaActualizacion`: `DateTime` - Marca de tiempo de la última modificación.

### Entidad: `Transcripcion`
Historial de todas las transcripciones de voz realizadas.

*   `id`: `Int` - Clave primaria, autoincremental.
*   `texto`: `String` - El texto transcrito.
*   `fecha`: `DateTime` - Fecha y hora en que se realizó la transcripción.
*   `idioma`: `String` - Idioma detectado o utilizado para esta transcripción.
*   `duracionAudioMs`: `Int?` - Duración del segmento de audio transcrito en milisegundos (opcional).
*   `confianza`: `Float?` - Nivel de confianza o probabilidad de la transcripción (opcional).
*   `proveedorIAId`: `Int` - ID del `ProveedorIA` que generó esta transcripción (Relación a `ProveedorIA`).

### Relaciones:

*   **`ConfiguracionGeneral`** `1:1` **`ProveedorIA` (predeterminado)**: `ConfiguracionGeneral` tiene un campo opcional `proveedorIApredeterminadoId` que referencia al `id` de un `ProveedorIA`.
*   **`Transcripcion`** `N:1` **`ProveedorIA`**: Múltiples `Transcripcion` pueden ser generadas por un único `ProveedorIA`. Cada `Transcripcion` está asociada a un `ProveedorIA`.

## 3. Esquema físico completo escrito en sintaxis Prisma DSL

```prisma
// This is your Prisma schema file,
// learn more about it in the docs: https://pris.ly/d/prisma-schema

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

/// Represents the global application settings. There should only be one record in this table.
model ConfiguracionGeneral {
  id                         Int         @id @default(autoincrement())
  idiomaPredeterminado       String      @default("es-ES") // Default language for transcription
  activacionMicrofono        String      @default("CTRL+SHIFT+M") // Keyboard shortcut or method to activate/deactivate microphone

  // Relationship to the default AI provider
  proveedorIApredeterminadoId Int?
  proveedorIApredeterminado  ProveedorIA? @relation("DefaultAIProvider", fields: [proveedorIApredeterminadoId], references: [id])
}

/// Stores configurations for different AI transcription services.
model ProveedorIA {
  id                        Int         @id @default(autoincrement())
  nombre                    String      @unique // e.g., "Turbo Whisper Local", "Gemini API"
  tipo                      String      // e.g., "LOCAL", "API"
  apiKey                    String?     // API key for external providers
  modelo                    String?     // Specific model to use (e.g., "small", "base", "gemini-pro")
  urlBase                   String?     // Base URL for external APIs
  activo                    Boolean     @default(true) // Is this provider active/enabled?
  orden                     Int         @default(0) // Display order in UI

  // Relations
  transcripciones           Transcripcion[] // Transcriptions made using this provider
  configuracionPredeterminada ConfiguracionGeneral[] @relation("DefaultAIProvider") // Used as default in settings
}

/// Stores custom keyboard shortcuts defined by the user.
model AtajoTeclado {
  id                  Int       @id @default(autoincrement())
  nombre              String    // Descriptive name for the shortcut (e.g., "Email Signature")
  combinacionTeclas   String    @unique // The actual key combination (e.g., "Ctrl+Alt+S")
  textoAsociado       String    // The text to be inserted
  activo              Boolean   @default(true) // Is this shortcut active/enabled?
  fechaCreacion       DateTime  @default(now())
  fechaActualizacion  DateTime  @updatedAt
}

/// Stores the history of all performed transcriptions.
model Transcripcion {
  id               Int         @id @default(autoincrement())
  texto            String      @db.Text // The transcribed text. Use @db.Text for potentially long strings.
  fecha            DateTime    @default(now())
  idioma           String      // Language detected or used for this transcription (e.g., "es-ES")
  duracionAudioMs  Int?        // Duration of the transcribed audio segment in milliseconds (optional)
  confianza        Float?      // Confidence level of the transcription (optional)

  // Relationship to the AI provider that generated this transcription
  proveedorIAId    Int
  proveedorIA      ProveedorIA @relation(fields: [proveedorIAId], references: [id])

  @@index([fecha]) // Index on date for faster history retrieval
  @@index([proveedorIAId]) // Index on provider for filtering by provider
}
```

## 4. Índices, restricciones o consideraciones de rendimiento

### Índices:
Los índices son cruciales para optimizar la velocidad de consulta en la base de datos.
*   **`Transcripcion.fecha`**: Se ha añadido un índice (`@@index([fecha])`) para acelerar las consultas que filtran o ordenan el historial de transcripciones por fecha. Esto es vital para una rápida recuperación del historial.
*   **`Transcripcion.proveedorIAId`**: Un índice (`@@index([proveedorIAId])`) en la clave foránea mejora el rendimiento al buscar transcripciones específicas asociadas a un determinado proveedor de IA.
*   **`AtajoTeclado.combinacionTeclas`**: La restricción `@unique` en esta columna asegura la unicidad y crea automáticamente un índice, lo que acelera la búsqueda y validación de atajos por su combinación de teclas.
*   **`ProveedorIA.nombre`**: Similarmente, la restricción `@unique` en `nombre` garantiza que no haya proveedores de IA con el mismo nombre y mejora las búsquedas por nombre.

### Restricciones:
Las restricciones garantizan la integridad y consistencia de los datos.
*   **Claves Primarias (`@id @default(autoincrement())`)**: Cada tabla tiene una clave primaria autoincremental para identificar de forma única cada registro.
*   **Claves Foráneas (`@relation`)**: Establecen vínculos entre tablas (`Transcripcion` a `ProveedorIA`, y `ConfiguracionGeneral` a `ProveedorIA`), manteniendo la integridad referencial.
*   **Unicidad (`@unique`)**: Aplicada a `ProveedorIA.nombre` y `AtajoTeclado.combinacionTeclas` para prevenir entradas duplicadas.
*   **Valores Predeterminados (`@default`)**: Establecen valores iniciales para las columnas, como `now()` para las fechas de creación y actualización, o valores booleanos (`true`) para indicar actividad por defecto.
*   **Tipos de Datos Específicos**: El campo `texto` en `Transcripcion` utiliza `@db.Text` para asegurar que SQLite asigne un tipo de columna capaz de almacenar cadenas de texto potencialmente muy largas sin truncado.

### Consideraciones de Rendimiento:
*   **SQLite es Local**: Como base de datos local, el rendimiento estará intrínsecamente ligado al hardware del dispositivo y la carga del sistema. Las operaciones se realizan directamente en el disco local.
*   **Frecuencia de Operaciones**: Se espera un alto volumen de lecturas en `Transcripcion` (historial) y `AtajoTeclado` (uso de atajos), así como escrituras frecuentes en `Transcripcion`. Los índices están diseñados para optimizar estos escenarios.
*   **Volumen de Datos en `Transcripcion`**: La tabla `Transcripcion` puede crecer considerablemente con el tiempo. Los índices aplicados son esenciales para mantener un buen rendimiento en consultas sobre grandes volúmenes de datos. Se podría considerar implementar una funcionalidad de archivo o purga de transcripciones muy antiguas si el tamaño de la base de datos se convierte en un problema.
*   **Atomicidad de Operaciones**: Para operaciones que implican múltiples pasos o la modificación de varias tablas, el uso de transacciones (manejo por Prisma Client) asegurará que los datos permanezcan consistentes incluso si ocurren fallos inesperados.
*   **`ConfiguracionGeneral` de una Sola Fila**: Esta tabla está diseñada para tener una única fila, lo que asegura una recuperación y actualización extremadamente rápida de las configuraciones globales.