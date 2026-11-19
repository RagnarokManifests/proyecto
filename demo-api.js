(function () {
  'use strict';

  function leerBandera(clave) {
    try {
      return localStorage.getItem(clave);
    } catch (error) {
      return null;
    }
  }

  function guardarBandera(clave, valor) {
    try {
      if (valor === null) localStorage.removeItem(clave);
      else localStorage.setItem(clave, valor);
    } catch (error) {
      // Si el navegador bloquea localStorage, el modo se decide por la URL.
    }
  }

  const parametros = new URLSearchParams(location.search);
  if (parametros.has('demo')) {
    guardarBandera('escuelaDemoModo', '1');
    guardarBandera('escuelaDemoReal', null);
  } else if (parametros.has('real')) {
    guardarBandera('escuelaDemoModo', null);
    guardarBandera('escuelaDemoReal', '1');
  }

  const host = location.hostname;
  const esLocal = !host ||
    host === 'localhost' ||
    host === '127.0.0.1' ||
    host === '::1' ||
    /^192\.168\./.test(host) ||
    /^10\./.test(host) ||
    /^172\.(1[6-9]|2\d|3[01])\./.test(host);

  const forzarReal = leerBandera('escuelaDemoReal') === '1';
  const DEMO = !forzarReal && (
    location.protocol === 'file:' ||
    !esLocal ||
    parametros.has('demo') ||
    leerBandera('escuelaDemoModo') === '1'
  );

  if (!DEMO || window.__demoApiInstalled) return;
  window.__demoApiInstalled = true;

  const STORAGE_KEY = 'escuelaDemoDB_v1';

  const TIPOS = {
    estudio: 'Constancia de Estudio',
    inscripcion: 'Constancia de Inscripción',
    aceptacion: 'Constancia de Aceptación de Cupo',
    asistencia: 'Constancia de Asistencia',
    labor_social: 'Constancia de Cumplimiento de Labor Social',
    retiro: 'Constancia de Retiro',
  };

  const ROLES = ['Estudiante', 'Docente', 'Control de Estudio'];

  function ahora() {
    return new Date().toISOString();
  }

  function siguienteId(lista) {
    return lista.reduce((max, item) => Math.max(max, Number(item.id) || 0), 0) + 1;
  }

  function normalizar(texto) {
    return String(texto || '')
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  function soloDigitos(texto) {
    return String(texto || '').replace(/\D/g, '');
  }

  function normalizarTipo(tipo) {
    const valor = normalizar(tipo);
    for (const clave of Object.keys(TIPOS)) {
      if (valor === normalizar(clave) || valor === normalizar(TIPOS[clave])) {
        return clave;
      }
    }
    return valor;
  }

  function enmascararCorreo(correo) {
    const [nombre, dominio] = String(correo || '').split('@');
    if (!dominio) return nombre || '';
    const visible = nombre.length <= 2
      ? (nombre.slice(0, 1) || '*') + '*'
      : nombre.slice(0, 2) + '*'.repeat(nombre.length - 2);
    return `${visible}@${dominio}`;
  }

  function seed() {
    return {
      usuarios: [
        {
          id: 1, username: 'admin', password: 'Admin123!',
          fullName: 'Administrador', email: 'admin@escuela.edu.ve',
          phone: '', cedula: '', role: 'Docente',
        },
        {
          id: 2, username: 'control', password: 'Control123!',
          fullName: 'Control de Estudio', email: 'control@escuela.edu.ve',
          phone: '0414-0000000', cedula: 'V-00000000', role: 'Control de Estudio',
        },
        {
          id: 3, username: 'maria.perez', password: 'Clave123!',
          fullName: 'María Fernanda Pérez', email: 'maria@example.com',
          phone: '0414-1234567', cedula: 'V-12.345.678', role: 'Estudiante',
        },
      ],
      constancias: [
        {
          id: 1, fecha: ahora(), tipo: 'estudio',
          estudiante: 'María Fernanda Pérez', cedula: 'V-12.345.678',
          anio: '3er', seccion: 'A', anioEscolar: '2025-2026',
          impresoPor: 'Control de Estudio', titulo: 'Constancia de Estudio',
          html: '<p>Quien suscribe, Profesora Glenda Josefina Hurtado, titular de la Cédula de Identidad N° V-6.220.989, Directora de la Unidad Educativa Nacional "Pedro Felipe Ledezma", por medio de la presente hace constar que él o la estudiante: <strong>María Fernanda Pérez</strong>, titular de la Cédula de Identidad N° <strong>V-12.345.678</strong>, cursa <strong>3er Año</strong> en la Sección <strong>A</strong> de Educación <strong>Media General</strong>, código 31059, en el año escolar: <strong>2025-2026</strong>, en esta institución.</p><p>Constancia que se expide a petición de la parte interesada, en la ciudad de Caracas.</p>',
        },
      ],
      solicitudes: [],
      recuperaciones: [],
      sessionUserId: null,
    };
  }

  function leerDB() {
    let db = null;
    try {
      db = JSON.parse(localStorage.getItem(STORAGE_KEY));
    } catch (error) {
      db = null;
    }
    if (!db || !Array.isArray(db.usuarios) || !Array.isArray(db.constancias)) {
      db = seed();
      guardarDB(db);
    }
    if (!Array.isArray(db.solicitudes)) db.solicitudes = [];
    if (!Array.isArray(db.recuperaciones)) db.recuperaciones = [];
    return db;
  }

  function guardarDB(db) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
    } catch (error) {
      // El modo demostración sigue funcionando en memoria mientras la pestaña esté abierta.
    }
  }

  function usuarioPublico(usuario) {
    return {
      id: usuario.id,
      username: usuario.username,
      fullName: usuario.fullName,
      email: usuario.email,
      phone: usuario.phone || '',
      cedula: usuario.cedula || '',
      role: usuario.role,
    };
  }

  function usuarioActual(db) {
    const id = Number(db.sessionUserId);
    return db.usuarios.find((u) => Number(u.id) === id) || null;
  }

  function esControl(usuario) {
    return !!usuario && (usuario.role === 'Control de Estudio' || usuario.username === 'admin');
  }

  function buscarUsuario(db, identificador, incluirEmail) {
    const texto = String(identificador || '').trim();
    if (!texto) return null;

    let encontrado = db.usuarios.find((u) => u.username.toLowerCase() === texto.toLowerCase());
    if (encontrado) return encontrado;

    if (incluirEmail) {
      encontrado = db.usuarios.find((u) => String(u.email || '').toLowerCase() === texto.toLowerCase());
      if (encontrado) return encontrado;
    }

    const objetivo = normalizar(texto);
    const digitos = soloDigitos(texto);

    encontrado = db.usuarios.find((u) => normalizar(u.fullName) === objetivo);
    if (encontrado) return encontrado;

    if (digitos.length >= 5) {
      encontrado = db.usuarios.find((u) => soloDigitos(u.cedula) === digitos);
      if (encontrado) return encontrado;
    }

    return db.usuarios.find((u) => {
      const nombre = normalizar(u.fullName);
      return objetivo && (nombre.includes(objetivo) || objetivo.includes(nombre));
    }) || null;
  }

  function constanciaParaUsuario(db, usuario, tipo) {
    const nombre = normalizar(usuario.fullName);
    const cedula = soloDigitos(usuario.cedula);
    const lista = [...db.constancias].sort((a, b) => Number(b.id) - Number(a.id));

    for (const constancia of lista) {
      if (tipo && normalizarTipo(constancia.tipo) !== tipo) continue;
      if (cedula && soloDigitos(constancia.cedula) === cedula) return constancia;
      const nombreConstancia = normalizar(constancia.estudiante);
      if (nombre && (
        nombre === nombreConstancia ||
        nombre.includes(nombreConstancia) ||
        nombreConstancia.includes(nombre)
      )) {
        return constancia;
      }
    }
    return null;
  }

  function jsonResponse(datos, estado) {
    return new Response(JSON.stringify(datos), {
      status: estado || 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  function error(mensaje, estado) {
    return jsonResponse({ error: mensaje }, estado || 400);
  }

  function agregarUsuario(db, datos, rolForzado) {
    const nombre = String(datos.fullName || '').trim();
    const correo = String(datos.email || '').trim();
    const usuario = String(datos.username || '').trim().toLowerCase();
    const clave = String(datos.password || '');
    const telefono = String(datos.phone || '').trim();
    const cedula = String(datos.cedula || '').trim();
    const rol = rolForzado || String(datos.role || 'Estudiante').trim();

    if (!ROLES.includes(rol)) return { response: error('Rol no válido.') };
    if (!nombre || !correo || !usuario || !clave) {
      return { response: error('Faltan datos por llenar.') };
    }
    if (rol === 'Estudiante' && (!telefono || !cedula)) {
      return { response: error('Para un estudiante, el teléfono y la cédula son obligatorios.') };
    }
    if (!/^[a-zA-Z0-9._-]{3,30}$/.test(usuario)) {
      return { response: error('El usuario debe tener entre 3 y 30 caracteres (letras, números, punto, guion o guion bajo).') };
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(correo)) {
      return { response: error('Escribe un correo válido.') };
    }
    if (telefono && soloDigitos(telefono).length < 7) {
      return { response: error('Escribe un número de teléfono válido.') };
    }
    if (cedula && soloDigitos(cedula).length < 5) {
      return { response: error('Escribe una cédula válida.') };
    }
    if (clave.length < 6) {
      return { response: error('La contraseña debe tener al menos 6 caracteres.') };
    }
    if (!/[^a-zA-Z0-9\s]/.test(clave)) {
      return { response: error('La contraseña debe tener al menos un carácter especial (ejemplo: !@#$%&*).') };
    }
    if (db.usuarios.some((u) => String(u.email || '').toLowerCase() === correo.toLowerCase())) {
      return { response: error('Ese correo ya está registrado.', 409) };
    }
    if (db.usuarios.some((u) => u.username.toLowerCase() === usuario)) {
      return { response: error('Ese usuario ya existe.', 409) };
    }
    if (cedula && db.usuarios.some((u) => u.cedula && soloDigitos(u.cedula) === soloDigitos(cedula))) {
      return { response: error('Ya existe una cuenta con esa cédula.', 409) };
    }

    const nuevo = {
      id: siguienteId(db.usuarios),
      username: usuario,
      password: clave,
      fullName: nombre,
      email: correo,
      phone: telefono,
      cedula: cedula,
      role: rol,
    };
    db.usuarios.push(nuevo);
    return { usuario: nuevo };
  }

  function mapearSolicitud(db, s) {
    const u = db.usuarios.find((x) => Number(x.id) === Number(s.usuarioId)) || {};
    const c = db.constancias.find((x) => Number(x.id) === Number(s.constanciaId)) || {};
    return {
      id: s.id,
      usuarioId: s.usuarioId,
      usuarioNombre: u.fullName || '',
      usuarioUsername: u.username || '',
      usuarioCorreo: u.email || '',
      usuarioTelefono: u.phone || '',
      usuarioCedula: u.cedula || '',
      usuarioRol: u.role || '',
      tipo: s.tipo,
      tipoNombre: TIPOS[s.tipo] || s.tipo,
      estado: s.estado,
      mensaje: s.mensaje || '',
      creado: s.creado,
      atendidoPor: s.atendidoPor || '',
      atendido: s.atendido || null,
      constanciaTitulo: c.titulo || '',
      constanciaFecha: c.fecha || '',
    };
  }

  async function manejar(ruta, init) {
    const metodo = String(init.method || 'GET').toUpperCase();
    let cuerpo = {};
    if (init.body) {
      try {
        cuerpo = typeof init.body === 'string' ? JSON.parse(init.body) : {};
      } catch (e) {
        cuerpo = {};
      }
    }

    const db = leerDB();
    const usuario = usuarioActual(db);
    const r = ruta.split('?')[0];

    if (r === '/api/sesion' && metodo === 'GET') {
      return jsonResponse({ user: usuario ? usuarioPublico(usuario) : null });
    }

    if (r === '/api/registro' && metodo === 'POST') {
      const resultado = agregarUsuario(db, cuerpo, 'Estudiante');
      if (resultado.response) return resultado.response;
      guardarDB(db);
      return jsonResponse({ ok: true });
    }

    if (r === '/api/login' && metodo === 'POST') {
      const nombreUsuario = String(cuerpo.username || '').trim().toLowerCase();
      const clave = String(cuerpo.password || '');
      const encontrado = db.usuarios.find(
        (u) => u.username.toLowerCase() === nombreUsuario && u.password === clave
      );
      if (!encontrado) return error('Usuario o contraseña incorrectos.', 401);
      db.sessionUserId = encontrado.id;
      guardarDB(db);
      return jsonResponse({ user: usuarioPublico(encontrado) });
    }

    if (r === '/api/logout' && metodo === 'POST') {
      db.sessionUserId = null;
      guardarDB(db);
      return jsonResponse({ ok: true });
    }

    if (r === '/api/recuperar' && metodo === 'POST') {
      const identificador = String(
        cuerpo.identifier || cuerpo.email || cuerpo.username || ''
      ).trim();
      if (!identificador) return error('Escribe tu usuario, correo o cédula.');
      const encontrado = buscarUsuario(db, identificador, true);
      if (!encontrado) {
        return error('No se encontró ninguna cuenta con ese usuario, nombre, cédula o correo.', 404);
      }
      db.recuperaciones.forEach((r2) => {
        if (Number(r2.usuarioId) === Number(encontrado.id)) r2.usado = true;
      });
      const codigo = String(Math.floor(Math.random() * 1000000)).padStart(6, '0');
      db.recuperaciones.push({
        usuarioId: encontrado.id,
        correo: encontrado.email,
        codigo: codigo,
        expira: Date.now() + 15 * 60 * 1000,
        usado: false,
      });
      guardarDB(db);
      return jsonResponse({
        ok: true,
        email: enmascararCorreo(encontrado.email),
        demoCodigo: codigo,
      });
    }

    if (r === '/api/restablecer' && metodo === 'POST') {
      const identificador = String(
        cuerpo.identifier || cuerpo.email || cuerpo.username || ''
      ).trim();
      const codigo = String(cuerpo.codigo || '').trim();
      const clave = String(cuerpo.password || '');
      if (!identificador || !codigo || !clave) return error('Faltan datos por llenar.');
      if (clave.length < 6) return error('La contraseña debe tener al menos 6 caracteres.');
      if (!/[^a-zA-Z0-9\s]/.test(clave)) {
        return error('La contraseña debe tener al menos un carácter especial (ejemplo: !@#$%&*).');
      }
      const encontrado = buscarUsuario(db, identificador, true);
      if (!encontrado) return error('No se encontró ninguna cuenta con esos datos.', 404);
      const rec = [...db.recuperaciones]
        .reverse()
        .find((r2) => Number(r2.usuarioId) === Number(encontrado.id) && !r2.usado);
      if (!rec || rec.codigo !== codigo) return error('El código es incorrecto.');
      if (rec.expira < Date.now()) return error('El código venció. Solicita uno nuevo.');
      encontrado.password = clave;
      rec.usado = true;
      guardarDB(db);
      return jsonResponse({ ok: true });
    }

    if (r === '/api/usuarios' && metodo === 'GET') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const lista = [...db.usuarios].sort((a, b) =>
        String(a.fullName).localeCompare(String(b.fullName), 'es')
      );
      return jsonResponse(lista.map(usuarioPublico));
    }

    if (r === '/api/usuarios' && metodo === 'POST') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const resultado = agregarUsuario(db, cuerpo);
      if (resultado.response) return resultado.response;
      guardarDB(db);
      return jsonResponse({ ok: true, user: usuarioPublico(resultado.usuario) }, 201);
    }

    const actualizarUsuario = r.match(/^\/api\/usuarios\/(\d+)$/);
    if (actualizarUsuario && metodo === 'PUT') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const fila = db.usuarios.find((u) => Number(u.id) === Number(actualizarUsuario[1]));
      if (!fila) return error('Usuario no encontrado.', 404);
      if (fila.username === 'admin') {
        return error('La cuenta administradora no se puede modificar desde aquí.');
      }
      if ('role' in cuerpo) {
        if (!ROLES.includes(cuerpo.role)) return error('Rol no válido.');
        fila.role = cuerpo.role;
      }
      if ('phone' in cuerpo) fila.phone = String(cuerpo.phone || '').trim();
      if ('cedula' in cuerpo) fila.cedula = String(cuerpo.cedula || '').trim();
      if ('fullName' in cuerpo) {
        const nombre = String(cuerpo.fullName || '').trim();
        if (!nombre) return error('El nombre no puede quedar vacío.');
        fila.fullName = nombre;
      }
      if ('email' in cuerpo) {
        const correo = String(cuerpo.email || '').trim();
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(correo)) return error('Escribe un correo válido.');
        fila.email = correo;
      }
      guardarDB(db);
      return jsonResponse({ ok: true, user: usuarioPublico(fila) });
    }

    if (r === '/api/solicitudes' && metodo === 'POST') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      const identificador = String(
        cuerpo.identificador || cuerpo.identifier || usuario.username
      ).trim();
      const tipo = normalizarTipo(cuerpo.tipo || 'estudio');
      if (!identificador) return error('Escribe tu usuario, nombre completo o cédula.');
      if (!TIPOS[tipo]) return error('Selecciona un tipo de constancia válido.');
      const objetivo = buscarUsuario(db, identificador, true);
      if (!objetivo) {
        return error('No se encontró ningún estudiante con ese usuario, nombre o cédula.', 404);
      }
      if (!esControl(usuario) && Number(objetivo.id) !== Number(usuario.id)) {
        return error('Solo puedes solicitar tu propia constancia.', 403);
      }
      const constancia = constanciaParaUsuario(db, objetivo, tipo);
      if (!constancia) {
        return error(
          `Todavía esa constancia no está disponible. Control de Estudio debe generar primero ` +
          `la ${TIPOS[tipo]} de ${objetivo.fullName}.`,
          404
        );
      }
      const existente = db.solicitudes.find(
        (s) => Number(s.usuarioId) === Number(objetivo.id) &&
          Number(s.constanciaId) === Number(constancia.id) &&
          s.tipo === tipo &&
          s.estado === 'pendiente'
      );
      if (existente) {
        return jsonResponse({
          ok: true,
          id: existente.id,
          mensaje: 'Ya enviaste esta solicitud. Espera la respuesta de Control de Estudio.',
        });
      }
      const nueva = {
        id: siguienteId(db.solicitudes),
        usuarioId: objetivo.id,
        constanciaId: constancia.id,
        tipo: tipo,
        identificador: identificador,
        estado: 'pendiente',
        mensaje: '',
        creado: ahora(),
        atendidoPor: '',
        atendido: null,
      };
      db.solicitudes.push(nueva);
      guardarDB(db);
      return jsonResponse({
        ok: true,
        id: nueva.id,
        mensaje: 'Solicitud enviada a Control de Estudio. Espera la aceptación para ver tu constancia.',
      }, 201);
    }

    if (r === '/api/solicitudes' && metodo === 'GET') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const prioridad = { pendiente: 0 };
      const lista = [...db.solicitudes].sort((a, b) => {
        const pa = prioridad[a.estado] === undefined ? 1 : prioridad[a.estado];
        const pb = prioridad[b.estado] === undefined ? 1 : prioridad[b.estado];
        return pa - pb || Number(b.id) - Number(a.id);
      });
      return jsonResponse(lista.map((s) => mapearSolicitud(db, s)));
    }

    if (r === '/api/solicitudes/aceptar-todas' && metodo === 'POST') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const pendientes = db.solicitudes.filter((s) => s.estado === 'pendiente');
      pendientes.forEach((s) => {
        s.estado = 'aprobada';
        s.atendidoPor = usuario.fullName;
        s.atendido = ahora();
      });
      guardarDB(db);
      return jsonResponse({ ok: true, aceptadas: pendientes.length });
    }

    const aceptar = r.match(/^\/api\/solicitudes\/(\d+)\/aceptar$/);
    if (aceptar && metodo === 'POST') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const fila = db.solicitudes.find((s) => Number(s.id) === Number(aceptar[1]));
      if (!fila) return error('Solicitud no encontrada.', 404);
      if (fila.estado !== 'pendiente') return jsonResponse({ ok: true, estado: fila.estado });
      fila.estado = 'aprobada';
      fila.atendidoPor = usuario.fullName;
      fila.atendido = ahora();
      guardarDB(db);
      return jsonResponse({ ok: true });
    }

    const rechazar = r.match(/^\/api\/solicitudes\/(\d+)\/rechazar$/);
    if (rechazar && metodo === 'POST') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const fila = db.solicitudes.find((s) => Number(s.id) === Number(rechazar[1]));
      if (!fila) return error('Solicitud no encontrada.', 404);
      fila.estado = 'rechazada';
      fila.mensaje = String(cuerpo.motivo || '').trim() || 'Solicitud rechazada por Control de Estudio.';
      fila.atendidoPor = usuario.fullName;
      fila.atendido = ahora();
      guardarDB(db);
      return jsonResponse({ ok: true });
    }

    if (r === '/api/mis-solicitudes' && metodo === 'GET') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      const lista = db.solicitudes
        .filter((s) => Number(s.usuarioId) === Number(usuario.id))
        .sort((a, b) => Number(b.id) - Number(a.id));
      return jsonResponse(lista.map((s) => {
        const c = db.constancias.find((x) => Number(x.id) === Number(s.constanciaId));
        return {
          id: s.id,
          tipo: s.tipo,
          tipoNombre: TIPOS[s.tipo] || s.tipo,
          estado: s.estado,
          mensaje: s.mensaje || '',
          creado: s.creado,
          atendidoPor: s.atendidoPor || '',
          atendido: s.atendido || null,
          constancia: (s.estado === 'aprobada' && c && c.html)
            ? { titulo: c.titulo, html: c.html, fecha: c.fecha, impresoPor: c.impresoPor }
            : null,
        };
      }));
    }

    if (r === '/api/constancias' && metodo === 'GET') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const lista = [...db.constancias].sort((a, b) => Number(b.id) - Number(a.id));
      return jsonResponse(lista.map((c) => ({
        id: c.id,
        fecha: c.fecha,
        tipo: c.tipo,
        tipoNombre: TIPOS[normalizarTipo(c.tipo)] || c.tipo,
        estudiante: c.estudiante,
        cedula: c.cedula,
        anio: c.anio,
        seccion: c.seccion,
        anioEscolar: c.anioEscolar,
        impresoPor: c.impresoPor,
        titulo: c.titulo,
        html: c.html,
      })));
    }

    if (r === '/api/constancias' && metodo === 'POST') {
      if (!usuario) return error('Debes iniciar sesión.', 401);
      if (!esControl(usuario)) return error('Esta sección es solo para Control de Estudio.', 403);
      const tipo = normalizarTipo(cuerpo.tipo || 'estudio');
      if (!TIPOS[tipo]) return error('Tipo de constancia no válido.');
      const nueva = {
        id: siguienteId(db.constancias),
        fecha: ahora(),
        tipo: tipo,
        estudiante: String(cuerpo.estudiante || '(sin nombre)').trim(),
        cedula: String(cuerpo.cedula || '(sin cédula)').trim(),
        anio: String(cuerpo.anio || '').trim(),
        seccion: String(cuerpo.seccion || '').trim(),
        anioEscolar: String(cuerpo.anioEscolar || '').trim(),
        impresoPor: usuario.fullName,
        usuarioId: usuario.id,
        titulo: String(cuerpo.titulo || '').trim(),
        html: String(cuerpo.html || ''),
      };
      db.constancias.push(nueva);
      guardarDB(db);
      return jsonResponse({ ok: true, id: nueva.id }, 201);
    }

    return error('Ruta no encontrada en el modo demostración.', 404);
  }

  const fetchOriginal = window.fetch ? window.fetch.bind(window) : null;
  if (fetchOriginal) {
    window.fetch = function (entrada, init) {
      let url = '';
      if (typeof entrada === 'string') {
        url = entrada;
      } else if (entrada && entrada.url) {
        url = entrada.url;
      } else {
        url = String(entrada);
      }

      let ruta = null;
      try {
        const parsed = new URL(url, location.href);
        const indice = parsed.pathname.lastIndexOf('/api/');
        if (indice !== -1) ruta = parsed.pathname.slice(indice);
      } catch (e) {
        ruta = null;
      }

      if (!ruta) return fetchOriginal(entrada, init);
      return manejar(ruta, init || {}).catch((e) =>
        error('Error en el modo demostración: ' + e.message, 500)
      );
    };
  }

  // FIN_DEMO_1
})();
