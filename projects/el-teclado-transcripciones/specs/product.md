# Product Definition: Turbo Whisper

## 1. Visión General del Producto y Propuesta de Valor

**Turbo Whisper** es una aplicación innovadora de dictado de voz y transcripción automática diseñada para transformar la interacción del usuario con cualquier aplicación que requiera entrada de texto. Utiliza tecnología avanzada de reconocimiento de voz, incluyendo un motor local (`Turbo Whisper`) y la opción de integración con servicios de IA externos (`Gemini API`), para convertir el habla en texto de manera instantánea y precisa.

Actuando como un teclado virtual inteligente, Turbo Whisper permite a los usuarios dictar texto en tiempo real directamente en documentos, correos electrónicos, chats o cualquier campo de texto, eliminando la necesidad de escribir manualmente. Además, ofrece funcionalidades de productividad como la gestión de atajos de teclado personalizados y un historial de transcripciones para referencia futura.

**Propuesta de Valor:**

*   **Eficiencia Superior:** Aumenta drásticamente la productividad al permitir la creación de texto a una velocidad mucho mayor que la escritura tradicional, liberando a los usuarios de la tediosa tarea de teclear.
*   **Comodidad Inigualable:** Proporciona una experiencia manos libres o con mínima interacción, ideal para situaciones en movimiento, usuarios con RSI (lesión por esfuerzo repetitivo) o aquellos que simplemente prefieren hablar en lugar de escribir.
*   **Flexibilidad y Universalidad:** Funciona como un teclado virtual integrado, lo que significa que el texto dictado puede insertarse en *cualquier* aplicación que acepte entrada de texto, sin limitaciones.
*   **Privacidad y Rendimiento:** Ofrece la opción de un motor de IA local (`Turbo Whisper`), garantizando que la voz y las transcripciones permanezcan completamente en el dispositivo del usuario, sin necesidad de conexión a internet ni envío de datos a la nube. También permite la elección de proveedores de IA externos para mayor precisión o capacidades específicas.
*   **Personalización Avanzada:** Permite a los usuarios personalizar su flujo de trabajo con atajos de teclado para frases comunes, comandos específicos o incluso insertar bloques de texto predefinidos.

## 2. Objetivos de Negocio y Métricas de Éxito

Dado que la aplicación se concibe como una herramienta local sin autenticación, los objetivos se centran en la adopción, la satisfacción del usuario y el rendimiento del producto.

**Objetivos de Negocio:**

*   **Aumentar la Productividad del Usuario:** Facilitar una forma más rápida y eficiente de introducir texto en el dispositivo, impactando positivamente en el flujo de trabajo diario de los usuarios.
*   **Establecerse como una Herramienta Esencial:** Convertirse en la solución de referencia para la transcripción de voz a texto para una amplia gama de usuarios y contextos.
*   **Ofrecer una Experiencia de Usuario Superior:** Garantizar que la interacción con la aplicación sea intuitiva, fluida y altamente fiable.
*   **Garantizar la Privacidad y Seguridad:** Proporcionar opciones de transcripción local para usuarios que priorizan la privacidad de sus datos.

**Métricas de Éxito:**

*   **Frecuencia de Uso:**
    *   Número promedio de sesiones de dictado por usuario al día/semana.
    *   Porcentaje de usuarios activos semanal/mensual que utilizan la función de dictado.
*   **Volumen de Transcripción:**
    *   Cantidad total de caracteres/palabras transcritas por usuario al día/semana.
    *   Longitud promedio de las transcripciones por sesión.
*   **Precisión y Latencia:**
    *   Tiempo promedio de respuesta desde que el usuario habla hasta que el texto aparece.
    *   Tasa de error de la transcripción (medible mediante pruebas internas y retroalimentación).
*   **Adopción de Funcionalidades Clave:**
    *   Porcentaje de usuarios que configuran y utilizan atajos de teclado personalizados.
    *   Porcentaje de usuarios que acceden al historial de transcripciones.
    *   Porcentaje de usuarios que alternan entre proveedores de IA (local vs. API externa).
*   **Satisfacción del Usuario:**
    *   Encuestas de satisfacción directas o calificaciones de la aplicación (si se distribuye en tiendas de aplicaciones).
    *   Retroalimentación cualitativa sobre la facilidad de uso y la utilidad.
*   **Rendimiento del Sistema:**
    *   Uso de CPU/RAM durante sesiones de dictado.
    *   Estabilidad de la aplicación (crashes por hora de uso).

## 3. Usuarios, Actores y sus Roles detallados

**Usuarios Principales (Usuarios Finales):**

