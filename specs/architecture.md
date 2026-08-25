# Arquitectura de la Aplicación de Gestión de Turnos (Mono Usuario)

## 1. Pila Tecnológica Propuesta

Considerando los requisitos de un sistema de gestión de turnos "mono usuario" y la necesidad de simplicidad y eficiencia, se propone la siguiente pila tecnológica:

*   **Frontend (Cliente Web):**
    *   **Tecnología:** **Vue.js 3 (con Composition API) y Vite.**
    *   **Estilos:** **Tailwind CSS.**
    *   **Justificación:** Vue.js es un framework progresivo y reactivo, conocido por su curva de aprendizaje suave y excelente rendimiento. Permite construir interfaces de usuario interactivas y ricas con un código limpio y modular. Vite proporciona un entorno de desarrollo extremadamente rápido y optimiza la construcción de la aplicación para producción. Tailwind CSS facilitará un desarrollo rápido y consistente de la interfaz de usuario con un enfoque de utilidades, garantizando un diseño responsivo y adaptable a diferentes dispositivos, lo cual es crucial para la reserva pública de turnos. Los archivos estáticos resultantes pueden ser servidos eficientemente.

*   **Backend (Servidor API):**
    *   **Tecnología:** **Python 3 con el microframework Flask.**
    *   **ORM:** **SQLAlchemy.**
    *   **Justificación:** Flask es ligero, flexible y se integra bien con el ecosistema de Python. Es ideal para construir APIs RESTful de manera eficiente, lo cual es adecuado para la comunicación con un frontend SPA. SQLAlchemy proporciona una potente capa de abstracción para la base de datos, permitiendo trabajar con objetos Python en lugar de SQL puro, lo que mejora la productividad y el mantenimiento del código. Python es una opción robusta y versátil, con una gran comunidad y bibliotecas para todo lo necesario (autenticación, envío de emails, etc.).

*   **Base de Datos:**
    *   **Tecnología:** **PostgreSQL.**
    *   **Justificación:** PostgreSQL es una de las bases de datos relacionales de código abierto más avanzadas, robustas y fiables. Ofrece una excelente integridad de datos, rendimiento y una rica característica set que supera a MySQL en muchos aspectos, siendo una elección sólida para gestionar datos estructurados como usuarios, servicios, disponibilidades y reservas de turnos. Su madurez y extensibilidad garantizan la escalabilidad y estabilidad a largo plazo.

*   **Servidor y Despliegue:**
    *   **Servidor de Aplicación:** **Gunicorn (WSGI HTTP Server para Flask).**
    *   **Servidor Web/Proxy Inverso:** **Nginx.**
    *   **Contenedorización:** **Docker y Docker Compose.**
    *   **Infraestructura de Hosting:** **VPS (Virtual Private Server).**
    *   **Justificación:**
        *   **VPS:** Proporciona un entorno dedicado y control total sobre el sistema operativo, permitiendo instalar y configurar todas las tecnologías necesarias (Python, PostgreSQL, Nginx, Docker) de manera óptima para el rendimiento y la seguridad. Es superior al hosting compartido para aplicaciones dinámicas que requieren una base de datos y un servidor de aplicación.
        *   **Docker y Docker Compose:** Simplificarán enormemente el desarrollo, despliegue y gestión de los diferentes componentes (frontend, backend, base de datos) al aislarlos en contenedores. Esto garantiza la consistencia del entorno entre desarrollo y producción, y facilita el escalado y la recuperación.
        *   **Nginx:** Actuará como proxy inverso para el servidor Gunicorn (que sirve la aplicación Flask) y también se encargará de servir los archivos estáticos del frontend (la aplicación Vue.js compilada). Esto mejora el rendimiento, la seguridad y permite la gestión de certificados SSL.
        *   **Gunicorn:** Es un servidor WSGI eficiente y ampliamente utilizado para aplicaciones Python en producción.

## 2. Decisiones de Diseño Clave e Infraestructura

Las siguientes decisiones fundamentales guiarán el desarrollo y la operación del sistema:

