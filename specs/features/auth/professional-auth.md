### Feature: Autenticación y Perfil del Profesional

**Categoría/Carpeta:** `auth`

### 1. Historia de Usuario

*   **Como** Profesional,
*   **Quiero** poder registrarme en el sistema, iniciar sesión de forma segura y gestionar mis datos de perfil y credenciales,
*   **Para** poder acceder a mi panel de control de turnos, mantener mi información actualizada y asegurar mi cuenta.

### 2. Criterios de Aceptación Detallados

#### 2.1. Registro del Profesional

*   **GIVEN** que estoy en la página de registro
*   **WHEN** ingreso un email válido y único, una contraseña segura (con al menos 8 caracteres, incluyendo mayúsculas, minúsculas y un número) y mi nombre completo, y confirmo la contraseña correctamente
*   **THEN** mi cuenta de Profesional debe ser creada exitosamente, se me debe autenticar automáticamente y redirigir al panel de control del profesional (o a una página de bienvenida inicial), y un nuevo registro `User` debe ser persistido en la base de datos con la contraseña hasheada.
*   **GIVEN** que estoy en la página de registro
*   **WHEN** intento registrarme con un email que ya está asociado a otra cuenta en el sistema
*   **THEN** el sistema debe mostrar un mensaje de error claro como "El email ya está registrado. Por favor, inicia sesión o usa otro email."
*   **GIVEN** que estoy en la página de registro
*   **WHEN** ingreso un email con formato inválido (ej. "usuario@.com", "usuario@dominio")
*   **THEN** el sistema debe mostrar un mensaje de error "Por favor, introduce un email válido."
*   **GIVEN** que estoy en la página de registro
*   **WHEN** ingreso una contraseña que no cumple con los requisitos de seguridad (ej. menos de 8 caracteres, sin mayúsculas, etc.)
*   **THEN** el sistema debe mostrar un mensaje de error descriptivo indicando los requisitos incumplidos (ej. "La contraseña debe tener al menos 8 caracteres, incluyendo una mayúscula, una minúscula y un número.").
*   **GIVEN** que estoy en la página de registro
*   **WHEN** la contraseña ingresada y su confirmación no coinciden
*   **THEN** el sistema debe mostrar un mensaje de error "Las contraseñas no coinciden."
*   **GIVEN** que estoy en la página de registro
*   **WHEN** dejo en blanco campos obligatorios como el email, la contraseña o el nombre
*   **THEN** el sistema debe mostrar un mensaje de error "Este campo es obligatorio." para cada campo en blanco.

#### 2.2. Inicio de Sesión del Profesional

*   **GIVEN** que estoy en la página de inicio de sesión
*   **WHEN** ingreso mi email y contraseña correctos
*   **THEN** debo ser autenticado exitosamente, mi sesión debe iniciarse y debo ser redirigido al panel de control del profesional.
*   **GIVEN** que estoy en la página de inicio de sesión
*   **WHEN** ingreso un email o contraseña incorrectos
*   **THEN** el sistema debe mostrar un mensaje de error genérico como "Credenciales inválidas. Por favor, verifica tu email y contraseña." (sin especificar qué campo es incorrecto por razones de seguridad).
*   **GIVEN** que estoy autenticado
*   **WHEN** hago clic en la opción "Cerrar Sesión"
*   **THEN** mi sesión activa debe ser invalidada, y debo ser redirigido a la página de inicio de sesión.
*   **GIVEN** que estoy en la página de inicio de sesión
*   **WHEN** mi cuenta existe pero intento iniciar sesión después de haber olvidado la contraseña
*   **THEN** el sistema debe ofrecer un enlace "Olvidé mi contraseña" que, por ahora, puede redirigir a una página informativa o de "Próximamente", ya que la funcionalidad de recuperación no está cubierta en esta feature.

#### 2.3. Gestión de Perfil del Profesional (Visualización y Actualización)

