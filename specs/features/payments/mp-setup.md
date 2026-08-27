# Feature: Configuración de Integración con Mercado Pago

**Categoría/Carpeta:** `payments`

## 1. Visión General de la Feature

Esta feature introduce la capacidad para que el profesional integre su cuenta de Mercado Pago con AgendaPro Simple. Esta integración permitirá al profesional definir, a nivel de servicio, si se requiere un pago anticipado por parte del cliente al momento de reservar un turno. Esto representa una evolución significativa de la plataforma, añadiendo una nueva capa de funcionalidad monetaria previamente no contemplada, y que impacta directamente en el flujo de reserva y la confirmación de turnos.

El objetivo principal es ofrecer al profesional una herramienta para reducir el ausentismo (no-shows) y asegurar un ingreso por servicios que lo requieran, al mismo tiempo que se mantiene la simplicidad de la interfaz para el cliente, redirigiéndolo a una pasarela de pago externa para la gestión del cobro.

## 2. Impacto en Reglas de Negocio Existentes

La introducción de esta feature modifica directamente la Regla de Negocio Crítica e Inquebrantable #6.

**Regla de Negocio Crítica Modificada:**

*   **Anterior Regla #6:** "No Permite Pagos Directos: La aplicación **no debe integrar** ni procesar ningún tipo de pago por los turnos. La funcionalidad se limita a la gestión de la reserva y la agenda."

*   **Nueva Regla #6 (Propuesta):** "Integración de Pagos Anticipados a Través de Terceros: La aplicación permitirá la integración con pasarelas de pago de terceros (como Mercado Pago) para gestionar **pagos anticipados opcionales** por servicios. La aplicación **no almacenará ni procesará información sensible de tarjetas de crédito o credenciales de pago del cliente**, delegando este proceso de forma segura y completa a la pasarela externa. Los pagos serán gestionados exclusivamente para la confirmación de turnos que el profesional haya marcado explícitamente como de pago anticipado."

**Nueva Regla de Negocio Crítica Adicional:**

*   **Nueva Regla #9: Confirmación de Turno por Pago Exitoso:** Los turnos asociados a servicios que el profesional ha configurado como de "pago anticipado" solo serán considerados `BOOKED` (reservados y confirmados) una vez que la pasarela de pago externa (ej. Mercado Pago) confirme el éxito de la transacción. Si el pago no se completa o falla, el turno provisionalmente reservado pasará a un estado de `CANCELLED` o `FAILED_PAYMENT` (según se defina), y el slot de tiempo se liberará.

## 3. Historias de Usuario

### Historias de Usuario del Profesional (Configuración)

*   **US-P_MP-01: Conectar con Mercado Pago**
    *   Como Profesional, quiero conectar mi cuenta de Mercado Pago con la aplicación, para poder activar la opción de pago anticipado en mis servicios y recibir dinero de mis clientes.
*   **US-P_MP-02: Desconectar Mercado Pago**
    *   Como Profesional, quiero poder desconectar mi cuenta de Mercado Pago de la aplicación, para dejar de ofrecer pagos anticipados y, si es necesario, reconfigurar la conexión.
*   **US-P_MP-03: Definir Pago Anticipado por Servicio**
    *   Como Profesional, quiero poder indicar en la configuración de cada servicio si requiere pago anticipado, para que los clientes sean redirigidos a pagar al momento de reservar ese servicio específico.
*   **US-P_MP-04: Visualizar Estado de Pago de un Turno**
    *   Como Profesional, quiero ver el estado de pago de cada turno (ej. Pagado, Pendiente de Pago, Fallido), para tener claro qué turnos ya están asegurados económicamente.

### Historias de Usuario del Cliente (Flujo de Reserva con Pago)

*   **US-C_MP-01: Identificar Servicio con Pago Anticipado**
    *   Como Cliente, quiero ver claramente en la página de reserva si un servicio requiere pago anticipado, para entender que debo realizar un pago para confirmar mi turno.
*   **US-C_MP-02: Realizar Pago Anticipado**
    *   Como Cliente, cuando reservo un servicio que requiere pago anticipado, quiero ser redirigido a la pasarela de Mercado Pago para completar el pago de forma segura y sencilla.
*   **US-C_MP-03: Recibir Confirmación de Reserva y Pago**
    *   Como Cliente, quiero recibir un email de confirmación de mi turno que también indique que el pago anticipado ha sido exitoso, para tener un comprobante completo de mi reserva.

## 4. Criterios de Aceptación Detallados

