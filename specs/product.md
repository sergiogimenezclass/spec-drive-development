# AgendaPro Simple: Aplicación de Gestión de Turnos para Profesionales

## 1. Visión General del Producto y Propuesta de Valor

**Nombre del Producto (Tentativo):** AgendaPro Simple

**Visión General:**
AgendaPro Simple es una aplicación web intuitiva y enfocada en un único profesional, diseñada para simplificar la gestión de sus citas y permitir a sus clientes reservar turnos de manera autónoma y conveniente. Pensada para profesionales individuales como peluqueros, psicólogos, tutores o cualquier proveedor de servicios 1-a-1, esta herramienta digitaliza el proceso de agendamiento, liberando tiempo valioso y mejorando la experiencia tanto para el profesional como para sus clientes.

**Propuesta de Valor:**

*   **Para el Profesional:**
    *   **Eficiencia Operativa:** Digitaliza la agenda, reduciendo la necesidad de gestionar turnos manualmente por teléfono o mensajes, permitiendo al profesional enfocarse en su servicio principal.
    *   **Control Total:** Permite al profesional definir su disponibilidad, servicios y gestionar todos los turnos desde una única plataforma.
    *   **Presencia Profesional:** Ofrece una herramienta moderna y accesible para que sus clientes interactúen, proyectando una imagen organizada y profesional.
*   **Para el Cliente:**
    *   **Conveniencia 24/7:** Facilita la reserva de turnos en cualquier momento y desde cualquier lugar, sin depender de los horarios de atención del profesional.
    *   **Autogestión Sencilla:** Permite a los clientes cancelar o reagendar sus propios turnos de forma rápida y sin intermediarios (dentro de las políticas establecidas).
    *   **Comunicación Clara:** Asegura que los clientes reciban confirmaciones y recordatorios importantes vía email.

**Enfoque:**
El producto se concibe como una solución "mono-usuario" en el sentido de que cada instancia de la aplicación está dedicada a la gestión de turnos de un único profesional. Se prioriza la simplicidad y la funcionalidad esencial para la gestión de turnos 1-a-1, sin complejidades como multi-tenant, pagos integrados o roles de equipo.

## 2. Objetivos de Negocio y Métricas de Éxito

**Objetivo Principal:**
Proveer una solución digital robusta y fácil de usar para que un profesional individual gestione su agenda de turnos de manera eficiente y mejore la experiencia de reserva para sus clientes.

**Objetivos de Negocio Específicos:**

1.  **Digitalizar la Gestión de Turnos:** Transicionar la agenda de turnos del profesional de un método manual a una plataforma online.
2.  **Aumentar la Eficiencia del Profesional:** Reducir el tiempo administrativo dedicado a la gestión de citas (reservas, cancelaciones, cambios).
3.  **Mejorar la Experiencia del Cliente:** Ofrecer una opción de reserva y autogestión de turnos conveniente y accesible 24/7 para los clientes.
4.  **Minimizar Conflictos de Agendamiento:** Reducir la probabilidad de dobles reservas o errores en la asignación de turnos.

**Métricas de Éxito (KPIs):**

1.  **Tasa de Adopción de la Reserva Online:** Porcentaje de turnos que son reservados a través de la aplicación, en comparación con otros métodos.
2.  **Número de Turnos Gestionados:** Cantidad total de turnos creados, confirmados y completados a través de la plataforma en un período determinado.
3.  **Tasa de Autogestión de Clientes:** Porcentaje de cancelaciones y reagendamientos de turnos que son realizados directamente por los clientes a través del sistema.
4.  **Reducción del Tiempo de Gestión:** Estimación del ahorro de tiempo del profesional en tareas administrativas relacionadas con turnos (medido por encuestas cualitativas o comparación antes/después).
5.  **Tasa de No-Show:** Medición de la reducción en el porcentaje de clientes que no se presentan a su turno, potencialmente influenciada por recordatorios automáticos.
6.  **Satisfacción del Usuario (Profesional y Cliente):** Feedback cualitativo sobre la facilidad de uso y la utilidad de la aplicación.

## 3. Usuarios, Actores y sus Roles detallados

El sistema contempla dos actores principales, cada uno con roles y responsabilidades diferenciadas:

### 3.1. Profesional (Proveedor de Servicio)

*   **Descripción:** Es el usuario principal de la aplicación, el dueño de la cuenta y el proveedor de los servicios. Gestiona su disponibilidad, configura sus servicios y supervisa todos los turnos.
*   **Roles y Responsabilidades Clave:**
    *   **Autenticación:**
        *   Registrarse e iniciar sesión en el sistema usando su email y una contraseña tradicional.
        *   Gestionar su perfil (cambiar contraseña, actualizar datos de contacto).
    *   **Configuración de Servicios:**
        *   Crear, editar y eliminar los servicios que ofrece, incluyendo su nombre, descripción y duración estándar.
    *   **Gestión de Disponibilidad:**
        *   Definir su horario de trabajo semanal (días y franjas horarias disponibles).
        *   Crear bloques de indisponibilidad (ej. almuerzos, pausas, reuniones, vacaciones, días festivos) que impidan la reserva en esos periodos.
    *   **Visualización y Gestión de Turnos:**
        *   Visualizar todos los turnos reservados en una interfaz de calendario (vista diaria, semanal, mensual).
        *   Ver los detalles de cada turno (cliente, servicio, fecha, hora, estado).
        *   Confirmar, cancelar o reagendar turnos de clientes de forma manual (lo cual notificará al cliente).
        *   Marcar turnos como "completados" o "no presentados".
    *   **Notificaciones:**
        *   Recibir notificaciones por email sobre nuevas reservas, cancelaciones o reagendamientos realizados por los clientes.