*   **Estrategia de Despliegue (refinada):**
    *   La aplicación completa se desplegará en un **único VPS** mediante **Docker Compose**. Esto significa que Nginx, el contenedor de la aplicación Flask y el contenedor de PostgreSQL residirán en el mismo servidor virtual. El frontend (aplicación Vue.js) se construirá como archivos estáticos que Nginx servirá directamente.
    *   Aunque se mencionó "hosting compartido", la naturaleza de una aplicación web dinámica con backend y base de datos relacional se beneficia enormemente del control y la flexibilidad que ofrece un VPS, especialmente cuando se usa Docker para una gestión eficiente. Un hosting compartido podría ser utilizado para alojar los archivos estáticos del frontend si se deseara una separación, pero la simplicidad y el control de un único VPS con Docker Compose para todos los componentes es preferible para este proyecto "mono usuario".
    *   **CI/CD (Integración y Entrega Continua):** Se recomienda implementar un flujo de CI/CD básico (por ejemplo, con GitHub Actions o GitLab CI) para automatizar el build del frontend, la creación de imágenes Docker del backend y el despliegue al VPS, asegurando entregas rápidas y consistentes.

*   **Autenticación y Autorización:**
    *   **Método:** Email y Contraseña tradicional.
    *   **Implementación Backend:** Se utilizarán **JSON Web Tokens (JWT)** para la autenticación entre el frontend SPA y el backend API. Después de un inicio de sesión exitoso, el backend emitirá un JWT que el frontend almacenará (preferiblemente en `localStorage` o `sessionStorage`) y enviará en los encabezados de cada solicitud protegida.
    *   Las contraseñas se almacenarán de forma segura utilizando un algoritmo de hash robusto (ej. bcrypt) en la base de datos.
    *   Para la gestión del "mono usuario" (el profesional), este será el único usuario con privilegios para configurar servicios y gestionar su disponibilidad. Los clientes no requieren autenticación para reservar, solo para gestionar sus propias reservas si se desea ofrecer esa funcionalidad más allá de la cancelación por enlace.

*   **Diseño de API:**
    *   La comunicación entre el frontend y el backend se realizará a través de una **API RESTful** utilizando **JSON** como formato de intercambio de datos. Esto asegura una clara separación de responsabilidades y facilita el desarrollo.

*   **Estrategia de Notificaciones:**
    *   **Canal:** Únicamente **Email**.
    *   **Implementación:** El backend integrará un cliente SMTP (Simple Mail Transfer Protocol) o una API de un proveedor de servicios de email transaccional (ej. SendGrid, Mailgun) para enviar notificaciones de confirmación de reserva, recordatorios, cancelaciones y reagendamientos tanto a los clientes como al profesional.

*   **Gestión de Disponibilidad:**
    *   El sistema permitirá al profesional definir sus horarios de trabajo regulares y excepciones (días libres, horarios especiales). El backend calculará las franjas horarias disponibles para la reserva, teniendo en cuenta la duración de los servicios y los turnos ya reservados.

*   **Escalabilidad y Fiabilidad:**
    *   Para una aplicación "mono usuario" inicial, el escalado vertical (aumentar los recursos del VPS) será suficiente.
    *   Se implementarán **copias de seguridad diarias automatizadas** de la base de datos (por ejemplo, a un almacenamiento de objetos externo como S3), esenciales para la recuperación ante desastres.

## 3. Estructura de Módulos del Sistema y Flujo de Datos

El sistema se puede conceptualizar en los siguientes módulos principales, interactuando a través de una API:

### Estructura de Módulos del Sistema

1.  **Módulo de Autenticación y Usuarios:**
    *   **Responsabilidad:** Gestión de registro, inicio de sesión (email/contraseña), cierre de sesión, recuperación de contraseña para el profesional. Gestión del perfil del profesional.
    *   **Tecnologías:** Flask-Login o JWT para la sesión, bcrypt para hashing de contraseñas.

2.  **Módulo de Servicios y Configuración:**
    *   **Responsabilidad:** Permitir al profesional definir y gestionar los tipos de servicios que ofrece (ej. "Consulta de 30 min", "Clase de 1 hora"), su duración estándar.
    *   **Tecnologías:** Modelos de SQLAlchemy para almacenar configuraciones.

3.  **Módulo de Disponibilidad y Horarios:**
    *   **Responsabilidad:** Permitir al profesional establecer su disponibilidad general (días y horas laborables) y excepciones (bloqueo de días/horas específicos, festivos). Calcular las franjas horarias disponibles para la reserva en función de los servicios y turnos ya ocupados.
    *   **Tecnologías:** Lógica de negocio en Flask para manejo de fechas y horas, modelos de SQLAlchemy para almacenar disponibilidad.

4.  **Módulo de Reservas (Turnos):**
    *   **Responsabilidad:**
        *   **Clientes:** Interfaz pública para buscar disponibilidad y realizar nuevas reservas.
        *   **Profesional:** Visualización de todos los turnos (en un calendario), capacidad para cancelar o reagendar turnos existentes.
        *   Validación de la disponibilidad antes de confirmar una reserva.
    *   **Tecnologías:** Modelos de SQLAlchemy para turnos, lógica de negocio en Flask.