### 4.1. Conexión y Desconexión de Mercado Pago (Profesional)

*   **GA-P_MP-01.1: Acceso a Configuración:**
    *   **Dado** que el Profesional accede a la sección de configuración de pagos.
    *   **Cuando** su cuenta de Mercado Pago no está conectada.
    *   **Entonces** ve un botón o enlace claro para "Conectar con Mercado Pago" o "Autorizar Mercado Pago".
*   **GA-P_MP-01.2: Flujo de Autorización Exitoso:**
    *   **Dado** que el Profesional hace clic en "Conectar con Mercado Pago".
    *   **Cuando** es redirigido a la página de autorización de Mercado Pago, autoriza la conexión, y es redirigido de vuelta a la aplicación.
    *   **Entonces** la aplicación guarda de forma segura las credenciales de conexión (ej. `access_token`, `refresh_token`), y el estado de la integración de Mercado Pago se muestra como "Conectada" con un mensaje de éxito.
*   **GA-P_MP-01.3: Flujo de Autorización Fallido/Cancelado:**
    *   **Dado** que el Profesional es redirigido a la página de autorización de Mercado Pago.
    *   **Cuando** cancela la autorización o Mercado Pago devuelve un error.
    *   **Entonces** es redirigido de vuelta a la aplicación, su cuenta de Mercado Pago no está conectada, y se muestra un mensaje de error o cancelación.
*   **GA-P_MP-02.1: Desconexión Exitosa:**
    *   **Dado** que el Profesional tiene su cuenta de Mercado Pago conectada.
    *   **Cuando** hace clic en "Desconectar" y confirma la acción.
    *   **Entonces** las credenciales de Mercado Pago se eliminan del sistema, el estado de la integración se muestra como "Desconectada", y los servicios previamente marcados con "requiere pago anticipado" dejarán de exigir dicho pago hasta que se reconecte la cuenta.

### 4.2. Configuración de Pago Anticipado por Servicio (Profesional)

*   **GA-P_MP-03.1: Opción de Pago Anticipado en Servicio:**
    *   **Dado** que el Profesional está creando o editando un servicio.
    *   **Cuando** su cuenta de Mercado Pago está conectada.
    *   **Entonces** ve una casilla de verificación o un switch claramente etiquetado como "Requiere pago anticipado" o similar.
*   **GA-P_MP-03.2: Activación y Desactivación:**
    *   **Dado** que el Profesional marca/desmarca la opción "Requiere pago anticipado" y guarda los cambios del servicio.
    *   **Cuando** la cuenta de Mercado Pago está conectada.
    *   **Entonces** el servicio se actualiza con la configuración de pago anticipado, y esto afecta a las futuras reservas de ese servicio.
*   **GA-P_MP-03.3: Restricción sin Conexión:**
    *   **Dado** que el Profesional está creando o editando un servicio.
    *   **Cuando** su cuenta de Mercado Pago *no* está conectada.
    *   **Entonces** la opción "Requiere pago anticipado" está deshabilitada (grisada) o no visible, con una indicación de que necesita conectar Mercado Pago primero.

### 4.3. Flujo de Reserva con Pago Anticipado (Cliente)

*   **GA-C_MP-01.1: Información de Pago en Reserva:**
    *   **Dado** que un Cliente selecciona un servicio que el Profesional ha configurado como de "pago anticipado".
    *   **Cuando** procede a la confirmación del turno.
    *   **Entonces** la interfaz de reserva muestra claramente que el servicio requiere un pago anticipado para su confirmación, indicando el monto si es posible.
*   **GA-C_MP-02.1: Redirección a Mercado Pago:**
    *   **Dado** que un Cliente selecciona un horario para un servicio de pago anticipado y proporciona sus datos.
    *   **Cuando** hace clic en "Confirmar Reserva" (o equivalente).
    *   **Entonces** el sistema crea un intento de turno con `AppointmentStatus` en `PENDING_PAYMENT` y `PaymentStatus` en `PENDING`, y redirige al Cliente a la pasarela de pago de Mercado Pago con los detalles de la compra (monto, descripción del servicio).
*   **GA-C_MP-02.2: Pago Exitoso:**
    *   **Dado** que el Cliente completa el pago exitosamente en la plataforma de Mercado Pago.
    *   **Cuando** Mercado Pago notifica el éxito del pago a la aplicación (vía webhook o redirección con parámetros).
    *   **Entonces** el turno provisional (`PENDING_PAYMENT`) se actualiza a `AppointmentStatus: BOOKED` y `PaymentStatus: PAID`, se registra el ID de la transacción, y se envía un email de confirmación de turno (con detalles de pago) al Cliente y una notificación al Profesional.