### 3.2. Cliente (Reservador de Turno)

*   **Descripción:** Es la persona que busca y reserva un turno con el profesional. No necesita crear una cuenta en el sistema para reservar; su identidad se asocia a la información proporcionada al momento de la reserva y a través de enlaces únicos para la autogestión.
*   **Roles y Responsabilidades Clave:**
    *   **Búsqueda y Reserva:**
        *   Acceder a la página de reservas del profesional (pública).
        *   Ver la disponibilidad de horarios y servicios del profesional.
        *   Seleccionar un servicio, fecha y horario disponible.
        *   Proporcionar sus datos de contacto (Nombre, Email, Teléfono) para completar la reserva.
    *   **Autogestión de Turnos:**
        *   Recibir un email de confirmación de turno que incluye un enlace único para cancelar o reagendar su propia cita.
        *   Cancelar un turno previamente reservado a través del enlace de autogestión (dentro de las políticas de cancelación).
        *   Reagendar un turno previamente reservado a través del enlace de autogestión, seleccionando un nuevo horario disponible (dentro de las políticas de reagendamiento).
    *   **Notificaciones:**
        *   Recibir confirmaciones de reserva, recordatorios de turnos, y notificaciones de cualquier cambio (cancelación, reagendamiento) vía email.

## 4. Reglas de Negocio Críticas e Inquebrantables

Estas reglas son fundamentales para la integridad, funcionalidad y lógica del negocio del sistema de gestión de turnos:

1.  **Disponibilidad Unívoca del Slot:**
    *   Un slot de tiempo definido por el profesional (`Fecha`, `Hora de Inicio`, `Hora de Fin`) solo puede ser reservado por **un único cliente** para **un único servicio** a la vez. No se permiten dobles reservas.
    *   Ejemplo: Si el profesional tiene un turno de 10:00 a 11:00 AM, ese periodo no puede ser reservado por otro cliente simultáneamente.

2.  **Reserva Basada en Disponibilidad del Profesional:**
    *   Un turno solo puede ser reservado en franjas horarias que el profesional haya marcado explícitamente como disponibles y que no estén ya ocupadas.
    *   Ejemplo: Un cliente no puede reservar un turno a las 3 PM si el profesional ha configurado su horario de trabajo hasta las 2 PM o tiene bloqueado ese horario por un descanso.

3.  **Límite Mínimo de Antelación para Reservas:**
    *   Los clientes no pueden reservar un turno con una antelación menor a un umbral predefinido por el profesional (ej. no se puede reservar para los próximos 30 minutos o 1 hora).
    *   Ejemplo: Si el umbral es de 1 hora, un cliente a las 10:00 AM no puede reservar un turno para antes de las 11:00 AM.

4.  **Límites de Antelación para Cancelación/Reagendamiento por Cliente:**
    *   Los clientes pueden cancelar o reagendar su propio turno solo hasta un tiempo límite antes de la hora de la cita, definido por el profesional (ej. 24 horas antes del turno). Después de este límite, solo el profesional puede realizar cambios.
    *   Ejemplo: Si el turno es el viernes a las 10:00 AM y el límite es 24 horas, el cliente puede cancelar hasta el jueves a las 9:59 AM.

5.  **Integridad del Historial de Turnos (Borrado Lógico):**
    *   Los turnos no deben ser eliminados físicamente de la base de datos una vez que han sido creados o gestionados. En su lugar, deben ser marcados con un estado (ej. "cancelado", "completado", "no presentado") para mantener un historial auditable.
    *   Ejemplo: Si un cliente cancela un turno, el registro del turno cambia su estado a "Cancelado" y el slot de disponibilidad se libera, pero el registro original permanece para fines de reporte.

6.  **No Permite Pagos Directos:**
    *   La aplicación **no debe integrar** ni procesar ningún tipo de pago por los turnos. La funcionalidad se limita a la gestión de la reserva y la agenda.
    *   Ejemplo: Durante el proceso de reserva, no habrá opciones ni campos para introducir datos de tarjeta de crédito o métodos de pago.

7.  **Notificaciones Obligatorias por Email:**
    *   Toda acción significativa sobre un turno (reserva, cancelación, reagendamiento) debe generar una notificación por email tanto al cliente afectado como al profesional.
    *   Ejemplo: Cuando un cliente reserva un turno, ambos reciben un email de confirmación. Cuando el profesional cancela, ambos reciben un email de cancelación.

