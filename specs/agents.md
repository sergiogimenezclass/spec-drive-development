# Guía para Agentes de Código de IA: Aplicación de Gestión de Turnos

Este documento establece las directrices y el contexto para cualquier Agente de Código de IA involucrado en el desarrollo de la aplicación de gestión de turnos. Es fundamental adherirse a estas instrucciones para garantizar la coherencia, calidad y cumplimiento de los requisitos del proyecto.

---

## 1. Contexto Básico de la Aplicación

El proyecto consiste en una **aplicación web de gestión de citas y turnos** diseñada para un **único profesional o proveedor de servicios** (ej. peluquero, psicólogo, profesor particular). Su propósito principal es permitir que este profesional gestione su disponibilidad y que sus clientes puedan reservar turnos de manera sencilla.

### Características Clave:
*   **Modelo de Usuario:** Es una aplicación mono-usuario para el profesional. Los clientes interactúan públicamente para reservar.
*   **Funcionalidades Core:**
    *   **Autenticación:** Acceso del profesional mediante Email y Contraseña.
    *   **Gestión de Disponibilidad:** El profesional puede configurar sus horarios y servicios disponibles.
    *   **Reserva de Turnos:** Clientes pueden ver la disponibilidad y reservar turnos directamente.
    *   **Gestión de Turnos (Profesional):** El profesional puede visualizar, cancelar y reagendar los turnos reservados.
    *   **Gestión de Turnos (Cliente):** Los clientes pueden cancelar o reagendar sus propios turnos reservados (si la política lo permite y está implementado en las especificaciones).
*   **Persistencia de Datos:** Se utilizará una base de datos **Relacional (PostgreSQL/MySQL)**.
*   **Notificaciones:** Las interacciones clave (confirmación de reserva, cancelación, reagendamiento) se comunicarán **únicamente por Email**.
*   **Pagos:** **No se contempla la integración de pagos** por turno en esta fase.
*   **Despliegue:** La aplicación está diseñada para ser desplegada en entornos de **servidor VPS o hosting compartido**, lo que implica optimización de recursos y evitar dependencias complejas.

### Actores Principales:
*   **Profesional (Proveedor de Servicio):** Gestiona la aplicación, configura servicios y disponibilidad, y maneja los turnos.
*   **Cliente (Reservador de Turno):** Accede a la interfaz pública para ver disponibilidad y reservar turnos.

---

## 2. Estilos de Codificación Explícitos

La adherencia a estos estilos es crítica para mantener la legibilidad y el mantenimiento del código.

### General:
*   **Indentación:** 2 espacios para todo el código (JavaScript/TypeScript, HTML, CSS, JSON).
*   **Nombres Descriptivos:** Utilizar nombres de variables, funciones y clases que sean claros y describan su propósito.
*   **Comentarios:** Incluir comentarios explicativos para lógica compleja o decisiones de diseño no obvias.
*   **Archivos:** Cada archivo debe tener un propósito singular y claro.

### TypeScript / JavaScript:
*   **Variables y Funciones:** `camelCase` (ej. `miVariable`, `calcularTotal`).
*   **Clases, Interfaces y Tipos:** `PascalCase` (ej. `Usuario`, `ITurno`, `ReservaService`).
*   **Constantes Globales/Enum Members:** `UPPER_SNAKE_CASE` (ej. `MAX_INTENTOS`, `ESTADO_PENDIENTE`).
*   **Nombres de Archivos:**
    *   Módulos, componentes, servicios: `kebab-case.ts` (ej. `turno-card.component.ts`, `auth.service.ts`).
    *   Clases principales, modelos, interfaces: `PascalCase.ts` (ej. `Turno.model.ts`, `IUser.interface.ts`).
*   **Tipado:** Usar tipado explícito siempre que sea posible para mejorar la claridad y la capacidad de refactorización.
*   **Uso de `const` y `let`:** Preferir `const` para variables que no cambian y `let` para las que sí, evitando `var`.

