# Especificación Técnica - Feature: Checkout de Mercado Pago para Clientes

## 1. Visión General de la Feature

Esta feature introduce la capacidad de procesar pagos en línea para los turnos reservados a través de la pasarela de pago de Mercado Pago. Su objetivo principal es permitir a los clientes asegurar sus reservas mediante un pago anticipado, mejorando la confirmación de la cita y reduciendo los "no-shows".

**Contexto en AgendaPro Simple:**
Actualmente, la aplicación AgendaPro Simple permite la reserva de turnos sin gestionar pagos directos. Esta feature expande significativamente la funcionalidad del producto al integrar un proceso de checkout, transformando el flujo de reserva en una transacción completa que incluye la confirmación del pago.

**NOTA CRÍTICA sobre la Regla de Negocio Existente:**
Es fundamental destacar que esta feature introduce un cambio sustancial en las "Reglas de Negocio Críticas e Inquebrantables" del proyecto. Específicamente, la **Regla de Negocio #6: "No Permite Pagos Directos"** será **modificada o derogada** por la implementación de esta funcionalidad. La nueva política de negocio implícita es que la aplicación **sí permitirá** la integración y procesamiento de pagos por turnos a través de pasarelas de pago externas. Esta adaptación es crucial para el alcance de esta feature.

## 2. Historia de Usuario

Como **Cliente**,
Quiero **pagar mi turno usando Mercado Pago al momento de la reserva**,
Para **confirmar mi cita de manera inmediata y segura, y asegurar mi espacio con el profesional.**

## 3. Criterios de Aceptación Detallados

### AC1: Selección del Método de Pago

*   **Dado** que el Cliente ha navegado hasta el final del flujo de reserva, ha seleccionado un servicio y un horario disponible, y ha ingresado sus datos de contacto (Nombre, Email, Teléfono),
*   **Cuando** el Cliente procede a la pantalla de confirmación de reserva (antes de la confirmación final),
*   **Entonces** se le presentará una sección clara y visible que ofrece "Pagar con Mercado Pago" como la opción de pago principal para confirmar su reserva.
*   **Y** la información del turno y el monto total a pagar serán claramente visibles junto a la opción de pago.

### AC2: Iniciación del Proceso de Pago

*   **Dado** que el Cliente ha revisado los detalles de su turno y el monto a pagar,
*   **Cuando** el Cliente hace clic en el botón o enlace "Pagar con Mercado Pago",
*   **Entonces** el sistema creará una intención de pago (Ej. un `checkout_link` o `preference_id` de Mercado Pago) vinculada a la reserva del turno.
*   **Y** el Cliente será redirigido de forma segura a la pasarela de pago de Mercado Pago para completar la transacción.
*   **Y** el estado del `Appointment` interno se actualizará a `PENDING_PAYMENT` (Pendiente de Pago) inmediatamente después de iniciar la redirección, marcando el slot como temporalmente no disponible para otros clientes.

### AC3: Gestión de Pago Exitoso

*   **Dado** que el Cliente ha sido redirigido a la pasarela de Mercado Pago,
*   **Cuando** el Cliente completa exitosamente el proceso de pago en Mercado Pago (Ej. tarjeta de crédito aprobada, pago en efectivo realizado y confirmado por MP),
*   **Entonces** Mercado Pago notificará al sistema (vía webhook/IPN) sobre el pago aprobado.
*   **Y** el sistema actualizará el estado del `Appointment` de `PENDING_PAYMENT` a `BOOKED` (lo que implica "Reservado y Pagado").
*   **Y** el sistema redirigirá al Cliente de vuelta a una página de confirmación de reserva y pago dentro de AgendaPro Simple, mostrando un mensaje de éxito.
*   **Y** el Cliente recibirá un email de confirmación de su turno, que ahora incluirá la información de que el pago ha sido exitoso.
*   **Y** el Profesional recibirá una notificación por email sobre la nueva reserva, indicando que ha sido pagada.
*   **Y** los detalles de la transacción de Mercado Pago (ID de pago, monto, estado final, método de pago) serán almacenados y vinculados al `Appointment` en la base de datos.

### AC4: Gestión de Pago Fallido o Rechazado

