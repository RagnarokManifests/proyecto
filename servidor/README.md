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

## Qué guarda la base de datos

- `usuarios`: usuario, nombre, correo, rol y la contraseña cifrada (scrypt).
- `constancias`: historial de constancias impresas, con su contenido.

Para respaldar los datos basta con copiar `escuela.db`.
