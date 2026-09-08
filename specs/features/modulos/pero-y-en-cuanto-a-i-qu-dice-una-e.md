# Especificación Técnica: Pero, ¿y en cuanto a I, qu dice una e...

## 1. Historia de Usuario (User Story)

**ID:** US-001

**Formato:** Como **Profesional**, quiero **poder visualizar de manera clara y organizada todos los turnos reservados en mi agenda**, para **planificar mi día, semana o mes de trabajo de manera eficiente y evitar conflictos de horarios**.

**Formato:** Como **Cliente**, quiero **poder reservar un turno de manera autónoma seleccionando un servicio, una fecha y un horario disponible**, para **asegurar mi cita sin necesidad de contactar directamente al profesional**.

**Formato:** Como **Cliente**, quiero **recibir una confirmación por email con los detalles de mi turno y un enlace seguro para autogestionar mi cita**, para **poder cancelar o reagendar mi turno de manera conveniente si surge algún imprevisto**.

**Formato:** Como **Profesional**, quiero **poder definir mi disponibilidad semanal y bloquear franjas horarias específicas**, para **controlar exactamente cuándo puedo recibir clientes y cuándo no**.

**Formato:** Como **Profesional**, quiero **configurar los servicios que ofrezco con su duración y descripción**, para **que los clientes puedan elegir correctamente el tipo de cita que necesitan**.

---

## 2. Criterios de Aceptación Detallados

### CA-001: Reserva de Turno Exitosa

**Dado** que un cliente accede a la página pública de reservas del profesional,
**Cuando** selecciona un servicio, elige una fecha y un horario disponible, ingresa sus datos de contacto (nombre, email y teléfono opcional) y confirma la reserva,
**Entonces** el sistema debe:
- Crear el turno con estado `BOOKED`.
- Enviar un email de confirmación al cliente con los detalles del turno y un enlace único de autogestión.
- Enviar un email de notificación al profesional informando de la nueva reserva.
- Mostrar un mensaje de éxito al cliente indicando que su turno ha sido reservado.

### CA-002: Visualización de Agenda del Profesional

**Dado** que el profesional ha iniciado sesión en el sistema,
**Cuando** accede a su panel de control,
**Entonces** debe poder visualizar su agenda en una vista de calendario con opciones de vista diaria, semanal y mensual, mostrando todos los turnos reservados con su estado, servicio, cliente y horario correspondiente.

### CA-003: Configuración de Disponibilidad Semanal

**Dado** que el profesional está autenticado en el sistema,
**Cuando** accede a la sección de configuración de disponibilidad,
**Entonces** debe poder:
- Definir para cada día de la semana (lunes a domingo) un horario de inicio y fin de trabajo.
- Establecer bloques de indisponibilidad (ej. pausas, almuerzo, reuniones) dentro de su horario laboral.
- Marcar días completos como no disponibles (ej. vacaciones, feriados).
- Guardar los cambios realizados.

**Y** el sistema debe validar que no existan solapamientos entre bloques de indisponibilidad y que los horarios sean lógicamente coherentes (hora de fin posterior a hora de inicio).

### CA-004: Cancelación de Turno por el Cliente

**Dado** que un cliente ha recibido un email de confirmación con un enlace de autogestión,
**Cuando** hace clic en el enlace de cancelación y confirma su intención de cancelar,
**Entonces** el sistema debe:
- Verificar que el turno existe y está en estado `BOOKED`.
- Verificar que la cancelación se realiza antes del límite de tiempo configurado por el profesional (ej. 24 horas antes del turno).
- Cambiar el estado del turno a `CANCELLED`.
- Liberar el slot de disponibilidad para que pueda ser reservado por otro cliente.
- Enviar un email de confirmación de cancelación al cliente.
- Enviar un email de notificación al profesional informando de la cancelación.

### CA-005: Reagendamiento de Turno por el Cliente

**Dado** que un cliente ha recibido un email de confirmación con un enlace de autogestión,
**Cuando** hace clic en el enlace de reagendamiento, selecciona un nuevo horario disponible y confirma el cambio,
**Entonces** el sistema debe:
- Verificar que el turno existe y está en estado `BOOKED`.
- Verificar que el reagendamiento se realiza antes del límite de tiempo configurado por el profesional.
- Verificar que el nuevo horario seleccionado está disponible.
- Actualizar el turno con la nueva fecha y hora de inicio y fin.
- Enviar un email de confirmación al cliente con los nuevos detalles del turno.
- Enviar un email de notificación al profesional informando del reagendamiento.