*   **Redactor de Contenido:**
    *   **Rol:** Periodistas, escritores, bloggers, investigadores que necesitan capturar ideas rápidamente o redactar textos extensos.
    *   **Necesidades:** Transcripción rápida y precisa, facilidad para dictar estructuras de texto (párrafos, puntos), gestión de atajos para frases o términos comunes.
*   **Profesional Ocupado:**
    *   **Rol:** Ejecutivos, médicos, abogados, consultores que necesitan dictar correos electrónicos, informes, notas de reuniones o memorandos.
    *   **Necesidades:** Eficiencia, operación manos libres, integración fluida con aplicaciones de oficina, privacidad de la información.
*   **Estudiante / Académico:**
    *   **Rol:** Personas que toman apuntes de clases, conferencias, dictan trabajos o resúmenes de lecturas.
    *   **Necesidades:** Precisión en terminología específica, capacidad de revisar y editar transcripciones, facilidad de uso en entornos de aprendizaje.
*   **Usuarios con Necesidades Especiales:**
    *   **Rol:** Individuos con discapacidades motoras, dislexia u otras condiciones que dificultan la escritura manual.
    *   **Necesidades:** Accesibilidad, alta precisión de reconocimiento, interfaz sencilla y adaptable, soporte para diversos acentos y velocidades de habla.
*   **Usuario General:**
    *   **Rol:** Cualquier persona que busca una forma más cómoda y rápida de introducir texto en su dispositivo para tareas cotidianas como mensajes de chat, búsquedas web o llenado de formularios.
    *   **Necesidades:** Facilidad de uso, respuesta rápida, integración con sus aplicaciones favoritas.

**Actores Secundarios:**

*   **Sistema Operativo (OS):**
    *   **Rol:** Proveedor de la infraestructura subyacente para el funcionamiento del teclado virtual, acceso al micrófono y gestión de permisos.
    *   **Interacción:** Permite que Turbo Whisper se registre como un método de entrada, gestiona el acceso al hardware y notificaciones del sistema.
*   **Proveedor de IA Externo (Ej: Gemini API):**
    *   **Rol:** Servicio externo que proporciona un motor de reconocimiento de voz y transcripción, consumido por Turbo Whisper cuando el usuario lo selecciona.
    *   **Interacción:** Recibe flujos de audio (o sus características procesadas) de Turbo Whisper y devuelve texto transcrito.

## 4. Reglas de Negocio Críticas e Inquebrantables

Estas reglas son fundamentales para la funcionalidad, la experiencia del usuario y la integridad del producto.

1.  **Transcripción en Tiempo Real y Latencia Mínima:** El sistema debe transcribir y mostrar el texto dictado con una latencia inferior a 500 ms (preferiblemente 200 ms) entre la finalización de una frase y su aparición en pantalla.
    *   *Ejemplo:* Un usuario dice "Hola mundo", el texto "Hola mundo" debe aparecer casi instantáneamente en la aplicación de destino.
2.  **Integración como Teclado Virtual Universal:** Turbo Whisper debe emular el comportamiento de un teclado físico o virtual estándar, asegurando que el texto transcrito se inserte *directamente* en el punto de inserción (cursor) de cualquier aplicación que acepte entrada de texto.
    *   *Ejemplo:* Si el usuario está en Microsoft Word, Google Chrome o WhatsApp, el dictado debe aparecer en el área de texto activa.
3.  **Privacidad Inquebrantable en Modo Local:** Cuando el usuario selecciona "Turbo Whisper local" como proveedor de IA, ninguna señal de audio ni dato textual debe salir del dispositivo del usuario. Todo el procesamiento debe realizarse localmente.
    *   *Ejemplo:* Incluso si el dispositivo tiene conexión a internet, el audio no se envía a ningún servidor externo.
4.  **Consentimiento Explícito para Proveedores Externos:** Si el usuario elige un proveedor de IA externo (ej. Gemini API), debe ser informado de manera clara y explícita que su audio (o sus características) serán enviadas a un servicio externo para su procesamiento y debe dar su consentimiento antes de activar dicho modo.
    *   *Ejemplo:* Una ventana emergente de consentimiento que detalla la política de privacidad del proveedor externo antes de la primera activación.
5.  **Persistencia del Historial de Transcripciones:** Todas las transcripciones realizadas deben guardarse automáticamente y de forma persistente en el almacenamiento local del dispositivo (SQLite/JSON), hasta que el usuario decida eliminarlas explícitamente.
    *   *Ejemplo:* Después de cerrar y reabrir la aplicación, el usuario debe poder acceder a sus transcripciones pasadas.
6.  **Gestión y Persistencia de Atajos de Teclado:** Los atajos de teclado personalizados definidos por el usuario deben ser guardados de forma persistente y activarse de manera fiable cada vez que se detecte la frase clave.
    *   *Ejemplo:* Si un usuario configura "mi firma" para expandirse a "Atentamente, [Nombre del Usuario]", esto debe funcionar en todas las sesiones.
