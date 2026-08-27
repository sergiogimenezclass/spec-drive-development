### Feature: Manejo de Webhooks de Mercado Pago

**Categoría/Carpeta:** `payments`

---

### Clarificación sobre el Contexto del Proyecto y Reglas de Negocio

**Importante:** El contexto general del proyecto, específicamente la "Regla de Negocio Crítica e Inquebrantable #6: No Permite Pagos Directos", establece que la aplicación no debe integrar ni procesar pagos directamente. La implementación del "Manejo de Webhooks de Mercado Pago" implica inherentemente la gestión del estado de pagos externos, lo que requiere una adaptación o interpretación de dicha regla.

Para esta especificación, se asume la siguiente interpretación de la regla de negocio:

*   La aplicación **no gestionará directamente** datos sensibles de pago (como números de tarjeta de crédito, etc.) ni procesará transacciones monetarias dentro de su interfaz de usuario o base de datos.
*   Sin embargo, la aplicación **sí se integrará con un proveedor de pagos externo (Mercado Pago)** para **recibir notificaciones (webhooks)** sobre el estado de pagos que han sido iniciados y gestionados completamente por dicho proveedor.
*   Esto habilita un flujo donde el profesional podría generar un enlace de pago de Mercado Pago (potencialmente desde la aplicación en una fase futura, o manualmente) y enviarlo al cliente. La aplicación, a través de los webhooks, utilizará estas notificaciones para **actualizar el estado de un turno asociado** una vez que el pago sea confirmado, rechazado o devuelto.

Esta característica requerirá modificaciones en el modelo de datos `Appointment` para incluir un identificador de pago externo y una expansión en el `AppointmentStatus` para reflejar estados de pago relevantes.

---

### 1. Historia de Usuario (User Story)

*   **Como Profesional,**
*   **Quiero** que la aplicación reciba y procese automáticamente las notificaciones de estado de pago (webhooks) de Mercado Pago para los turnos que requieren pago,
*   **Para** mantener el estado de los turnos actualizado en tiempo real sin intervención manual, y así saber si un cliente ha pagado por su reserva sin tener que consultar Mercado Pago manualmente.

---

### 2. Criterios de Aceptación Detallados

#### 2.1. Configuración y Pre-requisitos

*   **Dado** que el profesional ha configurado la URL de webhook en su cuenta de Mercado Pago para apuntar a nuestro endpoint `POST /api/webhooks/mercadopago`.
*   **Dado** que cada turno en el sistema `AgendaPro Simple` que requiere pago tiene un campo `mpPaymentId` (identificador del pago de Mercado Pago) asociado en la base de datos de `Appointment`.
    *   *(Nota: La funcionalidad para generar este `mpPaymentId` y enlazarlo a un `Appointment` se abordará en una feature separada. Para esta feature, asumimos que el `mpPaymentId` ya existe en el `Appointment` si el turno está asociado a un pago de Mercado Pago).*
*   **Dado** que el `AppointmentStatus` de la aplicación incluye nuevos estados como `PENDING_PAYMENT` y `REJECTED_PAYMENT`.

#### 2.2. Recepción y Validación del Webhook

*   **Dado** que Mercado Pago envía una notificación de webhook a la URL configurada.
*   **Cuando** el endpoint `POST /api/webhooks/mercadopago` recibe una solicitud,
*   **Entonces** el sistema debe:
    *   Responder con un `HTTP 200 OK` inmediatamente (en menos de 1 segundo) a Mercado Pago para evitar reintentos innecesarios por parte del originador, antes de iniciar el procesamiento asíncrono del contenido del webhook.
    *   Validar la firma del webhook (`X-Signature` o mecanismo de seguridad equivalente de Mercado Pago) para asegurar que la solicitud proviene de una fuente legítima de Mercado Pago y que el payload no ha sido alterado.
        *   **Dado** que la firma del webhook es válida, **Entonces** se procede con el procesamiento del contenido.
        *   **Dado** que la firma del webhook es inválida, **Entonces** el sistema debe registrar un evento de seguridad, responder con `HTTP 401 Unauthorized` y no procesar el webhook.
    *   Registrar el contenido completo del payload del webhook en un log de eventos (por ejemplo, en un servicio de logs o base de datos específica) para fines de auditoría, depuración y reprocesamiento si fuera necesario.