*   **Dado** que el Cliente ha sido redirigido a la pasarela de Mercado Pago,
*   **Cuando** el pago falla, es rechazado, o no se completa dentro de un tiempo razonable (Ej. se cierra la pestaña del navegador, tarjeta rechazada),
*   **Entonces** Mercado Pago notificará al sistema (vía webhook/IPN o por la redirección de retorno si aplica) sobre el estado de fallo o rechazo.
*   **Y** el sistema actualizará el estado del `Appointment` de `PENDING_PAYMENT` a `PAYMENT_FAILED` (Pago Fallido).
*   **Y** el Cliente será redirigido de vuelta a una página de estado de pago fallido dentro de AgendaPro Simple, mostrando un mensaje claro sobre el error y, si es posible, opciones para reintentar el pago o contactar al profesional.
*   **Y** el `slot` de disponibilidad asociado al turno `PAYMENT_FAILED` se liberará para otras reservas si se determina que no hay un reintento inminente (esta lógica deberá ser definida).
*   **Y** el Profesional recibirá una notificación por email sobre el intento fallido de reserva/pago para el turno.

### AC5: Visualización del Estado de Pago por el Profesional

*   **Dado** que el Profesional accede a su panel de turnos (vista de calendario o listado),
*   **Cuando** visualiza un turno que ha pasado por el proceso de pago,
*   **Entonces** la interfaz del Profesional mostrará claramente el estado del pago asociado a ese turno (Ej. "Pagado", "Pendiente de Pago", "Pago Fallido").

### AC6: Reconciliación de Pagos (Reintentos)

*   **Dado** que un Cliente ha experimentado un "Pago Fallido" o ha dejado un pago en estado `PENDING_PAYMENT`,
*   **Cuando** el Cliente decide reintentar el pago (Ej. desde la página de pago fallido o un enlace en email),
*   **Entonces** el sistema le permitirá iniciar un nuevo intento de pago para el mismo turno, respetando el estado actual de disponibilidad del slot.
*   **Y** se generará una nueva `PaymentTransaction` vinculada al mismo `Appointment`.

## 4. Casos de Error y Casos Borde (Edge cases)

### Errores de Conexión y Red
*   **Redirección interrumpida:** El Cliente pierde la conexión a internet justo después de ser redirigido a Mercado Pago, pero antes de que cargue la pasarela. El `Appointment` queda en `PENDING_PAYMENT` pero el cliente no ve la pasarela.
*   **Fallo de Webhook/IPN:** Mercado Pago aprueba un pago, pero la notificación (webhook/IPN) al sistema falla o se retrasa. El `Appointment` queda en `PENDING_PAYMENT` mientras el cliente ya pagó. Se requerirá un mecanismo de reintento/reconciliación.
*   **Redirección de retorno fallida:** El pago es exitoso, Mercado Pago intenta redirigir al cliente de vuelta, pero falla (ej. cliente cierra la pestaña, error de red). El `Appointment` se actualiza correctamente, pero el cliente no recibe confirmación visual inmediata.

### Estados de Pago Ambiguos o Inconsistentes
*   **Cierre de ventana durante pago:** El Cliente cierra la pestaña del navegador o la aplicación de Mercado Pago en medio del proceso, sin un resultado claro de éxito o fracaso. El `Appointment` queda en `PENDING_PAYMENT` hasta que Mercado Pago envíe una notificación final o expire el `checkout_link`.
*   **Pagos en efectivo/externos (Ej. Rapipago, Pagofácil):** El cliente selecciona un método de pago en efectivo. El `Appointment` entra en `PENDING_PAYMENT`. El pago puede tardar horas o días en confirmarse, o nunca realizarse. La duración de `PENDING_PAYMENT` debe ser configurable y la disponibilidad del slot debe gestionarse (ej. bloquear por X horas/días o liberar si no se paga).
*   **Reversión/Contracargo:** Un pago inicialmente aprobado es revertido o un contracargo es solicitado posteriormente. Esta es una gestión post-pago que puede afectar el `Appointment` (ej. si el turno ya fue completado).

### Concurrencia y Disponibilidad
*   **Doble reserva con pago:** Dos Clientes intentan reservar y pagar el mismo slot de tiempo casi simultáneamente. La lógica debe asegurar que solo uno de ellos logre confirmar el `Appointment` (`BOOKED`), y el otro reciba un "slot ya no disponible" o "pago fallido por disponibilidad" antes o durante el proceso de pago. El `Appointment` debe marcarse como `PENDING_PAYMENT` y bloquear el slot antes de redirigir a MP.
*   **Disponibilidad se agota durante el pago:** Un Cliente inicia el pago, pero mientras está en Mercado Pago, el profesional marca el slot como no disponible o se libera por otra razón. La confirmación del pago en el sistema debe revalidar la disponibilidad antes de marcar el `Appointment` como `BOOKED`.

