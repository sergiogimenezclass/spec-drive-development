# Especificación Técnica: Configuración de Política de Cancelación por Antelación

Esta especificación detalla la funcionalidad que permitirá al profesional definir el tiempo mínimo de antelación para que un cliente pueda cancelar un turno de forma autónoma.

---

## 1. Historia de Usuario

**Como Profesional**, quiero configurar el tiempo mínimo de antelación requerido para que un cliente pueda cancelar su turno de forma autónoma, **para** tener control sobre mi agenda y reducir cancelaciones de última hora, permitiéndome gestionar mejor mis tiempos.

---

## 2. Criterios de Aceptación Detallados

### 2.1. Configuración de la Política de Cancelación por el Profesional

*   **GIVEN** que soy un Profesional autenticado
*   **WHEN** accedo a la sección de "Configuración" de la aplicación
*   **THEN** debería ver una opción dedicada para "Política de Cancelación por Antelación".

*   **GIVEN** que estoy en la sección de "Configuración"
*   **AND** veo la opción para configurar la "Política de Cancelación por Antelación"
*   **WHEN** interactúo con esa opción (ej. haciendo clic o expandiendo la sección)
*   **THEN** debería poder ingresar un valor numérico entero que represente el número de horas, con un valor por defecto de "0".
    *   *Nota:* "0 horas" significa que el cliente puede cancelar en cualquier momento hasta el inicio del turno.

*   **GIVEN** que he ingresado un valor numérico entero para el tiempo de antelación (ej. "24") en el campo de la política de cancelación
*   **WHEN** guardo los cambios de configuración
*   **THEN** el sistema debería almacenar este valor como la política de cancelación para mi cuenta.
*   **AND** debería recibir una confirmación visual de que la configuración ha sido guardada exitosamente.

*   **GIVEN** que he configurado previamente una política de cancelación por antelación (ej. 12 horas)
*   **WHEN** vuelvo a la sección de "Política de Cancelación por Antelación" en "Configuración"
*   **THEN** debería ver mi valor previamente guardado (ej. "12") precargado en el campo.

### 2.2. Aplicación de la Política en la Autogestión del Cliente

*   **GIVEN** que un Profesional ha configurado una política de cancelación de *N* horas (ej. 24 horas)
*   **AND** un Cliente tiene un turno reservado para una fecha y hora específicas (ej. 2024-12-01 10:00 AM)
*   **AND** el Cliente accede al enlace de autogestión para cancelar su turno.
*   **WHEN** la hora actual es *más de N horas* antes del inicio del turno (ej. 2024-11-30 09:59 AM, si N=24)
*   **THEN** el Cliente debería ver la opción de cancelar el turno y poder hacerlo exitosamente.
*   **AND** tras la cancelación exitosa, el Cliente y el Profesional deberían recibir las notificaciones de cancelación por email.

*   **GIVEN** que un Profesional ha configurado una política de cancelación de *N* horas (ej. 24 horas)
*   **AND** un Cliente tiene un turno reservado para una fecha y hora específicas (ej. 2024-12-01 10:00 AM)
*   **AND** el Cliente accede al enlace de autogestión para cancelar su turno.
*   **WHEN** la hora actual es *N horas o menos* antes del inicio del turno (ej. 2024-11-30 10:00 AM o más tarde, si N=24)
*   **THEN** el Cliente NO debería ver la opción de cancelar el turno de forma autónoma.
*   **AND** en su lugar, debería ver un mensaje claro que indique que el tiempo límite para la cancelación autónoma ha expirado y que debe contactar al Profesional directamente para cualquier cambio.

*   **GIVEN** que el Profesional ha configurado la política de cancelación por antelación a "0 horas" (o no la ha configurado y se aplica el valor por defecto de 0)
*   **WHEN** el Cliente intenta cancelar su turno en cualquier momento antes del `startTime` del mismo
*   **THEN** el Cliente siempre debería poder cancelar el turno de forma autónoma.

---

## 3. Casos de Error y Casos Borde (Edge cases)

### 3.1. Errores en la Configuración (Profesional)

*   **P-ERR-01: Entrada Inválida en la Configuración:**
    *   **Escenario:** El profesional intenta guardar un valor no numérico, un número negativo, o un número decimal para la política de antelación.
    *   **Comportamiento esperado:** El sistema debe mostrar un mensaje de error claro (ej. "El valor debe ser un número entero mayor o igual a 0") y no guardar la configuración hasta que la entrada sea válida.

*   **P-ERR-02: Fallo de Conexión o Servidor al Guardar:**
    *   **Escenario:** El profesional intenta guardar la configuración de la política, pero hay un problema de conexión a internet o un error en el servidor que impide la actualización.
    *   **Comportamiento esperado:** El sistema debe informar al profesional que no se pudo guardar la configuración e indicar que intente de nuevo más tarde. La configuración anterior debe persistir si la nueva no pudo ser guardada correctamente.

### 3.2. Casos Borde y Errores en la Autogestión (Cliente)

*   **C-EDGE-01: Cancelación Exactamente en el Límite de Antelación:**
    *   **Escenario:** La política de cancelación configurada es de *N* horas. Un cliente intenta cancelar su turno *exactamente N horas* antes del `startTime` del turno.
    *   **Comportamiento esperado:** La cancelación debería ser permitida. La política se interpreta como que el cliente puede cancelar si el tiempo restante hasta el turno es *mayor o igual* a la política configurada.

*   **C-EDGE-02: Intento de Cancelación de Turno Ya Iniciado o Pasado:**
    *   **Escenario:** Un cliente intenta cancelar un turno que ya ha comenzado o que ya ha transcurrido.
    *   **Comportamiento esperado:** Independientemente de la política de antelación, el sistema debe informar al cliente que el turno no puede ser cancelado de forma autónoma porque ya ha iniciado/pasado. Este mensaje debe tener prioridad sobre el mensaje de la política de cancelación por antelación.

*   **C-ERR-03: Enlace de Autogestión Inválido o No Encontrado:**
    *   **Escenario:** Un cliente intenta usar un enlace de autogestión de turno que es inválido, ha sido alterado, o el turno asociado a ese enlace ya no existe o no corresponde (ej. por un borrado o modificación del profesional).
    *   **Comportamiento esperado:** El sistema debe mostrar un mensaje de error claro indicando que el enlace no es válido o que el turno no se encontró, y sugerir contactar al profesional.