*   **GIVEN** que he iniciado sesión como Profesional
*   **WHEN** accedo a la sección de "Mi Perfil" o "Configuración de Cuenta"
*   **THEN** debo ver mi nombre completo, mi email (como un campo de solo lectura) y mi número de teléfono de contacto (si ha sido proporcionado).
*   **GIVEN** que estoy en la sección de "Mi Perfil" y deseo actualizar mi información
*   **WHEN** modifico mi nombre completo y/o mi número de teléfono de contacto (opcionalmente lo añado, modifico o elimino) y guardo los cambios
*   **THEN** mi perfil debe ser actualizado exitosamente en la base de datos, y los nuevos datos deben reflejarse en la interfaz, mostrando un mensaje de éxito como "Perfil actualizado correctamente.".
*   **GIVEN** que estoy en la sección de "Mi Perfil"
*   **WHEN** intento actualizar mi nombre o número de teléfono de contacto con valores inválidos (ej. nombre vacío, teléfono con caracteres no numéricos)
*   **THEN** el sistema debe mostrar un mensaje de error de validación específico para cada campo (ej. "El nombre no puede estar vacío.", "Formato de teléfono inválido.").
*   **GIVEN** que estoy en la sección de "Mi Perfil"
*   **WHEN** intento modificar el campo de email
*   **THEN** el sistema *no* debe permitir la edición directa del email desde esta interfaz, mostrándolo como un campo de solo lectura, ya que es el identificador único para la autenticación y su cambio requeriría un proceso de verificación más complejo (fuera del alcance de esta feature).

#### 2.4. Cambio de Contraseña

*   **GIVEN** que he iniciado sesión como Profesional y estoy en la sección de "Cambiar Contraseña"
*   **WHEN** ingreso mi contraseña actual correcta, y luego una nueva contraseña segura (que cumpla con los requisitos definidos en el registro) que coincida con su confirmación
*   **THEN** mi contraseña debe ser actualizada exitosamente en la base de datos (hasheada), y debo recibir una notificación de que el cambio fue exitoso, mostrando un mensaje como "Contraseña cambiada correctamente.".
*   **GIVEN** que he iniciado sesión como Profesional y estoy en la sección de "Cambiar Contraseña"
*   **WHEN** ingreso una contraseña actual incorrecta
*   **THEN** el sistema debe mostrar un mensaje de error "La contraseña actual es incorrecta."
*   **GIVEN** que he iniciado sesión como Profesional y estoy en la sección de "Cambiar Contraseña"
*   **WHEN** la nueva contraseña no cumple con los requisitos de seguridad o no coincide con su confirmación
*   **THEN** el sistema debe mostrar el mensaje de error correspondiente a la validación fallida (similar a los criterios de registro de contraseña).

### 3. Casos de Error y Casos Borde (Edge Cases)

#### 3.1. Errores de Conectividad y Sistema

*   **Pérdida de Conexión:**
    *   **Escenario:** El profesional intenta realizar cualquier acción de autenticación o gestión de perfil (registro, login, actualización) y se pierde la conexión a internet.
    *   **Resultado Esperado:** La interfaz de usuario debe mostrar un mensaje de error claro y amigable indicando la ausencia de conexión a la red y sugerir reintentar la operación cuando la conexión se restablezca. La acción en progreso debe ser cancelada o quedar en un estado pendiente claro.
*   **Error Interno del Servidor (5xx):**
    *   **Escenario:** Durante cualquier operación de esta feature (registro, login, actualización de perfil/contraseña), ocurre un error inesperado en el servidor (ej. fallo de la base de datos, excepción no controlada).
    *   **Resultado Esperado:** El sistema debe mostrar un mensaje de error genérico al profesional ("Ocurrió un error inesperado. Por favor, inténtelo de nuevo más tarde.") y registrar los detalles del error en los logs del servidor para su posterior análisis y depuración, sin exponer información sensible al usuario.
