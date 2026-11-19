(function () {
  'use strict';

  let usuarioActivo = null;
  let esControl = false;
  let misSolicitudes = [];
  let usuarios = [];

  const ROLES = ['Estudiante', 'Docente', 'Control de Estudio'];

  async function api(ruta, opciones = {}) {
    let respuesta;
    try {
      respuesta = await fetch(ruta, {
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        ...opciones,
      });
    } catch (error) {
      throw new Error('No se pudo conectar con el servidor. Abre el sistema desde http://127.0.0.1:5000.');
    }
    let datos = {};
    try {
      datos = await respuesta.json();
    } catch (error) {
      datos = {};
    }
    if (!respuesta.ok) {
      throw new Error(datos.error || 'Ocurrió un error inesperado.');
    }
    return datos;
  }

  function esControlUser(user) {
    return !!user && (user.role === 'Control de Estudio' || user.username === 'admin');
  }

  function escaparHTML(texto) {
    const div = document.createElement('div');
    div.innerText = texto == null ? '' : String(texto);
    return div.innerHTML;
  }

  function formatearFecha(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso || '';
    return d.toLocaleDateString('es-VE') + ' ' +
      d.toLocaleTimeString('es-VE', { hour: '2-digit', minute: '2-digit' });
  }

  function mostrarAviso(elemento, texto, tipo) {
    elemento.innerText = texto;
    elemento.style.display = 'block';
    elemento.style.background = tipo === 'ok' ? '#d4edda' : '#f8d7da';
    elemento.style.color = tipo === 'ok' ? '#155724' : '#721c24';
  }

  function textoEstado(estado) {
    if (estado === 'aprobada') return 'Aprobada';
    if (estado === 'rechazada') return 'Rechazada';
    return 'Pendiente';
  }

  async function cargarMisSolicitudes() {
    try {
      misSolicitudes = await api('/api/mis-solicitudes');
      renderMisSolicitudes();
    } catch (error) {
      console.error(error);
    }
  }

  function renderMisSolicitudes() {
    const contenedor = document.getElementById('myRequests');
    if (!misSolicitudes.length) {
      contenedor.innerHTML = '<div class="empty">Todavía no has solicitado ninguna constancia.</div>';
      return;
    }
    contenedor.innerHTML = misSolicitudes.map((s) => {
      const aprobada = s.estado === 'aprobada' && s.constancia;
      return `<div class="request-item ${s.estado}">
        <div class="request-item-top">
          <strong>${escaparHTML(s.tipoNombre)}</strong>
          <span class="badge ${s.estado}">${textoEstado(s.estado)}</span>
        </div>
        <div class="meta">Solicitada: ${formatearFecha(s.creado)}</div>
        ${s.atendidoPor ? `<div class="meta">Atendida por: ${escaparHTML(s.atendidoPor)}</div>` : ''}
        ${s.estado === 'rechazada' && s.mensaje ? `<div class="meta">Motivo: ${escaparHTML(s.mensaje)}</div>` : ''}
        ${aprobada ? `<button type="button" class="primary-btn small" data-ver="${s.id}">Ver constancia</button>` : ''}
      </div>`;
    }).join('');
  }

  function verConstancia(id) {
    const solicitud = misSolicitudes.find((s) => String(s.id) === String(id));
    if (!solicitud || !solicitud.constancia) {
      alert('Esa constancia todavía no está disponible.');
      return;
    }
    document.getElementById('constanciaInfo').innerHTML =
      `<strong>${escaparHTML(solicitud.tipoNombre)}</strong><br>Solicitada el ${formatearFecha(solicitud.creado)}`;
    document.getElementById('constanciaSheet').innerHTML = `
      <div class="doc-header-text">
        República Bolivariana de Venezuela<br>
        Ministerio del Poder Popular para la Educación<br>
        Unidad Educativa Nacional "Pedro Felipe Ledezma"<br>
        Código de Dependencia: OD16670104<br>
        Circuito La Yaguara - Parroquia Antímano
      </div>
      <h2 class="doc-title">${escaparHTML(solicitud.constancia.titulo || solicitud.tipoNombre)}</h2>
      <div class="doc-body">${solicitud.constancia.html || ''}</div>
      <div class="doc-signature">
        <br><br>
        <strong>Profesora Glenda Josefina Hurtado</strong><br>
        C.I. N° V-6.220.989<br>
        Directora
      </div>`;
    document.getElementById('constanciaModal').classList.add('open');
  }

  function cerrarConstancia() {
    document.getElementById('constanciaModal').classList.remove('open');
  }

  document.getElementById('myRequests').addEventListener('click', (e) => {
    const boton = e.target.closest('button[data-ver]');
    if (boton) verConstancia(boton.dataset.ver);
  });
  document.getElementById('closeConstanciaModal').addEventListener('click', cerrarConstancia);
  document.getElementById('constanciaModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('constanciaModal')) cerrarConstancia();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') cerrarConstancia();
  });

  document.getElementById('requestBtn').addEventListener('click', async () => {
    const identificador = document.getElementById('requestIdentifier').value.trim();
    const tipo = document.getElementById('requestType').value;
    const aviso = document.getElementById('requestNotice');

    if (!identificador) {
      mostrarAviso(aviso, 'Escribe tu usuario, nombre completo o cédula.', 'error');
      return;
    }

    try {
      const resultado = await api('/api/solicitudes', {
        method: 'POST',
        body: JSON.stringify({ identificador: identificador, tipo: tipo }),
      });
      mostrarAviso(aviso, resultado.mensaje || 'Solicitud enviada a Control de Estudio.', 'ok');
      await cargarMisSolicitudes();
    } catch (error) {
      mostrarAviso(aviso, error.message, 'error');
    }
  });

  async function cargarUsuarios() {
    try {
      usuarios = await api('/api/usuarios');
      renderUsuarios();
    } catch (error) {
      mostrarAviso(document.getElementById('adminNotice'), error.message, 'error');
    }
  }

  function renderUsuarios() {
    const cuerpo = document.getElementById('usersBody');
    if (!usuarios.length) {
      cuerpo.innerHTML = '<tr><td colspan="6" class="empty">No hay usuarios registrados.</td></tr>';
      return;
    }
    cuerpo.innerHTML = usuarios.map((u) => {
      const esAdmin = u.username === 'admin';
      const opciones = ROLES.map((rol) =>
        `<option value="${rol}" ${u.role === rol ? 'selected' : ''}>${rol}</option>`
      ).join('');
      return `<tr>
        <td><strong>${escaparHTML(u.fullName)}</strong><br><small>@${escaparHTML(u.username)}</small></td>
        <td>${escaparHTML(u.email || '—')}</td>
        <td>${escaparHTML(u.phone || '—')}</td>
        <td>${escaparHTML(u.cedula || '—')}</td>
        <td><select data-role-for="${u.id}" ${esAdmin ? 'disabled' : ''}>${opciones}</select></td>
        <td><button type="button" class="ghost-btn" data-save-role="${u.id}" ${esAdmin ? 'disabled' : ''}>Guardar rol</button></td>
      </tr>`;
    }).join('');
  }

  document.getElementById('createUserBtn').addEventListener('click', async () => {
    const aviso = document.getElementById('adminNotice');
    const datos = {
      fullName: document.getElementById('newFullName').value.trim(),
      username: document.getElementById('newUsername').value.trim().toLowerCase(),
      email: document.getElementById('newEmail').value.trim(),
      phone: document.getElementById('newPhone').value.trim(),
      cedula: document.getElementById('newCedula').value.trim(),
      password: document.getElementById('newPassword').value,
      role: document.getElementById('newRole').value,
    };
    if (!datos.fullName || !datos.username || !datos.email || !datos.password) {
      mostrarAviso(aviso, 'Faltan datos por llenar (nombre, usuario, correo y contraseña).', 'error');
      return;
    }
    try {
      await api('/api/usuarios', {
        method: 'POST',
        body: JSON.stringify(datos),
      });
      ['newFullName', 'newUsername', 'newEmail', 'newPhone', 'newCedula', 'newPassword']
        .forEach((id) => { document.getElementById(id).value = ''; });
      mostrarAviso(aviso, 'Usuario creado correctamente.', 'ok');
      await cargarUsuarios();
    } catch (error) {
      mostrarAviso(aviso, error.message, 'error');
    }
  });

  document.getElementById('usersBody').addEventListener('click', async (e) => {
    const boton = e.target.closest('button[data-save-role]');
    if (!boton) return;
    const id = boton.dataset.saveRole;
    const selector = document.querySelector(`select[data-role-for="${id}"]`);
    if (!selector) return;
    try {
      await api(`/api/usuarios/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ role: selector.value }),
      });
      mostrarAviso(document.getElementById('adminNotice'), 'Rol actualizado correctamente.', 'ok');
      await cargarUsuarios();
    } catch (error) {
      mostrarAviso(document.getElementById('adminNotice'), error.message, 'error');
    }
  });

  document.getElementById('refreshMyBtn').addEventListener('click', cargarMisSolicitudes);
  document.getElementById('refreshUsersBtn').addEventListener('click', cargarUsuarios);

  async function iniciar() {
    try {
      const { user } = await api('/api/sesion');
      if (!user) {
        alert('Acceso denegado. Por favor, inicia sesión primero.');
        window.location.href = 'index.html';
        return;
      }
      usuarioActivo = user;
      esControl = esControlUser(user);

      document.getElementById('userName').innerText = user.fullName;
      document.getElementById('userRole').innerText = user.role;
      document.getElementById('requestIdentifier').value = user.username;
      document.getElementById('linkConstancias').style.display = esControl ? 'inline-block' : 'none';
      document.getElementById('adminPanel').style.display = esControl ? 'block' : 'none';

      await cargarMisSolicitudes();
      if (esControl) await cargarUsuarios();
      setInterval(cargarMisSolicitudes, 10000);
    } catch (error) {
      alert(error.message);
      window.location.href = 'index.html';
    }
  }

  document.getElementById('logoutBtn').addEventListener('click', async () => {
    try {
      await api('/api/logout', { method: 'POST' });
    } catch (error) {
      // La redirección se hace igualmente.
    }
    localStorage.removeItem('activeUser');
    window.location.href = 'index.html';
  });

  iniciar();

  // FIN_USUARIOS_1

})();