#### 2.3. Procesamiento del Estado de Pago

*   **Dado** un webhook válido recibido de Mercado Pago con el evento `payment.updated` (u otro evento relevante según la documentación de MP para el estado de pago).
*   **Cuando** el sistema extrae el `id` del recurso de pago (`data.id`) del payload del webhook,
*   **Entonces** el sistema debe:
    1.  **Consultar la API de Mercado Pago:** Utilizar el `id` del pago extraído para obtener los detalles completos y actualizados del pago directamente desde la API de Mercado Pago. Esta es la fuente de información más fidedigna y prioritaria sobre el estado real del pago.
        *   **Dado** que la consulta a la API de Mercado Pago falla (ej. error de red, timeout, pago no encontrado con el `id` provisto), **Entonces** el sistema debe implementar una estrategia de reintentos con backoff exponencial. Si persiste el error tras los reintentos, registrar un error crítico, notificar al profesional (o al equipo de soporte vía email) y marcar el evento para posible revisión manual.
    2.  **Identificar el Turno Asociado:** Buscar en la base de datos un `Appointment` cuyo campo `mpPaymentId` coincida con el `id` del pago obtenido de Mercado Pago.
        *   **Dado** que no se encuentra ningún `Appointment` con ese `mpPaymentId`, **Entonces** el sistema debe registrar un warning (indicando un posible pago no asociado o un `mpPaymentId` inválido/desactualizado), responder `HTTP 200 OK`, pero el procesamiento para ese webhook finaliza sin error crítico para el webhook en sí.
    3.  **Actualizar el Estado del Turno:** Basándose en el `payment_status` y `status_detail` de los detalles del pago obtenidos directamente de la API de Mercado Pago, actualizar el `status` del `Appointment` de la siguiente manera:
        *   **Si `payment_status` es `approved`:**
            *   **Entonces** el `Appointment.status` debe actualizarse a `BOOKED`.
            *   **Entonces** se debe enviar una notificación por email al profesional y al cliente confirmando la reserva y el pago.
        *   **Si `payment_status` es `pending` (y `status_detail` indica una espera de pago):**
            *   **Entonces** el `Appointment.status` debe actualizarse a `PENDING_PAYMENT` (si no lo está ya).
            *   **Entonces** no se envía ninguna notificación adicional por esta transición, ya que el turno ya fue marcado como `PENDING_PAYMENT` al generarse el link de pago.
        *   **Si `payment_status` es `rejected` o `cancelled` (por Mercado Pago):**
            *   **Entonces** el `Appointment.status` debe actualizarse a `REJECTED_PAYMENT`.
            *   **Entonces** se debe enviar una notificación por email al profesional y al cliente informando que el pago fue rechazado y el turno no pudo ser confirmado, sugiriendo pasos a seguir (ej. reintentar pago, contactar al profesional).
        *   **Si `payment_status` es `refunded`:**
            *   **Entonces** se registra un log informativo sobre el reembolso asociado al `Appointment`. El `Appointment.status` no cambia automáticamente a `CANCELLED` si el turno ya se había realizado (`COMPLETED`) o estaba `BOOKED` antes del reembolso. Se requerirá revisión manual si se desea cambiar el estado del turno para estos casos.
            *   **Entonces** se debe enviar una notificación por email al profesional y al cliente informando sobre el reembolso realizado.
    4.  **Idempotencia:**
        *   **Dado** que el sistema ya ha procesado previamente un webhook para un `payment_id` específico y el estado del `Appointment` ya refleja el estado final y más reciente de ese pago (ej. `BOOKED` para un pago aprobado o `REJECTED_PAYMENT` para un pago rechazado).
        *   **Cuando** se recibe un nuevo webhook para el mismo `payment_id` con un estado que no implica un cambio de estado significativo o final posterior (ej. `approved` de nuevo cuando ya está `BOOKED`),
        *   **Entonces** el sistema debe reconocer que la acción ya fue realizada. Solo registrará el evento como procesado sin realizar actualizaciones duplicadas en la base de datos o enviar notificaciones redundantes.