8.  **Unicidad del Profesional por Instancia:**
    *   La aplicación está diseñada para la gestión de un único profesional. No hay funcionalidad para que múltiples profesionales gestionen sus agendas bajo una misma instancia de la aplicación o con múltiples cuentas de profesional en la misma base de datos.
    *   Ejemplo: El sistema no tiene un "panel de administración global" para varios profesionales; cada despliegue es para un profesional específico.

## 5. Casos de Uso Principales e Historias Clave

### Casos de Uso del Profesional

*   **CU-P01: Autenticación y Gestión de Perfil**
    *   **Historia Clave:** Como Profesional, quiero registrarme con mi email y contraseña para crear mi cuenta y poder acceder al sistema.
    *   **Historia Clave:** Como Profesional, quiero iniciar sesión con mis credenciales para acceder a mi panel de control de turnos.
    *   **Historia Clave:** Como Profesional, quiero poder actualizar mi información de contacto y detalles de perfil para que los clientes tengan los datos correctos.
    *   **Historia Clave:** Como Profesional, quiero poder cambiar mi contraseña para mantener mi cuenta segura.

*   **CU-P02: Configuración de Servicios**
    *   **Historia Clave:** Como Profesional, quiero definir los servicios que ofrezco (ej. "Corte de pelo", "Consulta Terapéutica", "Clase de Yoga") con su duración y descripción, para que los clientes puedan elegir.
    *   **Historia Clave:** Como Profesional, quiero poder editar o eliminar un servicio existente si cambia mi oferta.

*   **CU-P03: Gestión de Disponibilidad**
    *   **Historia Clave:** Como Profesional, quiero establecer mi horario de trabajo semanal (días y horas) para indicar cuándo estoy disponible para recibir clientes.
    *   **Historia Clave:** Como Profesional, quiero bloquear franjas horarias específicas (ej. almuerzo, reuniones, descansos) dentro de mi horario de trabajo para que no se puedan reservar.
    *   **Historia Clave:** Como Profesional, quiero poder marcar días completos como no disponibles (ej. vacaciones, feriados) para que no se ofrezcan turnos en esas fechas.

*   **CU-P04: Visualización y Gestión de Turnos**
    *   **Historia Clave:** Como Profesional, quiero ver todos mis turnos programados en una vista de calendario clara para organizar mi día/semana/mes.
    *   **Historia Clave:** Como Profesional, quiero poder ver los detalles completos de cada turno reservado, incluyendo la información del cliente y el servicio solicitado.
    *   **Historia Clave:** Como Profesional, quiero poder cancelar un turno de un cliente y que el cliente reciba una notificación por email de la cancelación.
    *   **Historia Clave:** Como Profesional, quiero poder reagendar un turno de un cliente a un nuevo horario disponible y que el cliente reciba una notificación por email del cambio.
    *   **Historia Clave:** Como Profesional, quiero poder marcar un turno como "completado" o "no presentado" para mantener un registro preciso.

### Casos de Uso del Cliente

*   **CU-C01: Búsqueda y Reserva de Turno**
    *   **Historia Clave:** Como Cliente, quiero acceder fácilmente a la página de reservas del profesional para ver sus servicios y disponibilidad.
    *   **Historia Clave:** Como Cliente, quiero seleccionar un servicio y ver los horarios disponibles para ese servicio en diferentes fechas.
    *   **Historia Clave:** Como Cliente, quiero elegir un horario disponible, ingresar mis datos de contacto (nombre, email, teléfono) y confirmar la reserva de mi turno.
    *   **Historia Clave:** Como Cliente, quiero recibir una confirmación inmediata de mi reserva por email, incluyendo todos los detalles del turno y un enlace para autogestionar mi cita.

*   **CU-C02: Autogestión de Turno (Cancelación)**
    *   **Historia Clave:** Como Cliente, quiero poder cancelar mi turno a través de un enlace seguro en mi email de confirmación, siempre que sea antes del límite de tiempo establecido por el profesional.
    *   **Historia Clave:** Como Cliente, quiero recibir una notificación por email confirmando que mi turno ha sido cancelado exitosamente.

*   **CU-C03: Autogestión de Turno (Reagendamiento)**
    *   **Historia Clave:** Como Cliente, quiero poder reagendar mi turno a través de un enlace seguro en mi email de confirmación, seleccionando un nuevo horario disponible, siempre que sea antes del límite de tiempo.
    *   **Historia Clave:** Como Cliente, quiero recibir una notificación por email confirmando que mi turno ha sido reagendado exitosamente con los nuevos detalles.

*   **CU-C04: Recibir Notificaciones**
    *   **Historia Clave:** Como Cliente, quiero recibir un recordatorio por email de mi turno con una antelación configurable para no olvidarlo.
    *   **Historia Clave:** Como Cliente, quiero recibir notificaciones por email si el profesional realiza algún cambio en mi turno (ej. cancelación forzada, reagendamiento).