### CA-006: Gestión de Turnos por el Profesional

**Dado** que el profesional está autenticado y visualiza su agenda,
**Cuando** selecciona un turno específico,
**Entonces** debe poder:
- Ver los detalles completos del turno (cliente, servicio, fecha, hora, estado, notas).
- Cancelar el turno (lo que notificará al cliente por email).
- Reagendar el turno a un nuevo horario disponible (lo que notificará al cliente por email).
- Marcar el turno como `COMPLETED` o `CANCELLED` según corresponda.

### CA-007: Configuración de Servicios

**Dado** que el profesional está autenticado,
**Cuando** accede a la sección de servicios,
**Entonces** debe poder:
- Crear un nuevo servicio especificando nombre, descripción y duración en minutos.
- Editar un servicio existente.
- Eliminar un servicio que no tenga turnos asociados (si tiene turnos, el sistema debe impedir la eliminación).

**Y** el sistema debe validar que el nombre del servicio sea único para ese profesional.

---

## 3. Casos de Error y Casos Borde (Edge Cases)

### 3.1. Errores de Red y Conectividad

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-001 | El cliente intenta reservar un turno pero pierde la conexión a internet durante el proceso | El sistema debe mostrar un mensaje de error indicando problemas de conectividad y sugerir reintentar la operación. No debe crearse un turno parcial o duplicado. |
| EC-002 | El profesional intenta guardar cambios en su disponibilidad pero la conexión falla | El sistema debe mostrar un mensaje de error y no persistir cambios parciales. Los datos deben permanecer en su estado anterior. |
| EC-003 | El email de confirmación no se envía correctamente después de una reserva exitosa | El sistema debe registrar el error de envío de email en logs internos. El turno debe crearse correctamente, pero se debe mostrar una advertencia al cliente indicando que no se pudo enviar la confirmación por email y que contacte al profesional si necesita más información. |

### 3.2. Entradas Inválidas y Validación de Datos

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-004 | El cliente ingresa un email con formato inválido (ej. "usuario@") | El sistema debe mostrar un mensaje de error indicando que el email no es válido y no permitir continuar con la reserva. |
| EC-005 | El cliente ingresa un nombre vacío o solo espacios | El sistema debe mostrar un mensaje de error indicando que el nombre es obligatorio. |
| EC-006 | El cliente ingresa un número de teléfono con caracteres no numéricos (ej. "abc123") | El sistema debe mostrar un mensaje de error indicando que el teléfono debe contener solo números. Si el teléfono es opcional, se debe permitir dejarlo vacío. |
| EC-007 | El profesional intenta crear un servicio con duración negativa o cero | El sistema debe mostrar un mensaje de error indicando que la duración debe ser un número positivo mayor a cero. |
| EC-008 | El profesional intenta configurar un horario de trabajo donde la hora de fin es anterior a la hora de inicio | El sistema debe mostrar un mensaje de error indicando que la hora de fin debe ser posterior a la hora de inicio. |
| EC-009 | El profesional intenta crear un servicio con un nombre que ya existe | El sistema debe mostrar un mensaje de error indicando que ya existe un servicio con ese nombre. |

### 3.3. Violaciones de Reglas de Negocio

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-010 | Un cliente intenta reservar un turno en un horario que ya está ocupado por otro turno | El sistema debe mostrar un mensaje de error indicando que el horario seleccionado ya no está disponible y sugerir horarios alternativos. |
| EC-011 | Un cliente intenta reservar un turno en un horario fuera de la disponibilidad del profesional (ej. domingo cuando el profesional no trabaja) | El sistema debe mostrar un mensaje de error indicando que el horario no está disponible. |
| EC-012 | Un cliente intenta reservar un turno con menos antelación que el límite mínimo configurado (ej. intenta reservar para dentro de 15 minutos cuando el mínimo es 1 hora) | El sistema debe mostrar un mensaje de error indicando que no se puede reservar con tan poca antelación y sugerir el próximo horario disponible. |
| EC-013 | Un cliente intenta cancelar un turno después del límite de tiempo permitido (ej. intenta cancelar 2 horas antes cuando el límite es 24 horas) | El sistema debe mostrar un mensaje de error indicando que ya no es posible cancelar el turno de manera autónoma y que debe contactar al profesional directamente. |
| EC-014 | Un cliente intenta reagendar un turno después del límite de tiempo permitido | El sistema debe mostrar un mensaje de error indicando que ya no es posible reagendar el turno de manera autónoma y que debe contactar al profesional directamente. |
| EC-015 | Un cliente intenta cancelar o reagendar un turno que ya fue cancelado o completado | El sistema debe mostrar un mensaje de error indicando que el turno ya no está activo y no se puede modificar. |
| EC-016 | Dos clientes intentan reservar el mismo slot de tiempo simultáneamente | El sistema debe manejar la concurrencia de manera que solo uno de los dos pueda completar la reserva. El segundo cliente debe recibir un mensaje de error indicando que el horario ya no está disponible. |