### Base de Datos (SQL y ORM):
*   **Nombres de Tablas:** `snake_case_plural` (ej. `usuarios`, `turnos_reservados`).
*   **Nombres de Columnas:** `snake_case` (ej. `nombre_usuario`, `fecha_reserva`).
*   **Claves Primarias:** `id` para todas las tablas.
*   **Claves Foráneas:** `nombre_tabla_singular_id` (ej. `usuario_id`, `servicio_id`).
*   **Migraciones:** Utilizar un sistema de migraciones para la gestión de esquemas de base de datos.

---

## 3. Reglas Técnicas de Comportamiento Crítico

Estas reglas definen el comportamiento técnico esperado y son **no negociables**.

1.  **Integridad Transaccional de Base de Datos:**
    *   Todas las operaciones que impliquen la modificación de datos críticos (creación, actualización o eliminación de turnos, gestión de disponibilidad del profesional) deben ejecutarse **dentro de una transacción de base de datos**. Esto asegura la atomicidad y la consistencia de los datos.

2.  **Manejo Centralizado de Errores (API REST):**
    *   Se debe implementar un **middleware centralizado para el manejo de errores** en el backend. Este middleware debe capturar excepciones y errores, estandarizar el formato de las respuestas (JSON) y asignar códigos de estado HTTP apropiados (ej. `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `500 Internal Server Error`). Las respuestas de error no deben exponer detalles internos sensibles del servidor o la base de datos.

3.  **Validación Rigurosa de Entrada:**
    *   Toda la entrada de datos recibida del cliente (a través de la API) debe ser **validada exhaustivamente en el backend** antes de cualquier procesamiento o persistencia. Esto incluye tipos de datos, formatos, rangos y la prevención de inyecciones (SQL, XSS, etc.).

4.  **Control de Acceso (Autorización):**
    *   Implementar un sistema de autorización robusto a nivel de API. Todas las rutas o endpoints que requieran permisos específicos deben ser protegidos para garantizar que solo los usuarios autenticados y autorizados puedan realizar las acciones correspondientes (ej. solo el profesional puede modificar su disponibilidad; los clientes solo pueden reservar y gestionar sus propios turnos).

5.  **Prohibición de Librerías/Paquetes No Aprobados:**
    *   **No se permite la incorporación de librerías, paquetes o dependencias externas que no hayan sido explícitamente revisadas y aprobadas** por el arquitecto o líder técnico del proyecto. Esto es vital para mantener la seguridad, el rendimiento y la consistencia del stack tecnológico.

6.  **Seguridad de Autenticación:**
    *   Las contraseñas de usuario deben ser almacenadas de forma segura utilizando algoritmos de hash y salting robustos (ej. bcrypt). Las credenciales de acceso no deben ser almacenadas en texto plano en ninguna parte.

7.  **Diseño RESTful de API:**
    *   La API debe seguir los principios RESTful, utilizando verbos HTTP semánticos (GET, POST, PUT, DELETE), URLs descriptivas (preferiblemente plurales para colecciones, ej. `/api/turnos`) y respuestas en formato JSON estándar.

8.  **Gestión de Dependencias (Frontend/Backend):**
    *   Mantener los archivos `package.json` (y equivalentes) limpios, con dependencias mínimas y bien justificadas. Evitar dependencias que añadan una sobrecarga innecesaria al proyecto.

---

## 4. Fuente Única de Verdad (SSOT)

La **única y exclusiva fuente de verdad** para todos los requisitos funcionales, no funcionales, reglas de negocio y especificaciones técnicas son los documentos y artefactos contenidos en esta misma carpeta y sus subcarpetas.

*   **Cualquier ambigüedad, inconsistencia o necesidad de aclaración debe ser inmediatamente escalada** al Staff Software Architect o al Product Owner.
*   **No se deben tomar decisiones de diseño o implementación basadas en suposiciones** no documentadas en estas especificaciones.
*   Las decisiones de desarrollo deben priorizar la implementación precisa de las especificaciones proporcionadas.

---