---

### 3. Casos de Error y Casos Borde (Edge cases)

1.  **Webhook con Formato Inválido / Malicioso:**
    *   **Escenario:** El `payload` del webhook recibido no es un JSON válido, está corrupto, o no contiene los campos esperados (`type`, `data.id`).
    *   **Comportamiento Esperado:** El sistema debe registrar un error de validación, responder con `HTTP 400 Bad Request` y no procesar el contenido del webhook.

2.  **Identificador de Pago de Mercado Pago (MP) Ausente o Inválido en el Webhook:**
    *   **Escenario:** El webhook es válido en su estructura JSON y firma, pero el campo `data.id` (que contiene el `payment_id`) está vacío, no es un string, o tiene un formato que no corresponde a un ID de pago de Mercado Pago.
    *   **Comportamiento Esperado:** El sistema debe registrar un warning, responder con `HTTP 200 OK` (para no generar reintentos innecesarios de MP), pero no procederá con la búsqueda ni actualización de ningún `Appointment` ya que el identificador clave no es utilizable.

3.  **`mpPaymentId` No Encontrado en ningún `Appointment` de la Base de Datos:**
    *   **Escenario:** El webhook es válido, el `payment_id` de MP es válido y se recuperan los detalles del pago de la API de MP, pero no hay ningún `Appointment` en la base de datos local con un `mpPaymentId` coincidente.
    *   **Comportamiento Esperado:** El sistema debe registrar un warning (indicando un posible desajuste entre los pagos de MP y los turnos gestionados por AgendaPro, o un pago para un turno que ya fue borrado o no existe), responder `HTTP 200 OK`, y no realizar ninguna acción sobre los turnos.

4.  **Fallo en la Conexión o Autenticación con la API de Mercado Pago:**
    *   **Escenario:** Al intentar consultar los detalles del pago en la API de Mercado Pago, ocurre un error de red, un timeout, o las credenciales de la API de nuestro sistema son inválidas/expiradas.
    *   **Comportamiento Esperado:** El sistema debe implementar una estrategia de reintentos robusta (ej. 3 a 5 reintentos con backoff exponencial). Si todos los reintentos fallan, se debe registrar un error crítico en los logs, notificar al profesional (o al equipo de soporte técnico) vía email, y el estado del `Appointment` asociado permanece inalterado. El webhook inicial ya respondió `200 OK`, por lo que MP no reintentará enviar.

5.  **Fallo en la Actualización de la Base de Datos Local:**
    *   **Escenario:** Después de obtener y validar la información del pago desde MP, la operación de actualización del `Appointment.status` en la base de datos falla (ej. por un problema de concurrencia, error de conexión a la DB, o una validación interna de la BD).
    *   **Comportamiento Esperado:** La operación de base de datos debe ser gestionada dentro de una transacción o con control de reintentos a nivel de la aplicación. Si el fallo persiste, se debe registrar un error crítico, notificar al profesional/soporte, y el estado del turno se considera pendiente de revisión manual para asegurar la consistencia.

6.  **Webhook de Evento No Soportado (o no implementado en esta fase):**
    *   **Escenario:** Se recibe un webhook de Mercado Pago con un `type` diferente a `payment.updated` (ej. `merchant_order.updated`, `refund.updated` si se decide no procesar esto en la fase inicial de esta feature).
    *   **Comportamiento Esperado:** El sistema debe registrar el evento (como información o warning) y responder `HTTP 200 OK`, pero no debe realizar ninguna acción sobre los turnos ya que el tipo de evento no es de interés para esta feature o fase.

