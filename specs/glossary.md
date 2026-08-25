# Glosario de Términos del Proyecto

Este glosario define los términos clave utilizados en el proyecto "Sistema de Gestión de Citas y Turnos para Usuario Único". Proporciona traducciones sugeridas al inglés técnico, aplicables a variables de código, campos de base de datos y endpoints API, con el fin de asegurar la coherencia conceptual y terminológica en todo el equipo.

---

## 1. Términos Generales del Dominio

*   **Aplicación**: `Application`, `App`
    *   **Descripción**: El software completo que estamos desarrollando, destinado a gestionar citas y turnos.
    *   **Uso Sugerido**: N/A (Concepto general).
*   **Sistema**: `System`
    *   **Descripción**: El conjunto de componentes interconectados que conforman la aplicación.
    *   **Uso Sugerido**: N/A (Concepto general).
*   **Gestión**: `Management`
    *   **Descripción**: El proceso de organizar, controlar y supervisar recursos o procesos dentro de la aplicación (ej. gestión de turnos, gestión de disponibilidad).
    *   **Uso Sugerido**: `appointmentManagement`, `availabilityManagement`.
*   **Configuración**: `Configuration`, `Settings`
    *   **Descripción**: El proceso o los datos que definen las propiedades y opciones de funcionamiento del sistema o de una entidad (ej. configuración de servicios).
    *   **Uso Sugerido**: `serviceConfiguration`, `appSettings`.

---

## 2. Actores y Roles

*   **Profesional / Proveedor de Servicio**: `Professional`, `ServiceOwner`
    *   **Descripción**: El usuario principal de la aplicación, quien ofrece los servicios, gestiona su disponibilidad y sus citas.
    *   **Uso Sugerido**:
        *   **Variables/Campos DB**: `professionalId`, `professionalName`, `professionalEmail`.
        *   **Endpoints**: `/api/professional`, `/api/professional/settings`.
*   **Cliente / Reservador**: `Client`, `Customer`
    *   **Descripción**: La persona que reserva un turno o cita con el Profesional.
    *   **Uso Sugerido**:
        *   **Variables/Campos DB**: `clientId`, `clientName`, `clientEmail`.
        *   **Endpoints**: N/A (Los clientes interactúan con endpoints de `appointments`).
*   **Usuario**: `User`
    *   **Descripción**: Término genérico para cualquier persona que interactúa con el sistema (puede ser Cliente o Profesional). Se recomienda usar roles específicos (`Professional`, `Client`) cuando sea posible para mayor claridad.
    *   **Uso Sugerido**:
        *   **Variables/Campos DB**: `userId`, `userName`, `userPassword`.
        *   **Endpoints**: `/api/users/{id}` (si hay una API general de usuarios).

---

## 3. Entidades y Conceptos Clave

*   **Turno / Cita / Reserva**: `Appointment`, `Booking`
    *   **Descripción**: Un evento programado entre un Cliente y un Profesional para un servicio específico en una fecha y hora determinadas.
    *   **Uso Sugerido**:
        *   **Variables/Campos DB**: `appointmentId`, `bookingId`, `appointmentDate`, `appointmentStatus`.
        *   **Endpoints**: `/api/appointments`, `/api/bookings`.
*   **Servicio / Tipo de Cita**: `Service`, `ServiceType`
    *   **Descripción**: Una actividad específica que el Profesional ofrece y que puede ser reservada (ej. "Corte de pelo", "Sesión de terapia"). Cada servicio tiene una duración y un nombre.
    *   **Uso Sugerido**:
        *   **Variables/Campos DB**: `serviceId`, `serviceName`, `serviceDuration`.
        *   **Endpoints**: `/api/services`.
*   **Disponibilidad / Bloque de Disponibilidad**: `Availability`, `TimeSlot`, `AvailabilitySlot`
    *   **Descripción**: Un período de tiempo en el que el Profesional ha indicado que está disponible para aceptar reservas.
    *   **Uso Sugerido**:
        *   **Variables/Campos DB**: `availabilityId`, `startTime`, `endTime`, `slotDate`.
        *   **Endpoints**: `/api/availability`, `/api/professional/availability`.
*   **Calendario**: `Calendar`
    *   **Descripción**: Interfaz visual que muestra los turnos reservados y/o la disponibilidad del Profesional.
    *   **Uso Sugerido**: `professionalCalendar`, `calendarView`.
*   **Cuenta (de usuario)**: `Account`, `UserAccount`
    *   **Descripción**: El registro de un usuario en el sistema, que incluye sus credenciales (email, contraseña) y configuraciones personales.
    *   **Uso Sugerido**: `accountId`, `userAccountData`.

---

## 4. Acciones y Funcionalidades

*   **Reservar (un turno/cita)**: `Book`, `CreateAppointment`
    *   **Descripción**: La acción principal de un Cliente para seleccionar y confirmar un turno con un Profesional.
    *   **Uso Sugerido**:
        *   **Funciones/Métodos**: `bookAppointment()`, `createBooking()`.
        *   **Endpoints**: `POST /api/appointments`, `POST /api/bookings`.
*   **Cancelar (un turno/cita)**: `Cancel`, `CancelAppointment`
    *   **Descripción**: La acción de anular un turno previamente reservado, ya sea por el Cliente o el Profesional.
    *   **Uso Sugerido**:
        *   **Funciones/Métodos**: `cancelAppointment()`.
        *   **Endpoints**: `PATCH /api/appointments/{id}/cancel`, `DELETE /api/appointments/{id}`.