7.  **Estado Visual Claro del Micrófono:** La aplicación debe proporcionar un indicador visual claro (ej. icono de micrófono, onda de sonido) que muestre el estado actual del micrófono (activo/escuchando, inactivo, error/sin permiso).
    *   *Ejemplo:* Un icono rojo parpadeando cuando el micrófono está activo y una "X" sobre el icono si no hay permiso.
8.  **Manejo Inteligente de Puntuación y Espacios:** El sistema debe aplicar automáticamente la puntuación estándar (puntos, comas, signos de interrogación) y gestionar los espacios de manera apropiada durante el dictado para producir texto legible.
    *   *Ejemplo:* Dictar "hola coma como estas signo de interrogacion" debe resultar en "Hola, ¿cómo estás?".
9.  **Compatibilidad sin Conexión (Modo Local):** La aplicación debe ser completamente funcional sin necesidad de conexión a internet cuando el motor de IA "Turbo Whisper local" está activado.
    *   *Ejemplo:* Un usuario en un avión sin Wi-Fi debe poder dictar texto sin problemas.

## 5. Casos de Uso principales e Historias clave

### Caso de Uso 1: Dictado de Texto en Tiempo Real en Cualquier Aplicación

*   **Descripción:** El usuario activa Turbo Whisper, comienza a hablar, y el texto se transcribe en tiempo real directamente en la aplicación que esté activa en ese momento (ej. procesador de texto, navegador web, aplicación de mensajería).
*   **Historias Clave:**
    *   **Como** periodista en una entrevista, **quiero** dictar mis notas directamente en mi procesador de texto, **para** no perder el ritmo y tener mis transcripciones listas al instante.
    *   **Como** persona con una lesión en la muñeca, **quiero** poder dictar mis mensajes de WhatsApp sin necesidad de teclear, **para** comunicarme de forma cómoda y sin dolor.
    *   **Como** desarrollador, **quiero** dictar comentarios en mi código o mensajes de commit, **para** mantener mis manos en el teclado principal y acelerar mi flujo de trabajo.

### Caso de Uso 2: Gestión y Utilización de Atajos de Teclado Personalizados

*   **Descripción:** El usuario define frases o comandos específicos que, al ser dictados, se expanden automáticamente a un texto más largo, ejecutan una acción o insertan contenido predefinido.
*   **Historias Clave:**
    *   **Como** comercial, **quiero** crear un atajo de voz para insertar mi plantilla de correo electrónico de seguimiento, **para** ahorrar tiempo en correos repetitivos.
    *   **Como** estudiante, **quiero** configurar un atajo para escribir "bibliografía" y que se expanda a un formato de cita común, **para** asegurarme de que mis referencias son consistentes.
    *   **Como** usuario frecuente, **quiero** un atajo para insertar la fecha y hora actuales, **para** documentar de manera eficiente mis notas.

### Caso de Uso 3: Revisión y Gestión del Historial de Transcripciones

*   **Descripción:** El usuario puede acceder a una lista de todas sus transcripciones pasadas, ver los detalles, copiarlas, editarlas o eliminarlas.
*   **Historias Clave:**
    *   **Como** investigador, **quiero** poder revisar las transcripciones de mis sesiones de lluvia de ideas de la semana pasada, **para** recuperar ideas que pueda haber olvidado.
    *   **Como** usuario preocupado por la privacidad, **quiero** eliminar transcripciones específicas que contengan información sensible de mi historial, **para** mantener mis datos seguros.
    *   **Como** editor de contenido, **quiero** copiar rápidamente una sección de una transcripción anterior para reutilizarla en un nuevo documento, **para** maximizar la eficiencia.

### Caso de Uso 4: Selección y Configuración del Proveedor de IA para Transcripción

*   **Descripción:** El usuario puede elegir entre el motor de transcripción local (Turbo Whisper) o configurar y utilizar un proveedor de IA externo (ej. Gemini API), gestionando las credenciales si son necesarias.
*   **Historias Clave:**
    *   **Como** usuario con estrictos requisitos de privacidad, **quiero** seleccionar "Turbo Whisper local" **para** asegurarme de que mi voz nunca sale de mi dispositivo.
    *   **Como** usuario que busca la máxima precisión en idiomas complejos, **quiero** configurar y usar la API de Gemini, **para** obtener los mejores resultados de transcripción posibles.
    *   **Como** usuario con acceso a internet limitado, **quiero** poder cambiar a la opción local cuando estoy offline, **para** seguir usando la aplicación sin interrupciones.