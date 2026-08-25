# Ficha Técnica del Proyecto: Turnos
 
 ## Información General
 *   **Idea Semilla:** Vamos a hacer una aplicación de turnos para que se pueda reservar turnos. En este caso de mono usuario. Y para un solo proyecto. Puede ser para una peluquería, puede ser para un psicólogo, puede ser para reservar turnos para una clase. Pero algo sencillo de 1 a 1. Nada más, es lo que tenemos. Juan, al proceso.
 *   **Dominio:** Gestión de Citas y Turnos
 *   **Tipo de Producto:** Web Application (Herramienta para Usuario Único)
 *   **Actores Detectados:** Profesional (Proveedor de Servicio), Cliente (Reservador de Turno)
 
 ## Resumen de Respuestas clave
 *   **q_auth:** Email y Contraseña tradicional
*   **q_database:** Relacional (PostgreSQL/MySQL)
*   **q_features_core:** Reservar el turno y la gestion del mismo por parte del usuario
*   **q_user_roles_client_booking:** Ambos: el proveedor gestiona y los clientes reservan públicamente
*   **q_admin_management_actions:** El usuario puede reservar turnos, los puede cancelar y los puede reagendar.
*   **q_notifications_strategy:** Solo Email
*   **q_deployment_strategy:** Va a ser entre un servidor VPS y un hosting compartido.
*   **q_payment_integration:** No se contempla cobrar por turno reservado.
 
 ---
 *Documento generado automáticamente por [Spec IDE](file:///home/sergio/Documents/src/programador 2026/spect-first/app.py).*