*   **GA-C_MP-02.3: Pago Fallido/Cancelado:**
    *   **Dado** que el Cliente intenta realizar el pago en Mercado Pago.
    *   **Cuando** el pago falla, es rechazado, o el Cliente lo cancela, y Mercado Pago notifica este estado a la aplicación.
    *   **Entonces** el turno provisional (`PENDING_PAYMENT`) se actualiza a `AppointmentStatus: CANCELLED` y `PaymentStatus: FAILED` (o `CANCELLED`), el slot de tiempo se libera para nuevas reservas, se notifica al Cliente (opcionalmente) y al Profesional del fallo de pago/cancelación del turno.
*   **GA-C_MP-03.1: Email de Confirmación con Pago:**
    *   **Dado** que un Cliente ha pagado exitosamente un turno anticipado.
    *   **Cuando** recibe el email de confirmación del turno.
    *   **Entonces** el email incluye detalles sobre el pago realizado (monto, estado "Pagado") además de la información del turno.

### 4.4. Visualización de Turnos y Pagos (Profesional)

*   **GA-P_MP-04.1: Vista de Turnos con Estado de Pago:**
    *   **Dado** que el Profesional ve la lista o el calendario de sus turnos.
    *   **Cuando** un turno fue reservado con pago anticipado.
    *   **Entonces** se muestra claramente el `PaymentStatus` del turno (ej. "Pagado", "Pendiente de Pago", "Pago Fallido").
    *   **Entonces** si el `PaymentStatus` es `PAID`, el `AppointmentStatus` es `BOOKED`. Si `PaymentStatus` es `FAILED`, el `AppointmentStatus` es `CANCELLED`. Si `PaymentStatus` es `PENDING`, el `AppointmentStatus` es `PENDING_PAYMENT`.

## 5. Casos de Error y Casos Borde (Edge cases)

*   **Error de Conexión/API de Mercado Pago:**
    *   **Descripción:** Durante el proceso de conexión/autorización o al intentar generar un link de pago, la API de Mercado Pago no responde o devuelve un error.
    *   **Manejo:** La aplicación debe mostrar un mensaje de error claro al usuario (Profesional o Cliente) indicando que la operación no pudo completarse y sugerir reintentar más tarde. En caso de reserva, el slot debe permanecer disponible o liberarse. Para la conexión de MP, la cuenta del Profesional no se marcará como conectada.
*   **Token de Mercado Pago Expirado/Inválido:**
    *   **Descripción:** Las credenciales (`access_token`) almacenadas para Mercado Pago expiran o se invalidan por alguna razón.
    *   **Manejo:** Al detectar un `access_token` inválido (ej. al intentar crear una preferencia de pago), la aplicación debería intentar usar el `refresh_token` para obtener nuevas credenciales. Si esto falla, el Profesional debe ser notificado de que su integración con Mercado Pago está desactualizada y debe volver a conectar su cuenta. Los servicios configurados para pago anticipado no podrán aceptar nuevas reservas con pago hasta que se resuelva.
*   **Cancelación del Pago por el Cliente (Redirección o Navegador):**
    *   **Descripción:** El Cliente es redirigido a Mercado Pago, pero cierra la pestaña, pierde la conexión a internet, o explícitamente cancela el pago antes de completarlo, sin ser redirigido de vuelta a la URL de "fallo" de la aplicación.
    *   **Manejo:** El turno provisional (`PENDING_PAYMENT`) debe tener un mecanismo de caducidad. Si el pago no se confirma en un tiempo configurable (ej. 10-15 minutos), el turno provisional debe ser automáticamente `CANCELLED` y el slot de tiempo liberado. El profesional puede recibir una notificación de "Intento de reserva/pago no completado".
*   **Notificación de Webhook Retrasada/Fallida de Mercado Pago:**
    *   **Descripción:** El Cliente completa el pago en Mercado Pago, pero el webhook de notificación de Mercado Pago a la aplicación se retrasa o falla al ser entregado.
    *   **Manejo:** Además del webhook, la aplicación debería implementar una lógica de "polling" o reintento al redirigir al cliente de vuelta (consultar el estado del pago directamente a MP usando el ID de preferencia/pago). Si el webhook es la única fuente y falla, el turno podría permanecer en `PENDING_PAYMENT` indefinidamente. Un proceso batch podría revisar periódicamente turnos en `PENDING_PAYMENT` que exceden el tiempo de gracia y consultar su estado a MP. Si el estado es `PAID`, actualizar el turno; si es `FAILED`, cancelarlo.
