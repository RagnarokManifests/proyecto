import os
import re
import secrets
import smtplib
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, g, jsonify, redirect, request, send_from_directory, session,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE = Path(__file__).resolve().parent
WEB = BASE / "web"
if not WEB.exists():
    # En este proyecto los HTML viven en la carpeta principal.
    WEB = BASE.parent

DB_PATH = Path(os.environ.get("DB_PATH", BASE / "escuela.db"))

ROL_CONTROL = "Control de Estudio"
ROL_ESTUDIANTE = "Estudiante"
ROL_DOCENTE = "Docente"
ROLES = (ROL_ESTUDIANTE, ROL_DOCENTE, ROL_CONTROL)

TIPOS_CONSTANCIA = {
    "estudio": "Constancia de Estudio",
    "inscripcion": "Constancia de Inscripción",
    "aceptacion": "Constancia de Aceptación de Cupo",
    "asistencia": "Constancia de Asistencia",
    "labor_social": "Constancia de Cumplimiento de Labor Social",
    "retiro": "Constancia de Retiro",
}

EXTENSIONES_ESTATICAS = {
    ".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".gif",
    ".webp", ".svg", ".ico", ".woff", ".woff2", ".ttf",
}


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


def ahora():
    return datetime.now(timezone.utc).isoformat()


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


def asegurar_columna(conexion, tabla, columna, definicion):
    columnas = {fila[1] for fila in conexion.execute(f"PRAGMA table_info({tabla})")}
    if columna not in columnas:
        conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")


