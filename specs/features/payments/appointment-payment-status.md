### Feature: Gestión de Estado de Turno por Pago

**Categoría/Carpeta:** `payments`

---

### 1. Historia de Usuario

Como **Profesional**,
Quiero que el estado de mis turnos se actualice automáticamente en base al resultado del pago recibido de Mercado Pago,
Para **asegurarme de que solo los turnos pagados sean confirmados y liberar slots rápidamente en caso de pagos fallidos**, optimizando mi agenda y reduciendo la gestión manual.

---

### 2. Criterios de Aceptación Detallados

Esta sección describe el comportamiento esperado del sistema para la gestión del estado de los turnos por pago.

#### 2.1. Configuración de Servicios para Pago Anticipado

*   **Dado** que soy un Profesional y tengo acceso a la configuración de mis servicios,
*   **Cuando** creo o edito un servicio,
*   **Entonces** debo poder:
    *   Definir un `priceAmount` (monto) y `priceCurrency` (moneda) para el servicio.
    *   Activar una opción `requiresPayment` para indicar si este servicio necesita pago anticipado.
    *   Por defecto, `requiresPayment` debe ser `false`.

#### 2.2. Reserva de Turno con Pago Obligatorio

*   **Dado** que el profesional ha configurado un servicio para requerir `requiresPayment = true` y ha establecido un monto,
*   **Cuando** un cliente intenta reservar un turno para dicho servicio y completa el formulario de reserva con sus datos,
*   **Entonces** el sistema debe:
    *   Crear un registro de `Appointment` con el `status` `PENDING` y el `paymentStatus` `PENDING_PAYMENT`.
    *   Almacenar los datos del cliente, servicio y horario en el registro del turno.
    *   Generar una solicitud de pago a Mercado Pago utilizando el `priceAmount` y `priceCurrency` del servicio.
    *   Redirigir al cliente a la `paymentUrl` proporcionada por Mercado Pago para completar el pago.
    *   Almacenar el `paymentId` (ID de transacción de Mercado Pago) y el `paymentProvider` ("MERCADO_PAGO") en el registro del turno.
    *   El slot de tiempo para ese turno debe ser considerado como "reservado y pendiente de pago" y no disponible para otros clientes.

#### 2.3. Confirmación de Pago Exitoso (Webhook de Mercado Pago)

*   **Dado** que existe un `Appointment` con `status` `PENDING` y `paymentStatus` `PENDING_PAYMENT`, y un `paymentId` asociado,
*   **Cuando** Mercado Pago notifica al sistema (vía webhook autenticado) que un pago asociado a ese `paymentId` ha sido `aprobado` (`approved`),
*   **Entonces** el sistema debe:
    *   Validar la autenticidad del webhook.
    *   Actualizar el `paymentStatus` del `Appointment` a `CONFIRMED_PAYMENT`.
    *   Actualizar el `status` del `Appointment` a `BOOKED`.
    *   Enviar un email de confirmación de turno pagado al `clientEmail` del cliente, incluyendo todos los detalles del turno y el enlace de autogestión.
    *   Enviar una notificación (email) al `User.email` del profesional sobre el turno confirmado.

#### 2.4. Manejo de Pago Fallido/Rechazado (Webhook de Mercado Pago)

*   **Dado** que existe un `Appointment` con `status` `PENDING` y `paymentStatus` `PENDING_PAYMENT`, y un `paymentId` asociado,
*   **Cuando** Mercado Pago notifica al sistema (vía webhook autenticado) que un pago asociado a ese `paymentId` ha sido `rechazado` (`rejected`), `cancelado` (`cancelled`), `expirado` (`expired`), o ha ocurrido un `fallo` (`failed`),
*   **Entonces** el sistema debe:
    *   Validar la autenticidad del webhook.
    *   Actualizar el `paymentStatus` del `Appointment` a `PAYMENT_FAILED`.
    *   Actualizar el `status` del `Appointment` a `CANCELLED`.
    *   Liberar el slot de tiempo para que pueda ser reservado por otro cliente.
    *   Enviar un email al `clientEmail` del cliente informando sobre el fallo del pago, la cancelación del turno y ofreciendo la opción de intentar reservar de nuevo.
    *   Enviar una notificación (email) al `User.email` del profesional sobre el pago fallido y la cancelación del turno.

#### 2.5. Manejo de Pagos Pendientes (Timeout/Expiración por Sistema)

*   **Dado** que existe un `Appointment` con `status` `PENDING` y `paymentStatus` `PENDING_PAYMENT`,
*   **Cuando** ha transcurrido un tiempo configurable (ej. 30 minutos desde la creación del `paymentUrl`) y no se ha recibido una notificación de pago final de Mercado Pago,
*   **Entonces** el sistema debe:
    *   Realizar una consulta directa a la API de Mercado Pago usando el `paymentId` para obtener el estado actual del pago.
    *   Si el pago sigue en estado `pending`, `in_process`, `expirado` o `cancelado` en Mercado Pago,
        *   Actualizar el `paymentStatus` del `Appointment` a `PAYMENT_FAILED`.
        *   Actualizar el `status` del `Appointment` a `CANCELLED`.
        *   Liberar el slot de tiempo para que pueda ser reservado.
        *   Enviar un email al cliente informando sobre la expiración del intento de pago y la cancelación del turno.
        *   Enviar una notificación (email) al profesional.

