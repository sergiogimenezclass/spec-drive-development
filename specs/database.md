# Diseño de Base de Datos para Aplicación de Turnos (Mono-Usuario)

Este documento detalla el diseño conceptual y físico de la base de datos para una aplicación de gestión de turnos para un único profesional. La aplicación permitirá al profesional gestionar sus servicios, definir su disponibilidad y a los clientes reservar, cancelar o reagendar turnos.

## 1. Diseño Conceptual del Modelo de Datos

El modelo de datos se centra en la interacción entre un único profesional (usuario de la aplicación) y sus clientes externos, quienes reservan turnos.

*   **Usuario (User):** Representa al único profesional que utiliza la aplicación. Es el actor principal que gestiona la disponibilidad, configura los servicios y visualiza los turnos. Incluye la información de autenticación.
*   **Servicio (Service):** Define los tipos de citas o turnos que el profesional ofrece (ej. "Corte de pelo", "Sesión de terapia de 1h", "Clase de yoga"). Cada servicio tiene una duración específica y es ofrecido por el `User`.
*   **Horas de Trabajo (WorkingHours):** Establece los bloques de tiempo regulares en los que el profesional está disponible para recibir reservas durante la semana (ej. Lunes de 9:00 a 17:00).
*   **Turno (Appointment):** Representa una reserva concreta realizada por un cliente para un servicio y una franja horaria específicos. Incluye los datos de contacto del cliente y el estado del turno.

**Relaciones Clave:**

*   Un `Usuario` **ofrece** muchos `Servicios`.
*   Un `Usuario` **define** sus `Horas de Trabajo`.
*   Un `Servicio` **puede tener** muchos `Turnos` reservados.
*   Un `Turno` **está asociado a** un `Servicio` y, por extensión, al `Usuario` que lo ofrece.

## 2. Listado de Entidades principales

### Entidad: `User` (Usuario)

Representa al profesional o proveedor del servicio. Es la entidad central de autenticación y gestión. En la práctica, solo existirá un registro de este tipo.

*   `id`: `String` (UUID) - Identificador único del usuario.
*   `email`: `String` (Único) - Correo electrónico del profesional, utilizado para el inicio de sesión.
*   `password`: `String` - Contraseña hasheada del profesional.
*   `name`: `String` - Nombre completo del profesional o de la empresa/marca.
*   `contactPhone`: `String?` (Opcional) - Número de teléfono de contacto del profesional.
*   `createdAt`: `DateTime` - Fecha y hora de creación del registro.
*   `updatedAt`: `DateTime` - Última fecha y hora de actualización del registro.
*   **Relaciones:**
    *   `services`: Lista de `Service` (Relación 1:N con `Service`).
    *   `workingHours`: Lista de `WorkingHours` (Relación 1:N con `WorkingHours`).
    *   `appointments`: Lista de `Appointment` (Relación 1:N con `Appointment`).

### Entidad: `Service` (Servicio)

Define los tipos de servicios que el profesional ofrece, incluyendo su duración.

*   `id`: `String` (UUID) - Identificador único del servicio.
*   `name`: `String` - Nombre descriptivo del servicio (ej. "Corte de Pelo Básico", "Terapia Individual").
*   `description`: `String?` (Opcional) - Descripción detallada del servicio para los clientes.
*   `durationMinutes`: `Int` - Duración estándar del servicio en minutos (ej. 30, 60, 90).
*   `userId`: `String` - Clave foránea que vincula el servicio al `User` que lo ofrece.
*   `createdAt`: `DateTime` - Fecha y hora de creación.
*   `updatedAt`: `DateTime` - Última fecha y hora de actualización.
*   **Restricciones:** Un `userId` y `name` deben ser únicos.
*   **Relaciones:**
    *   `user`: `User` (Relación N:1 con `User`).
    *   `appointments`: Lista de `Appointment` (Relación 1:N con `Appointment`).

### Entidad: `WorkingHours` (Horas de Trabajo)

Define los bloques de tiempo regulares en los que el profesional está disponible cada día de la semana.

*   `id`: `String` (UUID) - Identificador único del registro de horario.
*   `dayOfWeek`: `Int` - Día de la semana (0 = Domingo, 1 = Lunes, ..., 6 = Sábado).
*   `startTime`: `String` - Hora de inicio del período de trabajo en formato "HH:MM" (ej. "09:00").
*   `endTime`: `String` - Hora de fin del período de trabajo en formato "HH:MM" (ej. "17:00").
*   `userId`: `String` - Clave foránea que vincula este horario al `User` correspondiente.
*   `createdAt`: `DateTime` - Fecha y hora de creación.
*   `updatedAt`: `DateTime` - Última fecha y hora de actualización.
*   **Restricciones:** La combinación `(userId, dayOfWeek)` debe ser única, asegurando que un profesional solo tenga un horario definido por día.
*   **Relaciones:**
    *   `user`: `User` (Relación N:1 con `User`).

### Entidad: `Appointment` (Turno)

Representa una reserva específica realizada por un cliente para un servicio en una fecha y hora determinadas.