*   **Servicio de Base de Datos No Disponible:**
    *   **Escenario:** La conexión o el servicio de la base de datos se interrumpe durante una operación crítica que requiere lectura o escritura de datos del usuario.
    *   **Resultado Esperado:** Se tratará como un error interno del servidor, mostrando un mensaje de error genérico al usuario y registrando la incidencia.

#### 3.2. Violaciones de Reglas de Negocio y Restricciones de Datos

*   **Email Duplicado al Registrar:**
    *   **Escenario:** El profesional intenta registrarse con un email que ya está en la base de datos.
    *   **Resultado Esperado:** El sistema debe rechazar la operación y mostrar el mensaje de error "El email ya está registrado. Por favor, inicia sesión o usa otro email." (tal como se define en los ACs).
*   **Contraseña Débil o No Coincidente:**
    *   **Escenario:** Durante el registro o cambio de contraseña, la nueva contraseña no cumple con los criterios de seguridad o la confirmación no coincide.
    *   **Resultado Esperado:** El sistema debe impedir la acción y mostrar mensajes de validación específicos que guíen al usuario (tal como se define en los ACs).
*   **Sesión Expirada o Inválida:**
    *   **Escenario:** Un profesional, habiendo iniciado sesión previamente, está inactivo durante un período extendido (o su token de sesión es invalidado/expirado) e intenta acceder a una sección protegida o realizar una acción.
    *   **Resultado Esperado:** El sistema debe detectar la sesión inválida, redirigir al profesional a la página de inicio de sesión y mostrar un mensaje "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.".
*   **Intentos Repetidos de Inicio de Sesión Fallidos:**
    *   **Escenario:** Un atacante (o el propio profesional por error) intenta iniciar sesión repetidamente con credenciales incorrectas.
    *   **Consideración:** Aunque no se especificó un mecanismo de bloqueo en los ACs, se debe implementar una política de limitación de intentos fallidos (ej. bloqueo temporal de la cuenta/IP tras X intentos) para prevenir ataques de fuerza bruta. El sistema debería informar al usuario (cuando sea el caso legítimo) que su cuenta está bloqueada temporalmente.

#### 3.3. Casos Borde de Entrada de Datos

*   **Campos Obligatorios Vacíos:**
    *   **Escenario:** El profesional intenta enviar formularios (registro, login, actualización) con campos obligatorios vacíos.
    *   **Resultado Esperado:** El sistema debe mostrar mensajes de validación en el lado del cliente (frontend) y del servidor (backend) indicando que los campos son obligatorios.
*   **Entrada de Texto con Exceso de Caracteres:**
    *   **Escenario:** El profesional ingresa un nombre o un número de teléfono excesivamente largo que supera los límites definidos en la base de datos para los campos `name` o `contactPhone`.
    *   **Resultado Esperado:** El sistema debe truncar el texto si es una estrategia aceptable, o idealmente, el frontend debe limitar la entrada o el backend debe rechazar la solicitud con un mensaje de error indicando la longitud máxima permitida.
*   **Espacios en Blanco en la Entrada:**
    *   **Escenario:** El profesional ingresa un email, nombre o contraseña con espacios en blanco al principio o al final.
    *   **Resultado Esperado:** El sistema debe recortar (trim) automáticamente los espacios en blanco de los campos de texto relevantes (ej. email, nombre) antes de la validación y el almacenamiento, excepto en las contraseñas donde los espacios pueden ser significativos.

#### 3.4. Otros Casos Borde

*   **No Manejo de "Olvidé mi contraseña":**
    *   **Escenario:** Un profesional olvida su contraseña.
    *   **Consideración:** Como esta funcionalidad no está dentro del alcance de la feature actual, el enlace "Olvidé mi contraseña" en la página de login debe ser manejado de una manera que indique su estado (ej. "Funcionalidad próximamente" o redirigir a una página de soporte genérica si no hay implementación). Es un punto crítico para la experiencia de usuario y seguridad que deberá ser abordado en una feature futura.