*   **Reagendar (un turno/cita)**: `Reschedule`, `RescheduleAppointment`
    *   **Descripción**: La acción de cambiar la fecha u hora de un turno existente, sin cancelarlo por completo.
    *   **Uso Sugerido**:
        *   **Funciones/Métodos**: `rescheduleAppointment()`.
        *   **Endpoints**: `PATCH /api/appointments/{id}/reschedule`.
*   **Gestionar Disponibilidad**: `ManageAvailability`, `UpdateAvailability`
    *   **Descripción**: La acción del Profesional de definir, modificar o eliminar sus bloques de tiempo disponibles para reservas.
    *   **Uso Sugerido**:
        *   **Funciones/Métodos**: `manageProfessionalAvailability()`.
        *   **Endpoints**: `PUT /api/professional/availability`, `POST /api/professional/availability`.
*   **Autenticación**: `Authentication`, `Auth`
    *   **Descripción**: El proceso de verificar la identidad de un usuario (Profesional o Cliente) en el sistema.
    *   **Uso Sugerido**:
        *   **Módulo/Servicio**: `authService`.
        *   **Endpoints**: `POST /api/auth/login`, `POST /api/auth/register`.
*   **Registro (de usuario)**: `Register`, `SignUp`
    *   **Descripción**: La acción de crear una nueva cuenta de usuario en el sistema.
    *   **Uso Sugerido**:
        *   **Funciones/Métodos**: `registerUser()`.
        *   **Endpoints**: `POST /api/auth/register`.
*   **Iniciar Sesión**: `Login`, `SignIn`
    *   **Descripción**: La acción de un usuario de acceder a su cuenta en el sistema.
    *   **Uso Sugerido**:
        *   **Funciones/Métodos**: `loginUser()`.
        *   **Endpoints**: `POST /api/auth/login`.

---

## 5. Atributos y Estados

*   **Email**: `email`
    *   **Descripción**: La dirección de correo electrónico del usuario, utilizada como identificador para la autenticación y para el envío de notificaciones.
    *   **Uso Sugerido**: `userEmail`, `professionalEmail`, `clientEmail`.
*   **Contraseña**: `password`
    *   **Descripción**: La credencial secreta utilizada para la autenticación de usuario.
    *   **Uso Sugerido**: `userPassword`.
*   **Fecha**: `date`
    *   **Descripción**: Un valor que representa un día específico.
    *   **Uso Sugerido**: `appointmentDate`, `slotDate`.
*   **Hora de Inicio**: `startTime`, `startAt`
    *   **Descripción**: La hora precisa en que comienza un evento (un turno, un bloque de disponibilidad).
    *   **Uso Sugerido**: `appointmentStartTime`, `slotStartAt`.
*   **Hora de Fin**: `endTime`, `endAt`
    *   **Descripción**: La hora precisa en que finaliza un evento (un turno, un bloque de disponibilidad).
    *   **Uso Sugerido**: `appointmentEndTime`, `slotEndAt`.
*   **Duración**: `duration`
    *   **Descripción**: La longitud de un servicio o turno, generalmente expresada en minutos.
    *   **Uso Sugerido**: `serviceDuration`, `appointmentDurationMinutes`.
*   **Estado (general)**: `status`
    *   **Descripción**: Un atributo que indica la condición actual de una entidad, como un turno.
    *   **Uso Sugerido**: `appointmentStatus`.
*   **Estado Pendiente**: `PENDING`
    *   **Descripción**: Valor del estado de un turno que indica que está esperando confirmación o acción.
    *   **Uso Sugerido**: `AppointmentStatus.PENDING` (Enum).
*   **Estado Confirmado**: `CONFIRMED`
    *   **Descripción**: Valor del estado de un turno que indica que ha sido aceptado y programado.
    *   **Uso Sugerido**: `AppointmentStatus.CONFIRMED` (Enum).
*   **Estado Cancelado**: `CANCELLED`
    *   **Descripción**: Valor del estado de un turno que indica que ha sido anulado.
    *   **Uso Sugerido**: `AppointmentStatus.CANCELLED` (Enum).
*   **Notificación**: `Notification`
    *   **Descripción**: Mensaje o alerta enviado a un usuario (Profesional o Cliente), principalmente por correo electrónico.
    *   **Uso Sugerido**: `sendNotification()`, `emailNotification`.
*   **Asunto (Email)**: `subject`
    *   **Descripción**: El título o la línea de asunto de un correo electrónico de notificación.
    *   **Uso Sugerido**: `emailSubject`.
*   **Mensaje (Email)**: `message`, `body`
    *   **Descripción**: El contenido principal de un correo electrónico de notificación.
    *   **Uso Sugerido**: `emailMessage`, `notificationBody`.

---

## 6. Conceptos Técnicos

*   **Base de Datos**: `Database`, `DB`
    *   **Descripción**: El sistema de almacenamiento persistente para todos los datos de la aplicación.
    *   **Uso Sugerido**: `dbConnection`, `databaseClient`.
*   **Tabla**: `Table`
    *   **Descripción**: Una colección estructurada de datos dentro de una base de datos relacional (ej. `users`, `appointments`).
    *   **Uso Sugerido**: `usersTable`, `appointmentsTable`.
*   **Campo / Columna**: `Field`, `Column`
    *   **Descripción**: Un atributo específico dentro de una tabla de base de datos o una propiedad de un objeto de datos.
    *   **Uso Sugerido**: `columnName`, `dataField`.
*   **Endpoint (API)**: `Endpoint`
    *   **Descripción**: Una URL específica que expone una funcionalidad de la API REST para interactuar con el sistema.
    *   **Uso Sugerido**: `/api/appointments`, `/api/auth/login`.
*   **Variable**: `Variable`
    *   **Descripción**: Un identificador que apunta a un valor almacenado en la memoria durante la ejecución del código.
    *   **Uso Sugerido**: `myVariable`, `appointmentList`.