*   `id`: `String` (UUID) - Identificador único del turno.
*   `startTime`: `DateTime` - Fecha y hora exacta de inicio del turno.
*   `endTime`: `DateTime` - Fecha y hora exacta de fin del turno (calculada a partir de `startTime` y `Service.durationMinutes`).
*   `clientName`: `String` - Nombre completo del cliente que realiza la reserva.
*   `clientEmail`: `String` - Correo electrónico del cliente (para confirmaciones y notificaciones).
*   `clientPhone`: `String?` (Opcional) - Número de teléfono del cliente.
*   `status`: `AppointmentStatus` (Enum) - Estado actual del turno (ej. `BOOKED`, `CANCELLED`, `COMPLETED`).
*   `notes`: `String?` (Opcional) - Notas adicionales o requerimientos especiales para el turno.
*   `serviceId`: `String` - Clave foránea al `Service` asociado con este turno.
*   `userId`: `String` - Clave foránea al `User` (profesional) al que pertenece este turno, para facilitar consultas directas.
*   `createdAt`: `DateTime` - Fecha y hora de creación.
*   `updatedAt`: `DateTime` - Última fecha y hora de actualización.
*   **Relaciones:**
    *   `service`: `Service` (Relación N:1 con `Service`).
    *   `user`: `User` (Relación N:1 con `User`).

### Enum: `AppointmentStatus`

Define los posibles estados por los que puede pasar un `Appointment`.

*   `BOOKED` (Reservado)
*   `CANCELLED` (Cancelado por el cliente o el profesional)
*   `COMPLETED` (El turno se ha realizado)

## 3. Esquema físico completo escrito en sintaxis Prisma DSL

```prisma
// schema.prisma
// Prisma schema para una aplicación de reserva de turnos mono-usuario

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql" // Se puede cambiar a "mysql" según la elección final
  url      = env("DATABASE_URL")
}

// Enum para el estado de los turnos
enum AppointmentStatus {
  BOOKED      // Turno reservado y activo
  CANCELLED   // Turno cancelado por el cliente o el profesional
  COMPLETED   // Turno que ha finalizado
}

// Entidad: User (Profesional/Proveedor de servicio)
// Representa al único usuario profesional que gestiona la aplicación.
model User {
  id           String        @id @default(uuid())
  email        String        @unique(map: "User_email_key")
  password     String        // La contraseña debe almacenarse hasheada (ej. con bcrypt)
  name         String
  contactPhone String?
  createdAt    DateTime      @default(now())
  updatedAt    DateTime      @updatedAt
  
  // Relaciones
  services     Service[]
  workingHours WorkingHours[]
  appointments Appointment[]
}

// Entidad: Service (Servicio ofrecido)
// Define los tipos de servicios que el profesional ofrece.
model Service {
  id              String        @id @default(uuid())
  name            String
  description     String?
  durationMinutes Int           // Duración del servicio en minutos (ej. 30, 60, 90)
  
  // Clave foránea al User que ofrece este servicio
  userId          String
  user            User          @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  createdAt       DateTime      @default(now())
  updatedAt       DateTime      @updatedAt
  
  // Relaciones
  appointments    Appointment[]

  @@unique([userId, name], map: "Service_userId_name_key") // Un usuario no puede tener dos servicios con el mismo nombre
}

// Entidad: WorkingHours (Horas de trabajo/disponibilidad regular)
// Define la disponibilidad horaria del profesional por día de la semana.
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

  @@unique([userId, dayOfWeek], map: "WorkingHours_userId_dayOfWeek_key") // Un usuario solo puede tener un registro de horas de trabajo por día
}

// Entidad: Appointment (Turno/Cita)
// Representa una reserva específica realizada por un cliente.
model Appointment {
  id          String          @id @default(uuid())
  startTime   DateTime        // Fecha y hora de inicio del turno (incluye fecha)
  endTime     DateTime        // Fecha y hora de fin del turno (calculada en la aplicación)
  clientName  String
  clientEmail String
  clientPhone String?
  status      AppointmentStatus @default(BOOKED)
  notes       String?
  
  // Clave foránea al Service asociado a este turno
  serviceId   String
  service     Service         @relation(fields: [serviceId], references: [id], onDelete: Restrict) // No permitir borrar un servicio si tiene turnos asociados
  
  // Clave foránea al User (profesional) al que pertenece este turno
  userId      String
  user        User            @relation(fields: [userId], references: [id], onDelete: Cascade) // Si el profesional se elimina, sus turnos también
  
  createdAt   DateTime        @default(now())
  updatedAt   DateTime        @updatedAt

  // Índices para optimizar la búsqueda de turnos
  @@index([userId, startTime], map: "Appointment_userId_startTime_idx") // Para consultar turnos de un profesional por rango de fechas
  @@index([clientEmail], map: "Appointment_clientEmail_idx") // Para buscar turnos de un cliente específico por email
}

```

## 4. Índices, restricciones o consideraciones de rendimiento

### Índices