*   **Profesional Desconecta MP con Turnos Pendientes/Pagados:**
    *   **Descripción:** El Profesional decide desconectar su cuenta de Mercado Pago cuando ya tiene turnos `PENDING_PAYMENT` o `PAID` activos.
    *   **Manejo:**
        *   Los turnos `PAID` deben permanecer `BOOKED` y `PAID`. La desconexión no afecta a pagos ya realizados.
        *   Los turnos `PENDING_PAYMENT` deben ser automáticamente `CANCELLED`, ya que no se puede procesar su pago. Se notificará al cliente y profesional.
        *   Los servicios previamente configurados con pago anticipado dejarán de exigir pago.
*   **Cambio de Servicio a No-Pago Anticipado con Turnos Pendientes:**
    *   **Descripción:** Un Profesional cambia la configuración de un servicio de "requiere pago anticipado" a "no requiere pago anticipado", mientras hay turnos en estado `PENDING_PAYMENT` para ese servicio.
    *   **Manejo:** Los turnos `PENDING_PAYMENT` para ese servicio deben ser cancelados automáticamente. El slot se libera. Se notifica al cliente y al profesional. El cliente deberá reservar de nuevo sin pago anticipado.
*   **Profesional No Conecta MP, Intenta Habilitar Pago Anticipado:**
    *   **Descripción:** El Profesional intenta marcar un servicio como "requiere pago anticipado" sin haber conectado su cuenta de Mercado Pago.
    *   **Manejo:** El sistema debe impedir esta acción, mostrando un mensaje informativo que indique la necesidad de conectar la cuenta de Mercado Pago primero.

## 6. Impacto en el Modelo de Datos (Esquema Prisma DSL)

Para soportar la funcionalidad de integración con Mercado Pago y el pago anticipado, se proponen las siguientes modificaciones y adiciones al esquema de base de datos existente:

### Modificaciones en Entidades Existentes

1.  **Enum `AppointmentStatus`:**
    *   **Adición:** `PENDING_PAYMENT` - Indica que el turno ha sido provisionalmente reservado y está a la espera de un pago exitoso para confirmarse.
    ```prisma
    enum AppointmentStatus {
      BOOKED          // Turno reservado y confirmado
      PENDING_PAYMENT // Nuevo: Reservado provisionalmente, esperando pago
      CANCELLED       // Turno cancelado por el cliente, profesional o por fallo de pago
      COMPLETED       // Turno que ha finalizado
    }
    ```

2.  **Entidad `Service`:**
    *   **Adición:** `requiresPrepayment`: `Boolean` `@default(false)`
        *   **Descripción:** Indica si este servicio específico requiere que el cliente realice un pago anticipado para confirmar la reserva.
    ```prisma
    model Service {
      // ... campos existentes ...
      requiresPrepayment Boolean @default(false) // Nuevo: Indica si el servicio requiere pago anticipado
      // ... relaciones existentes ...
    }
    ```

3.  **Entidad `Appointment`:**
    *   **Adición:** `paymentId`: `String?`
        *   **Descripción:** ID de la transacción o preferencia de pago generada en Mercado Pago.
    *   **Adición:** `paymentAmount`: `Decimal?`
        *   **Descripción:** Monto final pagado por el cliente por este turno. Utilizar `Decimal` para precisión monetaria.
    *   **Adición:** `paymentCurrency`: `String?`
        *   **Descripción:** Moneda del pago (ej. "ARS", "USD").
    *   **Adición:** `paymentStatus`: `PaymentStatus` `@default(PENDING)`
        *   **Descripción:** Estado actual del pago asociado a este turno.
    *   **Modificación:** El valor por defecto de `status` debe ser `PENDING_PAYMENT` si el servicio requiere pago, o `BOOKED` si no. Esto se gestionará a nivel de aplicación, no en el default de la DB.
    ```prisma
    // Enum para el estado de los pagos
    enum PaymentStatus {
      PENDING   // Pago iniciado, esperando confirmación
      PAID      // Pago exitosamente completado
      FAILED    // Pago fallido o rechazado
      REFUNDED  // Futuro: Pago reembolsado (puede ser implementado en una fase posterior)
    }

    model Appointment {
      // ... campos existentes ...
      paymentId       String?           // Nuevo: ID de la transacción de Mercado Pago
      paymentAmount   Decimal?          @db.Decimal(10, 2) // Nuevo: Monto pagado, precisión 10 dígitos, 2 decimales
      paymentCurrency String?           // Nuevo: Moneda del pago (ej. "ARS")
      paymentStatus   PaymentStatus     @default(PENDING) // Nuevo: Estado actual del pago
      
      // ... relaciones e índices existentes ...
      @@index([paymentId], map: "Appointment_paymentId_idx") // Nuevo índice para búsquedas por ID de pago
    }
    ```

