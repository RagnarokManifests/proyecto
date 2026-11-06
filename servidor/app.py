import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, redirect, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

BASE = Path(__file__).resolve().parent
WEB = BASE / "web"
DB_PATH = Path(os.environ.get("DB_PATH", BASE / "escuela.db"))
ROL_CONTROL = "Control de Estudio"


def clave_secreta():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    archivo = BASE / ".secret_key"
    if not archivo.exists():
        archivo.write_text(secrets.token_hex(32))
    return archivo.read_text().strip()


app = Flask(__name__, static_folder=None)
app.secret_key = clave_secreta()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(_):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def crear_tablas():
    conexion = sqlite3.connect(DB_PATH)
    conexion.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre        TEXT NOT NULL,
            correo        TEXT NOT NULL,
            rol           TEXT NOT NULL,
            creado        TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS constancias (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha        TEXT NOT NULL,
            tipo         TEXT NOT NULL,
            estudiante   TEXT NOT NULL,
            cedula       TEXT NOT NULL,
            anio         TEXT,
            seccion      TEXT,
            anio_escolar TEXT,
            impreso_por  TEXT,
            usuario_id   INTEGER REFERENCES usuarios(id),
            titulo       TEXT,
            html         TEXT
        );
    """)
    if not conexion.execute("SELECT 1 FROM usuarios WHERE username = 'admin'").fetchone():
        clave = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(9)
        conexion.execute(
            "INSERT INTO usuarios (username, password_hash, nombre, correo, rol, creado) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", generate_password_hash(clave), "Administrador", "admin@escuela.edu.ve", "Docente", ahora()),
        )
        print(f"\n  Usuario administrador creado ->  usuario: admin   clave: {clave}\n  (anotala, no se volvera a mostrar)\n")
    conexion.commit()
    conexion.close()


def ahora():
    return datetime.now(timezone.utc).isoformat()


def usuario_publico(fila):
    return {"username": fila["username"], "fullName": fila["nombre"], "email": fila["correo"], "role": fila["rol"]}


def usuario_actual():
    if "uid" not in session:
        return None
    return db().execute("SELECT * FROM usuarios WHERE id = ?", (session["uid"],)).fetchone()


def puede_ver_constancias(usuario):
    return usuario is not None and (usuario["rol"] == ROL_CONTROL or usuario["username"] == "admin")


def requiere_control(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        usuario = usuario_actual()
        if usuario is None:
            return jsonify(error="Debes iniciar sesión."), 401
        if not puede_ver_constancias(usuario):
            return jsonify(error="Esta sección es solo para Control de Estudio."), 403
        return f(usuario, *args, **kwargs)
    return envoltura


@app.post("/api/registro")
def registro():
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("fullName", "")).strip()
    correo = str(datos.get("email", "")).strip()
    usuario = str(datos.get("username", "")).strip().lower()
    clave = str(datos.get("password", ""))

    if not nombre or not correo or not usuario or not clave:
        return jsonify(error="Faltan datos por llenar."), 400
    if len(clave) < 6:
        return jsonify(error="La contraseña debe tener al menos 6 caracteres."), 400
    try:
        db().execute(
            "INSERT INTO usuarios (username, password_hash, nombre, correo, rol, creado) VALUES (?, ?, ?, ?, ?, ?)",
            (usuario, generate_password_hash(clave), nombre, correo, ROL_CONTROL, ahora()),
        )
        db().commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Ese usuario ya existe."), 409
    return jsonify(ok=True)


@app.post("/api/login")
def login():
    datos = request.get_json(silent=True) or {}
    usuario = str(datos.get("username", "")).strip().lower()
    clave = str(datos.get("password", ""))
    fila = db().execute("SELECT * FROM usuarios WHERE username = ?", (usuario,)).fetchone()
    if fila is None or not check_password_hash(fila["password_hash"], clave):
        return jsonify(error="Usuario o contraseña incorrectos."), 401
    session.clear()
    session["uid"] = fila["id"]
    return jsonify(user=usuario_publico(fila))


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/sesion")
def sesion():
    fila = usuario_actual()
    return jsonify(user=usuario_publico(fila) if fila else None)


@app.get("/api/constancias")
@requiere_control
def listar_constancias(_usuario):
    filas = db().execute("SELECT * FROM constancias ORDER BY id").fetchall()
    return jsonify([{
        "id": f["id"], "fecha": f["fecha"], "tipo": f["tipo"], "estudiante": f["estudiante"],
        "cedula": f["cedula"], "anio": f["anio"], "seccion": f["seccion"],
        "anioEscolar": f["anio_escolar"], "impresoPor": f["impreso_por"],
        "titulo": f["titulo"], "html": f["html"],
    } for f in filas])


@app.post("/api/constancias")
@requiere_control
def guardar_constancia(usuario):
    d = request.get_json(silent=True) or {}
    campo = lambda k, defecto="": str(d.get(k) or defecto).strip()
    db().execute(
        """INSERT INTO constancias (fecha, tipo, estudiante, cedula, anio, seccion, anio_escolar,
                                    impreso_por, usuario_id, titulo, html)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ahora(), campo("tipo"), campo("estudiante", "(sin nombre)"), campo("cedula", "(sin cédula)"),
         campo("anio"), campo("seccion"), campo("anioEscolar"), usuario["nombre"], usuario["id"],
         campo("titulo"), str(d.get("html") or "")),
    )
    db().commit()
    return jsonify(ok=True), 201


@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/constancias.html")
def pagina_constancias():
    if not puede_ver_constancias(usuario_actual()):
        return redirect("/")
    return send_from_directory(WEB, "constancias.html")


@app.get("/<path:archivo>")
def estaticos(archivo):
    return send_from_directory(WEB, archivo)


crear_tablas()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