### Cambios en los Datos del Turno/Servicio
*   **Cambio de precio después de iniciar pago:** El precio de un `Service` es modificado por el Profesional *después* de que un Cliente inicia el pago para ese servicio, pero *antes* de que lo complete. El monto enviado a Mercado Pago debe ser el precio al momento de iniciar la transacción.
*   **Servicio eliminado durante pago:** El Profesional elimina un `Service` mientras un Cliente está en proceso de pago para un turno de ese `Service`. El sistema debe manejar la confirmación del pago para un `Service` que ya no existe (ej. marcar como `CANCELLED` y reembolsar, o no permitir la eliminación si hay `PENDING_PAYMENT`).

### Otros Casos Borde
*   **Múltiples transacciones para un solo turno:** Un cliente inicia múltiples procesos de pago para el mismo `Appointment` (ej. cierra una ventana y abre otra). El sistema debe ser capaz de gestionar esto, posiblemente invalidando intentos de pago anteriores o asegurando que solo el pago exitoso más reciente sea el que actualice el `Appointment` a `BOOKED`.
*   **Cancelación de turno pagado:** Un Cliente o Profesional cancela un turno que ya ha sido pagado. Se requerirá un flujo de reembolso (manual o automático vía API de MP), lo cual está fuera del alcance directo de esta feature pero es una consideración futura crítica.

## 5. Impacto en el Modelo de Datos (Consideraciones Técnicas)

La integración de pagos requiere la adición de nuevas entidades y la modificación de las existentes.

### Modificaciones en `Service`
*   **`price`**: `Decimal` - Campo para almacenar el precio del servicio. Será utilizado para determinar el monto a cobrar en Mercado Pago.
*   **`currency`**: `String` - Campo para especificar la moneda del servicio (ej. "ARS", "USD").

### Modificaciones en `Appointment`
*   **`status`**: El `enum AppointmentStatus` debe expandirse para incluir nuevos estados relacionados con el pago:
    *   `PENDING_PAYMENT`: El turno ha sido creado y está a la espera de un pago exitoso.
    *   `PAYMENT_FAILED`: Se ha intentado un pago, pero ha fallado.
    *   `BOOKED` (Reinterpretado): Ahora significará "Confirmado y Pagado".
*   **`paymentTransactionId`**: `String?` (Opcional, FK) - Para vincular el `Appointment` directamente con la `PaymentTransaction` principal y más reciente.

### Nueva Entidad: `PaymentTransaction`
Esta entidad almacenará todos los intentos de pago y sus detalles, permitiendo un historial de transacciones y una reconciliación precisa.

*   `id`: `String` (UUID) - Identificador único de la transacción de pago.
*   `appointmentId`: `String` (FK a `Appointment`) - Clave foránea al turno al que corresponde este pago.
*   `mpPaymentId`: `String` - ID de la transacción proporcionado por Mercado Pago (puede ser `preference_id` o `payment_id`).
*   `amount`: `Decimal` - Monto exacto de la transacción.
*   `currency`: `String` - Moneda de la transacción.
*   `status`: `PaymentTransactionStatus` (Enum) - Estado interno de la transacción (ej. `INITIATED`, `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`).
*   `externalStatusDetail`: `String?` - Descripción más detallada del estado según Mercado Pago (ej. `accredited`, `cc_rejected_bad_filled_security_code`).
*   `paymentMethodType`: `String?` - Tipo de medio de pago utilizado (ej. "credit_card", "bank_transfer", "ticket").
*   `installments`: `Int?` - Número de cuotas si aplica.
*   `createdAt`: `DateTime` - Fecha y hora de creación del registro de la transacción.
*   `updatedAt`: `DateTime` - Última fecha y hora de actualización del registro.

### Nuevo Enum: `PaymentTransactionStatus`
Define los posibles estados por los que puede pasar una `PaymentTransaction` a lo largo de su ciclo de vida.
*   `INITIATED` (Iniciado): La transacción ha sido creada en el sistema, pero el cliente aún no ha interactuado con la pasarela.
*   `PENDING` (Pendiente): El cliente ha sido redirigido a la pasarela, o está a la espera de confirmación (ej. pago en efectivo).
*   `APPROVED` (Aprobado): El pago ha sido completado y confirmado por Mercado Pago.
*   `REJECTED` (Rechazado): El pago ha sido rechazado por Mercado Pago (ej. tarjeta inválida).
*   `CANCELLED` (Cancelado): La transacción ha sido cancelada antes de su aprobación (ej. por expiración, o por el cliente).
*   `REFUNDED` (Reembolsado): La transacción fue aprobada y posteriormente se realizó un reembolso (consideración futura).