### Nueva Entidad: `MercadoPagoConfig`

Esta entidad almacenará las credenciales y configuraciones de la integración con Mercado Pago para cada profesional.

```prisma
// Entidad: MercadoPagoConfig (Configuración de la integración con Mercado Pago)
// Almacena las credenciales de Mercado Pago para el profesional.
model MercadoPagoConfig {
  id           String    @id @default(uuid())
  userId       String    @unique // Clave foránea al User. Un usuario solo puede tener una configuración de MP.
  user         User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  accessToken  String    // Token de acceso de Mercado Pago (debe ser encriptado en la capa de aplicación)
  refreshToken String?   // Token para refrescar el accessToken, si es proporcionado por MP
  publicKey    String?   // Clave pública de MP, si es necesaria para el frontend (ej. Checkout Pro/Brick)
  merchantId   String?   // ID de la cuenta de comerciante en Mercado Pago
  
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
}
```

### Resumen del Esquema Prisma DSL Modificado

```prisma
// schema.prisma
// Prisma schema para una aplicación de reserva de turnos mono-usuario con integración de pagos

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql" // Se puede cambiar a "mysql" según la elección final
  url      = env("DATABASE_URL")
}

// Enum para el estado de los turnos (MODIFICADO)
enum AppointmentStatus {
  BOOKED          // Turno reservado y confirmado
  PENDING_PAYMENT // Nuevo: Reservado provisionalmente, esperando pago
  CANCELLED       // Turno cancelado por el cliente, profesional o por fallo de pago
  COMPLETED       // Turno que ha finalizado
}

// Enum para el estado de los pagos (NUEVO)
enum PaymentStatus {
  PENDING   // Pago iniciado, esperando confirmación
  PAID      // Pago exitosamente completado
  FAILED    // Pago fallido o rechazado
  REFUNDED  // Futuro: Pago reembolsado (puede ser implementado en una fase posterior)
}

// Entidad: User (Profesional/Proveedor de servicio)
model User {
  id                String              @id @default(uuid())
  email             String              @unique(map: "User_email_key")
  password          String
  name              String
  contactPhone      String?
  createdAt         DateTime            @default(now())
  updatedAt         DateTime            @updatedAt
  
  // Relaciones
  services          Service[]
  workingHours      WorkingHours[]
  appointments      Appointment[]
  mercadoPagoConfig MercadoPagoConfig? // Nuevo: Relación 1:1 opcional con la configuración de MP
}

// Entidad: Service (Servicio ofrecido) (MODIFICADO)
model Service {
  id                String        @id @default(uuid())
  name              String
  description       String?
  durationMinutes   Int
  requiresPrepayment Boolean       @default(false) // NUEVO CAMPO
  
  // Clave foránea al User que ofrece este servicio
  userId            String
  user              User          @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  createdAt         DateTime      @default(now())
  updatedAt         DateTime      @updatedAt
  
  // Relaciones
  appointments      Appointment[]

  @@unique([userId, name], map: "Service_userId_name_key")
}

// Entidad: WorkingHours (Horas de trabajo/disponibilidad regular)
model WorkingHours {
  id        String   @id @default(uuid())
  dayOfWeek Int      // 0 = Domingo, 1 = Lunes, ..., 6 = Sábado
  startTime String   // Hora de inicio en formato "HH:MM" (ej. "09:00")
  endTime   String   // Hora de fin en formato "HH:MM" (ej. "17:00")
  
  // Clave foránea al User al que pertenecen estas horas
  userId    String
  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  @@unique([userId, dayOfWeek], map: "WorkingHours_userId_dayOfWeek_key")
}

// Entidad: Appointment (Turno/Cita) (MODIFICADO)
model Appointment {
  id              String            @id @default(uuid())
  startTime       DateTime
  endTime         DateTime
  clientName      String
  clientEmail     String
  clientPhone     String?
  status          AppointmentStatus @default(BOOKED) // El default se gestionará en aplicación
  notes           String?
  
  paymentId       String?           // NUEVO CAMPO: ID de la transacción de Mercado Pago
  paymentAmount   Decimal?          @db.Decimal(10, 2) // NUEVO CAMPO: Monto pagado
  paymentCurrency String?           // NUEVO CAMPO: Moneda del pago (ej. "ARS")
  paymentStatus   PaymentStatus     @default(PENDING) // NUEVO CAMPO: Estado actual del pago
  
  // Clave foránea al Service asociado a este turno
  serviceId       String
  service         Service           @relation(fields: [serviceId], references: [id], onDelete: Restrict)
  
  // Clave foránea al User (profesional) al que pertenece este turno
  userId          String
  user            User              @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  createdAt       DateTime          @default(now())
  updatedAt       DateTime          @updatedAt

  // Índices para optimizar la búsqueda de turnos
  @@index([userId, startTime], map: "Appointment_userId_startTime_idx")
  @@index([clientEmail], map: "Appointment_clientEmail_idx")
  @@index([paymentId], map: "Appointment_paymentId_idx") // NUEVO ÍNDICE
}

// Entidad: MercadoPagoConfig (NUEVA ENTIDAD)
model MercadoPagoConfig {
  id           String   @id @default(uuid())
  userId       String   @unique // Asegura que solo hay una configuración de MP por usuario
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade) // Si el user se elimina, su config de MP también
  
  accessToken  String   // Token de acceso de Mercado Pago (encriptar en aplicación)
  refreshToken String?  // Token para refrescar el accessToken
  publicKey    String?  // Clave pública, si es necesaria para frontend
  merchantId   String?  // ID de la cuenta de comerciante en Mercado Pago
  
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
}
```