Los índices son fundamentales para optimizar el rendimiento de las consultas, especialmente en escenarios donde se buscan, filtran o ordenan grandes volúmenes de datos.

*   **`User.email`**: Un índice único se crea automáticamente debido a la restricción `@unique`. Esto es crucial para la autenticación, permitiendo búsquedas rápidas del usuario por su correo electrónico.
*   **`Service`**:
    *   `@@unique([userId, name])`: Este índice compuesto asegura la unicidad de los nombres de servicio para un mismo profesional y optimiza las búsquedas de servicios específicos de un usuario.
*   **`WorkingHours`**:
    *   `@@unique([userId, dayOfWeek])`: Este índice compuesto garantiza que solo haya un conjunto de horas de trabajo definido por día para cada profesional y agiliza las consultas de disponibilidad.
*   **`Appointment`**:
    *   `@@index([userId, startTime])`: Es un índice compuesto vital para la aplicación. Permite consultar eficientemente todos los turnos de un profesional, ordenarlos cronológicamente o filtrar por rangos de fechas, lo cual es esencial para la visualización del calendario.
    *   `@@index([clientEmail])`: Este índice es útil para buscar rápidamente todos los turnos asociados a un cliente específico a través de su correo electrónico, facilitando la gestión de cancelaciones o reagendamientos.

### Restricciones

Las restricciones aseguran la integridad y consistencia de los datos en la base de datos.

*   **Claves Primarias (`@id @default(uuid())`)**: Todas las entidades utilizan UUIDs como identificadores únicos. Esto ofrece una buena escalabilidad y flexibilidad en entornos distribuidos o futuros crecimientos, aunque para una aplicación mono-usuario su principal ventaja es la unicidad garantizada.
*   **Claves Foráneas (`@relation`)**: Establecen las relaciones entre tablas, manteniendo la integridad referencial.
    *   **`onDelete: Cascade`**: Se aplica en las relaciones de `User` con `Service`, `WorkingHours` y `Appointment`. Esto significa que si el profesional (`User`) es eliminado, todos sus servicios, horarios de trabajo y turnos asociados se eliminarán automáticamente. Esta es una decisión de diseño apropiada para una aplicación mono-usuario donde todo el contenido está inherentemente ligado a ese único `User`.
    *   **`onDelete: Restrict`**: Se aplica en la relación de `Appointment` con `Service`. Esto previene la eliminación de un `Service` si aún existen `Appointment`s que hacen referencia a él. Esto protege la información histórica y evita enlaces rotos en los turnos ya reservados.
*   **Unicidad (`@unique`, `@@unique`)**:
    *   `User.email`: Garantiza que cada profesional tenga un correo electrónico único para la autenticación.
    *   `Service` (`userId`, `name`): Impide que un profesional cree dos servicios con el mismo nombre, mejorando la organización.
    *   `WorkingHours` (`userId`, `dayOfWeek`): Asegura que un profesional no defina horarios duplicados para el mismo día de la semana.
*   **Valores Predeterminados (`@default`)**:
    *   `createdAt`: Establece automáticamente la fecha y hora de creación de un registro.
    *   `updatedAt`: Actualiza automáticamente la fecha y hora cada vez que un registro es modificado.
    *   `Appointment.status`: Por defecto, un turno nuevo se establece como `BOOKED`.

### Consideraciones de Rendimiento

*   **Consultas de Disponibilidad**: La lógica para determinar la disponibilidad deberá combinar la consulta de `WorkingHours` y los `Appointment`s existentes para una fecha y servicio determinados. Los índices en `WorkingHours.userId` y `Appointment.userId` junto con `Appointment.startTime` serán cruciales para que estas consultas sean rápidas.
*   **Manejo de la Zona Horaria**: Prisma almacena `DateTime` en UTC por defecto. Es esencial que la aplicación maneje la conversión a la zona horaria del profesional y/o del cliente al mostrar y permitir la reserva de turnos. Esto es una consideración a nivel de aplicación, pero su impacto en la base de datos reside en la necesidad de almacenar `DateTime` con la precisión adecuada.
*   **Escalabilidad (para un mono-usuario)**: Dado el alcance de "mono usuario" y "un solo proyecto", el volumen de datos no se espera que sea masivo. El diseño prioriza la claridad, la integridad de los datos y la eficiencia para las operaciones más comunes (visualización de calendario, reserva de turnos) en este contexto. La elección de UUIDs, si bien ligeramente más lenta que los enteros secuenciales en indexación en algunos casos, es insignificante para este volumen de datos y aporta flexibilidad.
*   **`WorkingHours` `startTime` y `endTime` como `String`**: Almacenar la hora como `String` ("HH:MM") simplifica el esquema y la entrada de datos. Sin embargo, cualquier lógica compleja de cálculo de tiempo (ej. superposiciones, duraciones) deberá ser implementada y gestionada robustamente en la capa de la aplicación, ya que el motor de base de datos no puede realizar operaciones de tiempo nativas en este formato. Para validaciones y cálculos, la aplicación deberá parsear estos strings a objetos de tiempo.