### 3.4. Casos Borde de Fechas y Horarios

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-017 | Un cliente intenta reservar un turno para una fecha en el pasado | El sistema debe mostrar un mensaje de error indicando que no se pueden reservar turnos en fechas pasadas. |
| EC-018 | Un cliente intenta reservar un turno para una fecha muy lejana en el futuro (ej. más de 6 meses) | El sistema debe mostrar un mensaje de error indicando que la fecha está fuera del rango permitido de reserva (si se configura un límite máximo). |
| EC-019 | El profesional configura un bloque de indisponibilidad que cubre exactamente el mismo horario que un turno ya reservado | El sistema debe impedir la creación del bloque de indisponibilidad si hay turnos activos en ese rango, o debe notificar al profesional que existen turnos que se verán afectados y requerir confirmación para proceder. |
| EC-020 | El profesional elimina un día completo de disponibilidad (ej. elimina los lunes) y existen turnos reservados para ese día | El sistema debe impedir la eliminación si hay turnos activos en ese día, o debe notificar al profesional y requerir que cancele o reagende esos turnos primero. |
| EC-021 | El profesional cambia la duración de un servicio que ya tiene turnos reservados | El sistema debe permitir el cambio solo para futuros turnos. Los turnos existentes deben mantener su duración original o el sistema debe solicitar al profesional que reagende los turnos afectados. |
| EC-022 | Un cliente intenta reservar un turno que cruza el límite del horario de trabajo (ej. servicio de 60 minutos y el profesional termina a las 17:00, el cliente intenta reservar a las 16:30) | El sistema debe impedir la reserva y mostrar un mensaje indicando que el servicio no cabe en el horario disponible, sugiriendo el último horario posible (16:00). |

### 3.5. Casos Borde de Autenticación y Sesión

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-023 | El profesional intenta iniciar sesión con credenciales incorrectas | El sistema debe mostrar un mensaje de error genérico indicando que el email o la contraseña son incorrectos, sin revelar cuál de los dos es el incorrecto. |
| EC-024 | El profesional intenta acceder a una ruta protegida sin estar autenticado | El sistema debe redirigir al profesional a la página de inicio de sesión. |
| EC-025 | La sesión del profesional expira mientras está trabajando en la configuración | El sistema debe redirigir al profesional a la página de inicio de sesión y mostrar un mensaje indicando que la sesión ha expirado. Los cambios no guardados se pierden. |
| EC-026 | El profesional intenta registrarse con un email que ya existe | El sistema debe mostrar un mensaje de error indicando que ya existe una cuenta con ese email. |

### 3.6. Casos Borde de Notificaciones

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-027 | El email del cliente es inválido o no existe y el sistema no puede enviar la confirmación | El turno debe crearse correctamente, pero el sistema debe registrar el fallo de envío. El profesional debe poder ver en el panel que el cliente no recibió confirmación. |
| EC-028 | El profesional cancela un turno y el email de notificación al cliente falla | El turno debe cancelarse correctamente. El sistema debe registrar el fallo y mostrar una advertencia al profesional indicando que el cliente podría no haber sido notificado. |
| EC-029 | El enlace de autogestión del cliente expira (si se implementa expiración) | El sistema debe mostrar un mensaje indicando que el enlace ha expirado y que el cliente debe contactar al profesional para gestionar su turno. |

### 3.7. Casos Borde de Integridad de Datos

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-030 | Un cliente intenta acceder al enlace de autogestión de un turno que no existe (enlace manipulado o incorrecto) | El sistema debe mostrar un mensaje de error indicando que el turno no fue encontrado. |
| EC-031 | Un cliente intenta cancelar un turno que ya fue cancelado previamente | El sistema debe mostrar un mensaje indicando que el turno ya no está activo. |
| EC-032 | El profesional intenta eliminar un servicio que tiene turnos asociados (incluso turnos cancelados o completados) | El sistema debe impedir la eliminación y mostrar un mensaje indicando que el servicio tiene turnos asociados y no puede ser eliminado. |
| EC-033 | El sistema recibe una solicitud de reserva duplicada (el cliente hace doble clic en el botón de confirmar) | El sistema debe detectar la solicitud duplicada y solo crear un turno. La segunda solicitud debe ser ignorada o devolver un mensaje indicando que la reserva ya fue procesada. |