## 7. Índices, Restricciones y Consideraciones de Rendimiento Adicionales

### Índices Adicionales

*   **`Appointment.paymentId`**: Un nuevo índice en `paymentId` permitirá búsquedas rápidas de turnos específicos asociados a una transacción de Mercado Pago, crucial para procesar webhooks o verificar estados de pago.
*   **`MercadoPagoConfig.userId`**: La restricción `@unique` en esta clave foránea generará un índice único automáticamente, garantizando que cada profesional tenga una única configuración de Mercado Pago y optimizando la búsqueda de su configuración.

### Restricciones Adicionales

*   **`MercadoPagoConfig.userId` `@unique`**: Asegura la unicidad de la configuración de Mercado Pago por profesional.
*   **`MercadoPagoConfig` `onDelete: Cascade`**: Si el `User` (profesional) es eliminado, su `MercadoPagoConfig` asociada también se eliminará automáticamente, manteniendo la consistencia de los datos.
*   **`Appointment.paymentAmount` `@db.Decimal(10, 2)`**: Define la precisión del campo `paymentAmount` para almacenar valores monetarios correctamente, con hasta 10 dígitos en total y 2 decimales.

### Consideraciones de Rendimiento y Seguridad

*   **Manejo de Credenciales de Mercado Pago**: El `accessToken` y `refreshToken` almacenados en `MercadoPagoConfig` son sensibles. Es **crítico** que estos valores sean almacenados de forma encriptada en la base de datos (ej. utilizando AES-256 o similar) y desencriptados solo cuando sean necesarios en la capa de la aplicación.
*   **Webhooks**: La implementación de webhooks de Mercado Pago será esencial para recibir notificaciones en tiempo real sobre el estado de los pagos. La aplicación debe ser capaz de recibir y procesar estas notificaciones de forma asíncrona y segura (validando firmas y origen).
*   **Idempotencia**: Las operaciones de confirmación de pago deben ser idempotentes. Esto significa que si un webhook o una redirección con estado de éxito se recibe múltiples veces para el mismo `paymentId`, la aplicación debe procesar el cambio de estado del turno solo una vez para evitar inconsistencias.
*   **Transacciones y Consistencia**: La actualización del `AppointmentStatus` y `PaymentStatus` debe realizarse dentro de una transacción de base de datos para asegurar que ambos cambios se confirmen o se reviertan juntos, manteniendo la consistencia de los datos en caso de errores intermedios.
*   **Caducidad de `PENDING_PAYMENT`**: La lógica de la aplicación debe incluir un mecanismo (ej. un cron job) que revise periódicamente los turnos con `AppointmentStatus: PENDING_PAYMENT` cuya `createdAt` exceda un tiempo límite predefinido. Estos turnos deben ser cancelados automáticamente y sus slots liberados, en caso de que el cliente no haya completado el pago o la notificación de pago no haya llegado.