5.  **Módulo de Notificaciones:**
    *   **Responsabilidad:** Envío de correos electrónicos automáticos para confirmar reservas, enviar recordatorios, notificar cancelaciones o reagendamientos a clientes y al profesional.
    *   **Tecnologías:** Integración de bibliotecas SMTP de Python o API de servicio de email (ej. `smtplib` o `requests` para APIs de terceros).

### Flujo de Datos (Ejemplo: Reserva de un Turno por un Cliente)

Este es un ejemplo simplificado de cómo los datos fluirían a través del sistema cuando un cliente reserva un turno:

1.  **Inicio de la Sesión de Reserva:**
    *   El **Cliente** accede a la URL pública de la aplicación de turnos a través de su navegador web.
    *   El **Frontend (Vue.js)** se carga y realiza una solicitud GET a la **API del Backend (Flask)** para obtener la configuración de servicios y la disponibilidad general del profesional.

2.  **Visualización de Disponibilidad:**
    *   El **Backend** consulta el **Módulo de Servicios y Configuración** y el **Módulo de Disponibilidad y Horarios** en la **Base de Datos (PostgreSQL)** para obtener la información necesaria.
    *   El **Backend** procesa esta información para calcular las franjas horarias disponibles para los próximos días/semanas.
    *   El **Backend** devuelve esta lista de franjas horarias disponibles en formato JSON al **Frontend**.
    *   El **Frontend** renderiza un calendario o una lista de opciones para que el **Cliente** elija.

3.  **Selección y Envío de Reserva:**
    *   El **Cliente** selecciona un servicio, una fecha y una franja horaria específica, e ingresa sus datos personales (nombre, email).
    *   El **Frontend** envía una solicitud POST a la **API del Backend** con los detalles del turno y los datos del cliente.

4.  **Procesamiento y Confirmación de Reserva:**
    *   El **Backend (Módulo de Reservas)** recibe la solicitud.
    *   Realiza una validación final de la disponibilidad en la **Base de Datos** para evitar reservas dobles (considerando concurrencia si aplica, aunque para "mono usuario" es menos crítico).
    *   Si la reserva es válida y la franja está disponible:
        *   Crea un nuevo registro en la tabla de `turnos` en la **Base de Datos (PostgreSQL)**.
        *   Invoca al **Módulo de Notificaciones** para enviar un correo electrónico de confirmación al **Cliente** y, opcionalmente, una notificación al **Profesional**.
    *   Si la reserva no es válida (ej. franja ya ocupada), devuelve un error.
    *   El **Backend** responde al **Frontend** con el estado de la reserva (éxito o error) en formato JSON.

5.  **Notificación al Cliente:**
    *   El **Frontend** muestra un mensaje de confirmación (o error) al **Cliente**.
    *   El **Cliente** recibe el email de confirmación de su turno.

### Diagrama Conceptual de Interacción

```mermaid
graph TD
    A[Cliente <br> (Navegador Web)] --> B(Frontend <br> (Vue.js, Nginx));
    B --> C(Backend API <br> (Flask, Gunicorn));
    C --> D(Base de Datos <br> (PostgreSQL));

    subgraph Backend Services
        C -- Consulta/Almacena --> M1[Módulo de Autenticación y Usuarios];
        C -- Consulta/Almacena --> M2[Módulo de Servicios y Configuración];
        C -- Consulta/Almacena --> M3[Módulo de Disponibilidad y Horarios];
        C -- Consulta/Almacena --> M4[Módulo de Reservas];
        C -- Envía Mensajes --> M5[Módulo de Notificaciones <br> (Email)];
    end

    M1 --> D;
    M2 --> D;
    M3 --> D;
    M4 --> D;
    M5 --> E[Servicio de Email <br> (SMTP)];

    E --> A; % Notificaciones llegan al cliente por email
    M5 --> A; % Notificaciones llegan al profesional por email (mismo actor en este contexto)

    style A fill:#f9f,stroke:#333,stroke-width:2px;
    style B fill:#bbf,stroke:#333,stroke-width:2px;
    style C fill:#bfb,stroke:#333,stroke-width:2px;
    style D fill:#fb9,stroke:#333,stroke-width:2px;
    style E fill:#ddd,stroke:#333,stroke-width:2px;

    linkStyle 0 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 1 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 2 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 3 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 4 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 5 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 6 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 7 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 8 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 9 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 10 stroke:#000,stroke-width:1.5px,fill:none;
    linkStyle 11 stroke:#000,stroke-width:1.5px,fill:none;

```