def crear_tablas():
    conexion = sqlite3.connect(DB_PATH)
    conexion.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre        TEXT NOT NULL,
            correo        TEXT NOT NULL,
            telefono      TEXT NOT NULL DEFAULT '',
            cedula        TEXT NOT NULL DEFAULT '',
            rol           TEXT NOT NULL,
            creado        TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS recuperaciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
            correo      TEXT NOT NULL,
            codigo_hash TEXT NOT NULL,
            expira      TEXT NOT NULL,
            usado       INTEGER NOT NULL DEFAULT 0,
            creado      TEXT NOT NULL
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
        CREATE TABLE IF NOT EXISTS solicitudes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id    INTEGER NOT NULL REFERENCES usuarios(id),
            constancia_id INTEGER REFERENCES constancias(id),
            tipo          TEXT NOT NULL,
            identificador TEXT,
            estado        TEXT NOT NULL DEFAULT 'pendiente',
            mensaje       TEXT,
            creado        TEXT NOT NULL,
            atendido_por  TEXT,
            atendido      TEXT,
            leido         INTEGER NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes(estado);
    """)
    # Migración para bases de datos creadas con la versión anterior.
    asegurar_columna(conexion, "usuarios", "telefono", "TEXT NOT NULL DEFAULT ''")
    asegurar_columna(conexion, "usuarios", "cedula", "TEXT NOT NULL DEFAULT ''")

    if not conexion.execute("SELECT 1 FROM usuarios WHERE username = 'admin'").fetchone():
        clave = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(9)
        conexion.execute(
            "INSERT INTO usuarios (username, password_hash, nombre, correo, telefono, cedula, rol, creado)"
            " VALUES (?, ?, ?, ?, '', '', ?, ?)",
            ("admin", generate_password_hash(clave), "Administrador",
             "admin@escuela.edu.ve", ROL_DOCENTE, ahora()),
        )
        print(f"\n  Usuario administrador creado ->  usuario: admin   clave: {clave}\n"
              "  (anótala, no se volverá a mostrar)\n")
    conexion.commit()
    conexion.close()


class ErrorCorreo(Exception):
    pass


def enviar_correo(destino, asunto, cuerpo):
    host = os.environ.get("SMTP_HOST")
    usuario = os.environ.get("SMTP_USER")
    clave = os.environ.get("SMTP_PASSWORD")
    remitente = os.environ.get("SMTP_FROM") or usuario
    if not host or not usuario or not clave:
        raise ErrorCorreo("El envío de correos no está configurado. Contacta al administrador.")
    puerto = int(os.environ.get("SMTP_PORT", "587"))

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destino
    mensaje.set_content(cuerpo)

    try:
        with smtplib.SMTP(host, puerto, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(usuario, clave)
            smtp.send_message(mensaje)
    except Exception:
        raise ErrorCorreo("No se pudo enviar el correo. Revisa la configuración SMTP.")


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().casefold()


def solo_digitos(texto):
    return re.sub(r"\D", "", str(texto or ""))


def normalizar_tipo(tipo):
    valor = normalizar(tipo)
    for clave, nombre in TIPOS_CONSTANCIA.items():
        if valor in (normalizar(clave), normalizar(nombre)):
            return clave
    return valor


def enmascarar_correo(correo):
    nombre, _, dominio = str(correo or "").partition("@")
    if len(nombre) <= 2:
        visible = (nombre[:1] or "*") + "*"
    else:
        visible = nombre[:2] + "*" * (len(nombre) - 2)
    return f"{visible}@{dominio}" if dominio else visible


def usuario_publico(fila):
    return {
        "id": fila["id"],
        "username": fila["username"],
        "fullName": fila["nombre"],
        "email": fila["correo"],
        "phone": fila["telefono"] or "",
        "cedula": fila["cedula"] or "",
        "role": fila["rol"],
    }


def usuario_actual():
    if "uid" not in session:
        return None
    return db().execute("SELECT * FROM usuarios WHERE id = ?", (session["uid"],)).fetchone()


def es_control(usuario):
    return usuario is not None and (
        usuario["rol"] == ROL_CONTROL or usuario["username"] == "admin"
    )


def puede_ver_constancias(usuario):
    return es_control(usuario)


def requiere_sesion(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        usuario = usuario_actual()
        if usuario is None:
            return jsonify(error="Debes iniciar sesión."), 401
        return f(usuario, *args, **kwargs)
    return envoltura


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


def requiere_gestion(f):
    @wraps(f)
    def envoltura(*args, **kwargs):
        usuario = usuario_actual()
        if usuario is None:
            return jsonify(error="Debes iniciar sesión."), 401
        if not es_control(usuario):
            return jsonify(error="Esta sección es solo para Control de Estudio."), 403
        return f(usuario, *args, **kwargs)
    return envoltura


def buscar_usuario_por_identificador(identificador, incluir_email=False):
    texto = str(identificador or "").strip()
    if not texto:
        return None
    fila = db().execute(
        "SELECT * FROM usuarios WHERE lower(username) = ?", (texto.lower(),)
    ).fetchone()
    if fila is not None:
        return fila
    if incluir_email:
        fila = db().execute(
            "SELECT * FROM usuarios WHERE lower(correo) = ?", (texto.lower(),)
        ).fetchone()
        if fila is not None:
            return fila
    objetivo = normalizar(texto)
    digitos = solo_digitos(texto)
    filas = db().execute("SELECT * FROM usuarios").fetchall()
    for usuario in filas:
        if normalizar(usuario["nombre"]) == objetivo:
            return usuario
    if len(digitos) >= 5:
        for usuario in filas:
            if solo_digitos(usuario["cedula"]) == digitos:
                return usuario
    for usuario in filas:
        nombre = normalizar(usuario["nombre"])
        if objetivo and (objetivo in nombre or nombre in objetivo):
            return usuario
    return None


def constancia_para_usuario(usuario, tipo):
    nombre = normalizar(usuario["nombre"])
    cedula = solo_digitos(usuario["cedula"])
    filas = db().execute("SELECT * FROM constancias ORDER BY id DESC").fetchall()
    for fila in filas:
        if tipo and normalizar_tipo(fila["tipo"]) != tipo:
            continue
        if cedula and solo_digitos(fila["cedula"]) == cedula:
            return fila
        nombre_constancia = normalizar(fila["estudiante"])
        if nombre and (
            nombre == nombre_constancia
            or nombre in nombre_constancia
            or nombre_constancia in nombre
        ):
            return fila
    return None


def notificar_aprobacion(usuario_id, tipo, solicitud_id):
    fila = db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if fila is None:
        return
    nombre_tipo = TIPOS_CONSTANCIA.get(tipo, "constancia")
    cuerpo = (
        f"Hola {fila['nombre']},\n\n"
        f"Tu solicitud de {nombre_tipo} fue aceptada por Control de Estudio.\n"
        "Ya puedes entrar al Módulo de Usuario para verla o descargarla.\n\n"
        f"Número de solicitud: {solicitud_id}\n"
    )
    try:
        enviar_correo(fila["correo"], "Tu constancia fue aceptada", cuerpo)
    except ErrorCorreo:
        pass


@app.post("/api/registro")
def registro():
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("fullName", "")).strip()
    correo = str(datos.get("email", "")).strip()
    usuario = str(datos.get("username", "")).strip().lower()
    clave = str(datos.get("password", ""))
    telefono = str(datos.get("phone", "")).strip()
    cedula = str(datos.get("cedula", "")).strip()

    if not nombre or not correo or not usuario or not clave or not telefono or not cedula:
        return jsonify(error="Faltan datos por llenar."), 400
    if not re.match(r"^[a-zA-Z0-9._-]{3,30}$", usuario):
        return jsonify(error="El usuario debe tener entre 3 y 30 caracteres (letras, números, punto, guion o guion bajo)."), 400
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
        return jsonify(error="Escribe un correo válido."), 400
    if len(solo_digitos(telefono)) < 7:
        return jsonify(error="Escribe un número de teléfono válido."), 400
    if len(solo_digitos(cedula)) < 5:
        return jsonify(error="Escribe una cédula válida."), 400
    if len(clave) < 6:
        return jsonify(error="La contraseña debe tener al menos 6 caracteres."), 400
    if not re.search(r"[^a-zA-Z0-9\s]", clave):
        return jsonify(error="La contraseña debe tener al menos un carácter especial (ejemplo: !@#$%&*)."), 400

    if db().execute("SELECT 1 FROM usuarios WHERE lower(correo) = ?", (correo.lower(),)).fetchone():
        return jsonify(error="Ese correo ya está registrado."), 409
    for fila in db().execute("SELECT cedula FROM usuarios WHERE cedula <> ''"):
        if solo_digitos(fila["cedula"]) == solo_digitos(cedula):
            return jsonify(error="Ya existe una cuenta con esa cédula."), 409

    try:
        db().execute(
            "INSERT INTO usuarios (username, password_hash, nombre, correo, telefono, cedula, rol, creado)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (usuario, generate_password_hash(clave), nombre, correo,
             telefono, cedula, ROL_ESTUDIANTE, ahora()),
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


@app.post("/api/recuperar")
def recuperar():
    datos = request.get_json(silent=True) or {}
    identificador = str(
        datos.get("identifier") or datos.get("email") or datos.get("username") or ""
    ).strip()
    if not identificador:
        return jsonify(error="Escribe tu usuario, correo o cédula."), 400

    fila = buscar_usuario_por_identificador(identificador, incluir_email=True)
    if fila is None:
        return jsonify(error="No se encontró ninguna cuenta con ese usuario, nombre, cédula o correo."), 404

    codigo = f"{secrets.randbelow(1000000):06d}"
    expira = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
    db().execute("UPDATE recuperaciones SET usado = 1 WHERE usuario_id = ? AND usado = 0", (fila["id"],))
    db().execute(
        "INSERT INTO recuperaciones (usuario_id, correo, codigo_hash, expira, usado, creado)"
        " VALUES (?, ?, ?, ?, 0, ?)",
        (fila["id"], fila["correo"], generate_password_hash(codigo), expira, ahora()),
    )
    db().commit()

    cuerpo = (
        f"Hola {fila['nombre']},\n\n"
        f"Tu código para restablecer la contraseña es: {codigo}\n\n"
        "El código vence en 15 minutos. Si no solicitaste este cambio, ignora este mensaje."
    )
    try:
        enviar_correo(fila["correo"], "Recuperación de contraseña", cuerpo)
    except ErrorCorreo as e:
        return jsonify(error=str(e)), 503
    return jsonify(ok=True, email=enmascarar_correo(fila["correo"]))


@app.post("/api/restablecer")
def restablecer():
    datos = request.get_json(silent=True) or {}
    identificador = str(
        datos.get("identifier") or datos.get("email") or datos.get("username") or ""
    ).strip()
    codigo = str(datos.get("codigo", "")).strip()
    clave = str(datos.get("password", ""))

    if not identificador or not codigo or not clave:
        return jsonify(error="Faltan datos por llenar."), 400
    if len(clave) < 6:
        return jsonify(error="La contraseña debe tener al menos 6 caracteres."), 400
    if not re.search(r"[^a-zA-Z0-9\s]", clave):
        return jsonify(error="La contraseña debe tener al menos un carácter especial (ejemplo: !@#$%&*)."), 400

    fila = buscar_usuario_por_identificador(identificador, incluir_email=True)
    if fila is None:
        return jsonify(error="No se encontró ninguna cuenta con esos datos."), 404

    rec = db().execute(
        "SELECT * FROM recuperaciones WHERE usuario_id = ? AND usado = 0 ORDER BY id DESC LIMIT 1",
        (fila["id"],),
    ).fetchone()
    if rec is None or not check_password_hash(rec["codigo_hash"], codigo):
        return jsonify(error="El código es incorrecto."), 400
    if datetime.fromisoformat(rec["expira"]) < datetime.now(timezone.utc):
        return jsonify(error="El código venció. Solicita uno nuevo."), 400

    db().execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (generate_password_hash(clave), fila["id"]))
    db().execute("UPDATE recuperaciones SET usado = 1 WHERE id = ?", (rec["id"],))
    db().commit()
    return jsonify(ok=True)


@app.get("/api/usuarios")
@requiere_gestion
def listar_usuarios(_usuario):
    filas = db().execute("SELECT * FROM usuarios ORDER BY nombre").fetchall()
    return jsonify([usuario_publico(f) for f in filas])


@app.post("/api/usuarios")
@requiere_gestion
def crear_usuario(_usuario):
    datos = request.get_json(silent=True) or {}
    nombre = str(datos.get("fullName", "")).strip()
    correo = str(datos.get("email", "")).strip()
    usuario = str(datos.get("username", "")).strip().lower()
    clave = str(datos.get("password", ""))
    telefono = str(datos.get("phone", "")).strip()
    cedula = str(datos.get("cedula", "")).strip()
    rol = str(datos.get("role", ROL_ESTUDIANTE)).strip()
    if rol not in ROLES:
        return jsonify(error="Rol no válido."), 400

    if not nombre or not correo or not usuario or not clave:
        return jsonify(error="Faltan datos por llenar."), 400
    if rol == ROL_ESTUDIANTE and (not telefono or not cedula):
        return jsonify(error="Para un estudiante, el teléfono y la cédula son obligatorios."), 400
    if not re.match(r"^[a-zA-Z0-9._-]{3,30}$", usuario):
        return jsonify(error="El usuario debe tener entre 3 y 30 caracteres (letras, números, punto, guion o guion bajo)."), 400
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
        return jsonify(error="Escribe un correo válido."), 400
    if len(clave) < 6:
        return jsonify(error="La contraseña debe tener al menos 6 caracteres."), 400
    if not re.search(r"[^a-zA-Z0-9\s]", clave):
        return jsonify(error="La contraseña debe tener al menos un carácter especial (ejemplo: !@#$%&*)."), 400

    if db().execute("SELECT 1 FROM usuarios WHERE lower(correo) = ?", (correo.lower(),)).fetchone():
        return jsonify(error="Ese correo ya está registrado."), 409
    if cedula:
        for fila in db().execute("SELECT cedula FROM usuarios WHERE cedula <> ''"):
            if solo_digitos(fila["cedula"]) == solo_digitos(cedula):
                return jsonify(error="Ya existe una cuenta con esa cédula."), 409

    try:
        cursor = db().execute(
            "INSERT INTO usuarios (username, password_hash, nombre, correo, telefono, cedula, rol, creado)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (usuario, generate_password_hash(clave), nombre, correo,
             telefono, cedula, rol, ahora()),
        )
        db().commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Ese usuario ya existe."), 409
    fila = db().execute("SELECT * FROM usuarios WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return jsonify(ok=True, user=usuario_publico(fila)), 201


@app.put("/api/usuarios/<int:usuario_id>")
@requiere_gestion
def actualizar_usuario(_usuario, usuario_id):
    fila = db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if fila is None:
        return jsonify(error="Usuario no encontrado."), 404
    if fila["username"] == "admin":
        return jsonify(error="La cuenta administradora no se puede modificar desde aquí."), 400

    datos = request.get_json(silent=True) or {}
    nuevos = {}
    if "role" in datos:
        if datos["role"] not in ROLES:
            return jsonify(error="Rol no válido."), 400
        nuevos["rol"] = datos["role"]
    if "phone" in datos:
        nuevos["telefono"] = str(datos["phone"]).strip()
    if "cedula" in datos:
        nuevos["cedula"] = str(datos["cedula"]).strip()
    if "fullName" in datos:
        nombre = str(datos["fullName"]).strip()
        if not nombre:
            return jsonify(error="El nombre no puede quedar vacío."), 400
        nuevos["nombre"] = nombre
    if "email" in datos:
        correo = str(datos["email"]).strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
            return jsonify(error="Escribe un correo válido."), 400
        nuevos["correo"] = correo

    if not nuevos:
        return jsonify(ok=True)
    sql = "UPDATE usuarios SET " + ", ".join(f"{campo} = ?" for campo in nuevos) + " WHERE id = ?"
    db().execute(sql, (*nuevos.values(), usuario_id))
    db().commit()
    fila = db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return jsonify(ok=True, user=usuario_publico(fila))


@app.post("/api/solicitudes")
@requiere_sesion
def crear_solicitud(usuario):
    datos = request.get_json(silent=True) or {}
    identificador = str(
        datos.get("identificador") or datos.get("identifier") or usuario["username"]
    ).strip()
    tipo = normalizar_tipo(datos.get("tipo", "estudio"))
    if not identificador:
        return jsonify(error="Escribe tu usuario, nombre completo o cédula."), 400
    if tipo not in TIPOS_CONSTANCIA:
        return jsonify(error="Selecciona un tipo de constancia válido."), 400

    objetivo = buscar_usuario_por_identificador(identificador, incluir_email=True)
    if objetivo is None:
        return jsonify(error="No se encontró ningún estudiante con ese usuario, nombre o cédula."), 404
    if not es_control(usuario) and objetivo["id"] != usuario["id"]:
        return jsonify(error="Solo puedes solicitar tu propia constancia."), 403

    constancia = constancia_para_usuario(objetivo, tipo)
    if constancia is None:
        nombre_tipo = TIPOS_CONSTANCIA.get(tipo, "constancia")
        return jsonify(error=(
            f"Todavía esa constancia no está disponible. Control de Estudio debe generar primero "
            f"la {nombre_tipo} de {objetivo['nombre']}."
        )), 404

    existente = db().execute(
        "SELECT id FROM solicitudes WHERE usuario_id = ? AND constancia_id = ? AND tipo = ? AND estado = 'pendiente'",
        (objetivo["id"], constancia["id"], tipo),
    ).fetchone()
    if existente is not None:
        return jsonify(
            ok=True, id=existente["id"],
            mensaje="Ya enviaste esta solicitud. Espera la respuesta de Control de Estudio.",
        )

    cursor = db().execute(
        "INSERT INTO solicitudes (usuario_id, constancia_id, tipo, identificador, estado, creado)"
        " VALUES (?, ?, ?, ?, 'pendiente', ?)",
        (objetivo["id"], constancia["id"], tipo, identificador, ahora()),
    )
    db().commit()
    return jsonify(
        ok=True, id=cursor.lastrowid,
        mensaje="Solicitud enviada a Control de Estudio. Espera la aceptación para ver tu constancia.",
    ), 201


@app.get("/api/solicitudes")
@requiere_control
def listar_solicitudes(_usuario):
    filas = db().execute("""
        SELECT s.*, u.username AS usuario_username, u.nombre AS usuario_nombre,
               u.correo AS usuario_correo, u.telefono AS usuario_telefono,
               u.cedula AS usuario_cedula, u.rol AS usuario_rol,
               c.titulo AS constancia_titulo, c.html AS constancia_html,
               c.fecha AS constancia_fecha
        FROM solicitudes s
        JOIN usuarios u ON u.id = s.usuario_id
        LEFT JOIN constancias c ON c.id = s.constancia_id
        ORDER BY CASE s.estado WHEN 'pendiente' THEN 0 ELSE 1 END, s.id DESC
    """).fetchall()
    return jsonify([{
        "id": f["id"],
        "usuarioId": f["usuario_id"],
        "usuarioNombre": f["usuario_nombre"],
        "usuarioUsername": f["usuario_username"],
        "usuarioCorreo": f["usuario_correo"],
        "usuarioTelefono": f["usuario_telefono"],
        "usuarioCedula": f["usuario_cedula"],
        "usuarioRol": f["usuario_rol"],
        "tipo": f["tipo"],
        "tipoNombre": TIPOS_CONSTANCIA.get(f["tipo"], f["tipo"]),
        "estado": f["estado"],
        "mensaje": f["mensaje"],
        "creado": f["creado"],
        "atendidoPor": f["atendido_por"],
        "atendido": f["atendido"],
        "constanciaTitulo": f["constancia_titulo"],
        "constanciaFecha": f["constancia_fecha"],
    } for f in filas])


@app.post("/api/solicitudes/<int:solicitud_id>/aceptar")
@requiere_control
def aceptar_solicitud(usuario, solicitud_id):
    fila = db().execute("SELECT * FROM solicitudes WHERE id = ?", (solicitud_id,)).fetchone()
    if fila is None:
        return jsonify(error="Solicitud no encontrada."), 404
    if fila["estado"] != "pendiente":
        return jsonify(ok=True, estado=fila["estado"])
    db().execute(
        "UPDATE solicitudes SET estado = 'aprobada', atendido_por = ?, atendido = ? WHERE id = ?",
        (usuario["nombre"], ahora(), solicitud_id),
    )
    db().commit()
    notificar_aprobacion(fila["usuario_id"], fila["tipo"], solicitud_id)
    return jsonify(ok=True)


@app.post("/api/solicitudes/aceptar-todas")
@requiere_control
def aceptar_todas(usuario):
    pendientes = db().execute(
        "SELECT id, usuario_id, tipo FROM solicitudes WHERE estado = 'pendiente'"
    ).fetchall()
    for fila in pendientes:
        db().execute(
            "UPDATE solicitudes SET estado = 'aprobada', atendido_por = ?, atendido = ? WHERE id = ?",
            (usuario["nombre"], ahora(), fila["id"]),
        )
    db().commit()
    for fila in pendientes:
        notificar_aprobacion(fila["usuario_id"], fila["tipo"], fila["id"])
    return jsonify(ok=True, aceptadas=len(pendientes))


@app.post("/api/solicitudes/<int:solicitud_id>/rechazar")
@requiere_control
def rechazar_solicitud(usuario, solicitud_id):
    fila = db().execute("SELECT * FROM solicitudes WHERE id = ?", (solicitud_id,)).fetchone()
    if fila is None:
        return jsonify(error="Solicitud no encontrada."), 404
    datos = request.get_json(silent=True) or {}
    motivo = str(datos.get("motivo", "")).strip() or "Solicitud rechazada por Control de Estudio."
    db().execute(
        "UPDATE solicitudes SET estado = 'rechazada', mensaje = ?, atendido_por = ?, atendido = ? WHERE id = ?",
        (motivo, usuario["nombre"], ahora(), solicitud_id),
    )
    db().commit()
    return jsonify(ok=True)


@app.get("/api/mis-solicitudes")
@requiere_sesion
def mis_solicitudes(usuario):
    filas = db().execute("""
        SELECT s.*, c.titulo AS constancia_titulo, c.html AS constancia_html,
               c.fecha AS constancia_fecha, c.impreso_por AS constancia_impreso_por
        FROM solicitudes s
        LEFT JOIN constancias c ON c.id = s.constancia_id
        WHERE s.usuario_id = ?
        ORDER BY s.id DESC
    """, (usuario["id"],)).fetchall()
    respuesta = []
    for f in filas:
        constancia = None
        if f["estado"] == "aprobada" and f["constancia_html"]:
            constancia = {
                "titulo": f["constancia_titulo"],
                "html": f["constancia_html"],
                "fecha": f["constancia_fecha"],
                "impresoPor": f["constancia_impreso_por"],
            }
        respuesta.append({
            "id": f["id"],
            "tipo": f["tipo"],
            "tipoNombre": TIPOS_CONSTANCIA.get(f["tipo"], f["tipo"]),
            "estado": f["estado"],
            "mensaje": f["mensaje"],
            "creado": f["creado"],
            "atendidoPor": f["atendido_por"],
            "atendido": f["atendido"],
            "constancia": constancia,
        })
    return jsonify(respuesta)


@app.get("/api/constancias")
@requiere_control
def listar_constancias(_usuario):
    filas = db().execute("SELECT * FROM constancias ORDER BY id DESC").fetchall()
    return jsonify([{
        "id": f["id"],
        "fecha": f["fecha"],
        "tipo": f["tipo"],
        "tipoNombre": TIPOS_CONSTANCIA.get(normalizar_tipo(f["tipo"]), f["tipo"]),
        "estudiante": f["estudiante"],
        "cedula": f["cedula"],
        "anio": f["anio"],
        "seccion": f["seccion"],
        "anioEscolar": f["anio_escolar"],
        "impresoPor": f["impreso_por"],
        "titulo": f["titulo"],
        "html": f["html"],
    } for f in filas])


@app.post("/api/constancias")
@requiere_control
def guardar_constancia(usuario):
    d = request.get_json(silent=True) or {}
    campo = lambda k, defecto="": str(d.get(k) or defecto).strip()
    tipo = normalizar_tipo(campo("tipo", "estudio"))
    if tipo not in TIPOS_CONSTANCIA:
        return jsonify(error="Tipo de constancia no válido."), 400
    cursor = db().execute(
        """INSERT INTO constancias (fecha, tipo, estudiante, cedula, anio, seccion, anio_escolar,
                                    impreso_por, usuario_id, titulo, html)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (ahora(), tipo, campo("estudiante", "(sin nombre)"), campo("cedula", "(sin cédula)"),
         campo("anio"), campo("seccion"), campo("anioEscolar"), usuario["nombre"], usuario["id"],
         campo("titulo"), str(d.get("html") or "")),
    )
    db().commit()
    return jsonify(ok=True, id=cursor.lastrowid), 201


@app.get("/")
def inicio():
    return send_from_directory(WEB, "index.html")


@app.get("/constancias.html")
def pagina_constancias():
    usuario = usuario_actual()
    if usuario is None:
        return redirect("/")
    if not puede_ver_constancias(usuario):
        return redirect("/usuarios.html")
    return send_from_directory(WEB, "constancias.html")


@app.get("/usuarios.html")
def pagina_usuarios():
    if usuario_actual() is None:
        return redirect("/")
    return send_from_directory(WEB, "usuarios.html")


@app.get("/<path:archivo>")
def estaticos(archivo):
    if archivo.startswith("api/"):
        abort(404)
    if Path(archivo).suffix.lower() not in EXTENSIONES_ESTATICAS:
        abort(404)
    return send_from_directory(WEB, archivo)


crear_tablas()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)