#### 2.6. Consulta Manual de Estado de Pago por el Profesional

*   **Dado** que el Profesional está visualizando un `Appointment` con `paymentStatus` `PENDING_PAYMENT` o `PAYMENT_FAILED` en su panel de turnos,
*   **Cuando** el Profesional selecciona la opción "Consultar Estado de Pago" para ese turno,
*   **Entonces** el sistema debe:
    *   Realizar una consulta en tiempo real a la API de Mercado Pago usando el `paymentId` asociado.
    *   Actualizar el `paymentStatus` y el `status` del `Appointment` en la base de datos según la respuesta de Mercado Pago, siguiendo la lógica de los puntos 2.3 y 2.4.
    *   Mostrar el estado de pago actualizado al Profesional en la interfaz.
    *   Activar las notificaciones por email correspondientes si el estado de pago cambia de manera significativa (ej. de `PENDING_PAYMENT` a `CONFIRMED_PAYMENT`).

---

### 3. Casos de Error y Casos Borde (Edge Cases)

#### 3.1. Errores de Comunicación con Mercado Pago

*   **Escenario:** El sistema no puede comunicarse con la API de Mercado Pago (ej. errores de red, timeouts, credenciales inválidas, respuesta inesperada del API) al intentar crear un pago o consultar su estado.
*   **Comportamiento esperado:**
    *   **Al crear el pago (reserva):** La reserva del turno debe fallar completamente. Se debe informar al cliente y al profesional que hubo un problema técnico y que la reserva no pudo ser completada. No se debe crear el registro de `Appointment` en la base de datos o, si se crea temporalmente, debe ser marcado con un `status` `ERROR` y `paymentStatus` `PAYMENT_FAILED` y eliminado automáticamente después de un corto tiempo. Se debe registrar el error para revisión y alerta al administrador del sistema.
    *   **Al recibir webhook o consulta manual:** Registrar el evento de error de comunicación. Para webhooks, se puede reintentar procesar si la plataforma de webhook lo permite. Para consultas manuales, mostrar un mensaje de error al profesional indicando que no se pudo obtener el estado actual de Mercado Pago. El estado del turno en la base de datos no debe cambiar y la operación debe poder ser reintentada.

#### 3.2. Webhook de Mercado Pago Duplicado o Fuera de Orden

*   **Escenario:** Mercado Pago envía la misma notificación de webhook múltiples veces o el orden de los webhooks no es estrictamente secuencial (ej. llega el webhook de `aprobado` antes que el de `pendiente`).
*   **Comportamiento esperado:**
    *   El sistema debe ser **idempotente**: Procesar cada webhook de forma que las actualizaciones de estado solo ocurran si el nuevo estado es una progresión lógica y válida. Por ejemplo, un webhook `pendiente` no debe sobrescribir un estado `CONFIRMED_PAYMENT`.
    *   Ignorar webhooks duplicados para el mismo `paymentId` que no implican un cambio de estado válido.
    *   Registrar todos los webhooks recibidos para auditoría, incluyendo aquellos que no generaron un cambio de estado.

#### 3.3. Turno no Encontrado para `paymentId` del Webhook

*   **Escenario:** Un webhook de Mercado Pago llega con un `paymentId` que no corresponde a ningún `Appointment` existente en la base de datos (ej. un pago de prueba, un turno eliminado por el profesional manualmente antes de que el pago se confirmara, un error en el `paymentId` enviado inicialmente a MP).
*   **Comportamiento esperado:**
    *   Registrar el evento como una advertencia o error en los logs del sistema, indicando que el `paymentId` no se encontró.
    *   No realizar ninguna acción sobre los turnos existentes.
    *   Opcionalmente, enviar una alerta al profesional o al administrador del sistema sobre un pago recibido no asociado a un turno para una posible conciliación manual.

#### 3.4. Inconsistencia entre `status` y `paymentStatus`

*   **Escenario:** Debido a un error o un fallo en el sistema, el `status` de un `Appointment` no se alinea lógicamente con su `paymentStatus` (ej. `paymentStatus = CONFIRMED_PAYMENT` pero `status = PENDING` o `CANCELLED`).
*   **Comportamiento esperado:**
    *   Implementar validaciones a nivel de aplicación para prevenir la creación de estos estados inconsistentes.
    *   Considerar un proceso de "reconciliación" o "sanidad" programado que se ejecute periódicamente para verificar la coherencia y corregir automáticamente las anomalías o, al menos, alertar al profesional o administrador.

#### 3.5. Modificación Manual del Turno con Pago Pendiente por el Profesional