### 3.8. Casos Borde de Disponibilidad y Concurrencia

| ID | Caso | Comportamiento Esperado |
|----|------|------------------------|
| EC-034 | El profesional modifica su disponibilidad mientras un cliente está en medio del proceso de reserva | El sistema debe validar la disponibilidad en el momento de la confirmación final. Si el horario ya no está disponible, se debe mostrar un error al cliente. |
| EC-035 | El profesional tiene múltiples bloques de indisponibilidad en un mismo día | El sistema debe permitir configurar múltiples bloques siempre que no se solapen entre sí ni con los turnos existentes. |
| EC-036 | El profesional no configura ningún horario de trabajo para un día específico | El sistema debe tratar ese día como no disponible y no mostrar horarios para reserva. |
| EC-037 | El profesional configura horarios de trabajo que cruzan la medianoche (ej. de 22:00 a 02:00) | El sistema debe manejar este caso de manera especial, interpretando que el horario se extiende al día siguiente. Se debe validar que no existan conflictos con los horarios del día siguiente. |

---

## 4. Reglas de Negocio Adicionales

### RN-01: Límite de Antelación para Reservas

El profesional debe poder configurar un tiempo mínimo de antelación para nuevas reservas (ej. no se pueden reservar turnos con menos de 1 hora de anticipación). Este valor debe ser configurable y aplicarse a todas las reservas.

### RN-02: Límite de Antelación para Cancelación/Reagendamiento

El profesional debe poder configurar un tiempo límite antes del turno para que los clientes puedan cancelar o reagendar de manera autónoma (ej. 24 horas antes). Después de este límite, solo el profesional puede realizar cambios.

### RN-03: Política de Turnos Cancelados

Los turnos cancelados deben mantener su registro en la base de datos con estado `CANCELLED` y no deben ser eliminados físicamente. Esto permite mantener un historial auditable.

### RN-04: Política de Turnos Completados

Los turnos que han sido realizados deben marcarse como `COMPLETED` por el profesional. Una vez completados, no pueden ser cancelados ni reagendados.

### RN-05: Notificaciones Obligatorias

Toda acción significativa sobre un turno (reserva, cancelación, reagendamiento, cambio por parte del profesional) debe generar notificaciones por email tanto al cliente como al profesional.

### RN-06: Unicidad de Datos del Profesional

La aplicación está diseñada para un único profesional. No se permite la creación de múltiples cuentas de profesional en la misma instancia de la aplicación.

### RN-07: Sin Pagos Integrados

La aplicación no debe incluir ni procesar ningún tipo de pago. La funcionalidad se limita exclusivamente a la gestión de turnos y agenda.

---

## 5. Consideraciones Técnicas Adicionales

### 5.1. Manejo de Zonas Horarias

- Todos los horarios deben almacenarse en UTC en la base de datos.
- La aplicación debe convertir los horarios a la zona horaria del profesional para mostrar la agenda y la disponibilidad.
- Los clientes deben ver los horarios en la zona horaria del profesional (no en la suya propia) para evitar confusiones.

### 5.2. Seguridad

- Las contraseñas deben almacenarse hasheadas utilizando un algoritmo seguro (ej. bcrypt).
- Los enlaces de autogestión del cliente deben ser únicos y no adivinables (utilizar tokens aleatorios seguros).
- Todas las rutas del panel del profesional deben estar protegidas por autenticación.
- Se debe implementar protección contra CSRF y validación de entrada de datos.

### 5.3. Rendimiento

- Las consultas de disponibilidad deben optimizarse utilizando los índices definidos en el esquema de base de datos.
- La visualización del calendario debe cargar los turnos por rangos de fechas para evitar sobrecargar la interfaz.
- Se debe implementar paginación o carga incremental si el volumen de turnos crece significativamente.

### 5.4. Accesibilidad y Usabilidad

- La interfaz debe ser responsive y funcionar correctamente en dispositivos móviles, tablets y desktop.
- Los mensajes de error deben ser claros y accionables, indicando al usuario qué hacer a continuación.
- Los formularios deben incluir validación en tiempo real cuando sea posible para mejorar la experiencia del usuario.