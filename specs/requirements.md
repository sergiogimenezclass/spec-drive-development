# Requisitos Funcionales y No Funcionales
 
 ## Requisitos Funcionales (RF)
 A partir de la idea: *Vamos a hacer una aplicación de turnos para que se pueda reservar turnos. En este caso de mono usuario. Y para un solo proyecto. Puede ser para una peluquería, puede ser para un psicólogo, puede ser para reservar turnos para una clase. Pero algo sencillo de 1 a 1. Nada más, es lo que tenemos. Juan, al proceso.*
 *   **RF-01 (Autenticación):** El sistema debe permitir a los actores (Profesional (Proveedor de Servicio), Cliente (Reservador de Turno)) iniciar sesión de forma segura.
 *   **RF-02 (Core):** El sistema debe resolver la problemática central: "Vamos a hacer una aplicación de turnos para que se pueda reservar turnos. En este caso de mono usuario. Y para un solo proyecto. Puede ser para una peluquería, puede ser para un psicólogo, puede ser para reservar turnos para una clase. Pero algo sencillo de 1 a 1. Nada más, es lo que tenemos. Juan, al proceso.".
 *   **RF-03 (Administración):** Se debe proveer un panel de control para gestionar recursos.
 
 ## Requisitos No Funcionales (RNF)
 *   **RNF-01 (Seguridad):** Cifrado de datos en tránsito (TLS/HTTPS).
 *   **RNF-02 (Rendimiento):** Tiempos de respuesta del backend inferiores a 300ms para endpoints CRUD.
 *   **RNF-03 (Usabilidad):** Interfaz fluida y accesible que cumpla con los estándares WCAG 2.1 AA.