*   **Escenario:** El Profesional intenta cancelar o reagendar un turno que tiene `status = PENDING` y `paymentStatus = PENDING_PAYMENT`.
*   **Comportamiento esperado:**
    *   **Si el profesional cancela:** El sistema debe intentar cancelar la solicitud de pago en Mercado Pago (si la API de Mercado Pago lo permite). El `Appointment` debe ser marcado como `status = CANCELLED` y `paymentStatus = PAYMENT_FAILED` (o un estado específico como `PAYMENT_CANCELLED_BY_PROFESSIONAL`). El slot debe ser liberado.
    *   **Si el profesional reagenda:** No se debe permitir el reagendamiento directo de un turno `PENDING_PAYMENT`. El profesional debe ser guiado a cancelar el turno actual (lo que cancelaría el pago pendiente) y luego crear un nuevo turno con un nuevo proceso de pago.

#### 3.6. Seguridad del Webhook y Validación de Datos

*   **Escenario:** Se recibe una notificación de webhook falsa o maliciosa de una fuente que no es Mercado Pago, o con datos manipulados.
*   **Comportamiento esperado:**
    *   El sistema debe implementar los mecanismos de seguridad recomendados por Mercado Pago para validar la autenticidad del webhook (ej. verificación de firmas, tokens, IPs de origen).
    *   Ignorar y registrar como un intento de intrusión cualquier webhook que no pueda ser autenticado o que contenga datos inconsistentes/inválidos después de la validación.

---

### 4. Modificaciones al Esquema de Base de Datos Existente

La implementación de la "Gestión de Estado de Turno por Pago" requiere la adición de nuevos campos y enums a las tablas existentes, así como la modificación de los estados de algunos enums.

#### 4.1. Nuevos Enums

```prisma
// Enum para el estado de los turnos (MODIFICADO)
enum AppointmentStatus {
  PENDING     // Turno creado, esperando pago o confirmación manual. Nuevo estado inicial.
  BOOKED      // Turno reservado y activo (confirmado).
  CANCELLED   // Turno cancelado por el cliente, profesional o sistema.
  COMPLETED   // Turno que ha finalizado.
}

// Enum para el estado del pago (NUEVO)
enum PaymentStatus {
  NOT_REQUIRED      // El servicio no requiere pago anticipado.
  PENDING_PAYMENT   // Pago iniciado, esperando confirmación de Mercado Pago.
  CONFIRMED_PAYMENT // Pago aprobado exitosamente por Mercado Pago.
  PAYMENT_FAILED    // Pago rechazado, cancelado o expirado por Mercado Pago.
  // REFUNDED         // Opcional para futuras versiones: Pago reembolsado.
}
```

#### 4.2. Entidad `Service` (Servicio) - Modificaciones

Se añadirán campos para la configuración de pagos por servicio.

```prisma
model Service {
  // ... campos existentes ...
  durationMinutes Int           // Duración del servicio en minutos (ej. 30, 60, 90)
  
  // NUEVOS CAMPOS:
  priceAmount     Float         @default(0.0) // Monto del servicio.
  priceCurrency   String        @default("ARS") // Moneda del servicio (ej. "ARS", "USD").
  requiresPayment Boolean       @default(false) // Indica si este servicio requiere pago anticipado.
  
  userId          String
  // ... resto de campos y relaciones ...
}
```

#### 4.3. Entidad `Appointment` (Turno) - Modificaciones

Se añadirán campos para rastrear el estado del pago y los detalles de la transacción. El estado inicial por defecto `status` se cambiará a `PENDING`.

```prisma
model Appointment {
  id              String          @id @default(uuid())
  startTime       DateTime        // Fecha y hora de inicio del turno (incluye fecha)
  endTime         DateTime        // Fecha y hora de fin del turno (calculada en la aplicación)
  clientName      String
  clientEmail     String
  clientPhone     String?
  status          AppointmentStatus @default(PENDING) // MODIFICADO: Estado inicial a PENDING
  
  // NUEVOS CAMPOS:
  paymentStatus   PaymentStatus   @default(NOT_REQUIRED) // Estado del pago del turno.
  paymentProvider String?         // Proveedor de pago (ej. "MERCADO_PAGO").
  paymentId       String?         // ID de transacción del proveedor de pago.
  paymentUrl      String?         // URL de redirección al cliente para el pago.
  
  notes           String?
  serviceId       String
  userId          String
  // ... resto de campos y relaciones ...

  // NUEVO ÍNDICE:
  @@index([paymentId], map: "Appointment_paymentId_idx") // Para buscar rápidamente por ID de pago.
}
```

#### 4.4. Reglas de Negocio Críticas - Actualización

La **Regla de Negocio Crítica e Inquebrantable #6: "No Permite Pagos Directos"** se actualiza y flexibiliza para permitir la integración con pasarelas de pago externas:

**6. Integración con Pasarela de Pagos Externa (Mercado Pago):**
    *   La aplicación **no procesará ni almacenará directamente información sensible de pago** (ej. números de tarjeta de crédito, datos bancarios).
    *   Se utilizará un proveedor externo seguro (Mercado Pago) para la gestión de transacciones de pago, redirigiendo a los clientes a la plataforma del proveedor para completar el proceso.
    *   El sistema solo recibirá notificaciones de estado de pago (webhooks) del proveedor externo para actualizar automáticamente el estado de los turnos en la aplicación.

---