7.  **Concurrencia de Webhooks para el Mismo Pago:**
    *   **Escenario:** Múltiples webhooks para el mismo `payment_id` llegan a la aplicación en un corto período de tiempo o en un orden inesperado (ej. `pending` seguido de `approved`, o `approved` dos veces).
    *   **Comportamiento Esperado:** La lógica de procesamiento debe ser idempotente. Solo el primer evento que cambia el `Appointment.status` a un estado final relevante (`BOOKED`, `REJECTED_PAYMENT`) debe realizar la actualización de la DB. Eventos posteriores para el mismo `payment_id` con el mismo estado final simplemente se registran y se descartan las operaciones de actualización. La consulta a la API de Mercado Pago siempre debe obtener el estado *actual y final* del pago, lo que ayuda a resolver conflictos de estado si los webhooks llegan desordenados.

8.  **Turno ya en Estado Final (Completado o Cancelado Localmente) antes del Webhook de Aprobación:**
    *   **Escenario:** Se recibe un webhook de pago (`approved`) para un `Appointment` que ya está marcado como `COMPLETED` (quizás el pago llegó tarde y el turno ya se realizó y se marcó manualmente) o `CANCELLED` (el cliente canceló o el profesional canceló antes de que el pago se aprobara).
    *   **Comportamiento Esperado:**
        *   Si el pago es `approved` para un turno `COMPLETED`: El sistema registra el evento como informativo (pago confirmado para un turno ya finalizado), pero no cambia el `Appointment.status`.
        *   Si el pago es `approved` para un turno `CANCELLED` o `REJECTED_PAYMENT` (por una acción interna del sistema): El sistema registra un error/warning (inconsistencia, ¿se debe reabrir el turno? ¿se debe contactar al cliente para un reembolso?). Para esta fase, no se realiza un cambio de estado automático en estos casos. Se requiere una revisión manual si esta situación es frecuente o una política de negocio clara para la resolución.

---

### Modificaciones Requeridas en el Esquema de Base de Datos (Prisma DSL)

Para soportar esta feature, se requieren las siguientes adiciones y modificaciones al esquema `schema.prisma`:

```prisma
// schema.prisma
// ... (código existente del schema) ...

// Enum para el estado de los turnos (se añaden nuevos estados)
enum AppointmentStatus {
  BOOKED            // Turno reservado y activo (implica pago confirmado o no requerido)
  CANCELLED         // Turno cancelado por el cliente o el profesional
  COMPLETED         // Turno que ha finalizado
  PENDING_PAYMENT   // Nuevo: Indica que el turno está a la espera de un pago externo (ej. Mercado Pago)
  REJECTED_PAYMENT  // Nuevo: Indica que el pago externo asociado fue rechazado o falló
}

// Entidad: Appointment (Turno/Cita)
model Appointment {
  id          String          @id @default(uuid())
  startTime   DateTime
  endTime     DateTime
  clientName  String
  clientEmail String
  clientPhone String?
  status      AppointmentStatus @default(BOOKED) // El valor por defecto podría cambiar a PENDING_PAYMENT si la mayoría de los turnos requieren pago
  notes       String?
  
  // NUEVO CAMPO: Identificador del pago de Mercado Pago asociado a este turno.
  // Puede ser nulo si el turno no requiere pago o si el pago se gestiona fuera de MP.
  // @unique asegura que un payment_id de MP solo se vincule a un único turno en nuestro sistema.
  mpPaymentId String?         @unique(map: "Appointment_mpPaymentId_key") 

  serviceId   String
  service     Service         @relation(fields: [serviceId], references: [id], onDelete: Restrict)
  
  userId      String
  user        User            @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  createdAt   DateTime        @default(now())
  updatedAt   DateTime        @updatedAt

  // ... (índices existentes) ...
}

```