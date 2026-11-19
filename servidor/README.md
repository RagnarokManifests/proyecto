# Sistema de constancias - E.B.B. Pedro Felipe Ledezma

## Cómo ejecutar

1. Abre una terminal en la carpeta `servidor`.
2. Instala las dependencias (solo la primera vez):

   ```powershell
   pip install -r requirements.txt
   ```

3. Inicia el servidor:

   ```powershell
   python app.py
   ```

4. Abre en el navegador:

   ```text
   http://127.0.0.1:5000
   ```

> Importante: el sistema debe abrirse desde `http://127.0.0.1:5000` (no haciendo doble clic en los HTML), porque el registro, las constancias y las solicitudes se guardan en la base de datos SQLite.

## Roles

- **Estudiante**: se registra desde la página principal y entra a **Mi Módulo** para solicitar sus constancias y ver las que Control de Estudio haya aceptado.
- **Control de Estudio**: genera/guarda constancias y recibe las solicitudes en una ventana emergente con los botones **Aceptar** y **Aceptar todas**.
- **Docente**: cuenta base. El usuario `admin` tiene acceso total al sistema.
- **Administrador del sistema**: el usuario `admin` puede crear usuarios y cambiar roles desde el panel **Usuarios y roles** del módulo de usuario.

## Flujo de una constancia

1. Control de Estudio llena los datos del estudiante y pulsa **Imprimir o guardar en PDF**. La constancia queda guardada en la base de datos.
2. El estudiante entra a **Mi Módulo** y solicita la constancia indicando su usuario, nombre completo o cédula.
   - Si esa constancia todavía no existe, el sistema muestra el aviso **"Todavía esa constancia no está disponible"**.
3. A Control de Estudio le aparece una ventana emergente con la solicitud. Puede aceptarla una por una o usar **Aceptar todas**.
4. Cuando la acepta, la constancia queda disponible para el estudiante en **Mis solicitudes** con el botón **Ver constancia**.

## Base de datos

La base de datos es `servidor/escuela.db`. Al iniciar el servidor se agregan automáticamente las columnas y tablas nuevas:

- `usuarios`: cédula y teléfono.
- `solicitudes`: solicitudes de constancias y su estado.

## Correos (opcional)

Para recuperación de contraseña y avisos por correo configura las variables de entorno:

```powershell
$env:SMTP_HOST="smtp.tu-correo.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="tu-correo@ejemplo.com"
$env:SMTP_PASSWORD="tu-clave"
$env:SMTP_FROM="tu-correo@ejemplo.com"
python app.py
```

Si no se configuran, el sistema sigue funcionando; solo no enviará correos.

## Clave del administrador

Si la base de datos es nueva, el servidor muestra en la terminal la clave del usuario `admin`. Si ya existe, se conserva la clave que tenías. Puedes definir otra al crear una base nueva con la variable `ADMIN_PASSWORD`.
