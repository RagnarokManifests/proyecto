# Sistema de constancias — U.E.N. "Pedro Felipe Ledezma"

Página web + servidor en Python (Flask) con base de datos SQLite (`escuela.db`).

## Cómo usarlo

```
pip install -r requirements.txt
python app.py
```

Abre http://localhost:5000

La base de datos `escuela.db` ya viene creada, con las tablas vacías y el usuario `admin`.
Si la borras, se vuelve a crear al arrancar y la nueva clave del `admin` se muestra **una sola vez** en la consola
(o defínela tú con la variable `ADMIN_PASSWORD`).

Esta carpeta es independiente de la página publicada en GitHub Pages (los archivos de la raíz del repositorio),
porque GitHub Pages no puede ejecutar Python.

## Recuperar contraseña

En la ventana de inicio de sesión, el enlace "¿Olvidaste tu contraseña?" envía un código de 6 dígitos
al correo con el que se registró el usuario. El código vence a los 15 minutos y sirve una sola vez.

Para que el servidor pueda enviar correos, define estas variables de entorno antes de arrancar:

- `SMTP_HOST` — servidor de correo (ej: `smtp.gmail.com`)
- `SMTP_PORT` — puerto (por defecto `587`, con STARTTLS)
- `SMTP_USER` — usuario/correo emisor
- `SMTP_PASSWORD` — contraseña o clave de aplicación del correo
- `SMTP_FROM` — remitente que verá el destinatario (opcional, por defecto igual a `SMTP_USER`)

Si no están definidas, la pantalla de recuperación avisará de que el envío de correos no está configurado.

## Qué guarda la base de datos

- `usuarios`: usuario, nombre, correo, rol y la contraseña cifrada (scrypt).
- `constancias`: historial de constancias impresas, con su contenido.

Para respaldar los datos basta con copiar `escuela.db`.
