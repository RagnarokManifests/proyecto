(function () {
  'use strict';

  let activeUser = null;
  let historial = [];
  let solicitudes = [];
  let ultimoPendientes = -1;

  const certType = document.getElementById('certType');
  const studentNameInput = document.getElementById('studentName');
  const studentIdInput = document.getElementById('studentId');
  const studentGrade = document.getElementById('studentGrade');
  const studentSection = document.getElementById('studentSection');
  const eduLevelInput = document.getElementById('eduLevel');
  const schoolYear = document.getElementById('schoolYear');

  const docTitle = document.getElementById('docTitle');
  const docBody = document.getElementById('docBody');

  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];

  const TIPOS = {
    estudio: 'Constancia de Estudio',
    inscripcion: 'Constancia de Inscripción',
    aceptacion: 'Constancia de Aceptación de Cupo',
    asistencia: 'Constancia de Asistencia',
    labor_social: 'Constancia de Cumplimiento de Labor Social',
    retiro: 'Constancia de Retiro',
  };

  function nombreTipo(tipo) {
    return TIPOS[tipo] || tipo || 'Constancia';
  }

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

  function esControl(user) {
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

  function getClosingParagraph(finesLegales) {
    const d = new Date();
    const motivo = finesLegales ? 'a los fines legales consiguientes' : 'a petición de la parte interesada';
    return `<p>Constancia que se expide ${motivo}, en la ciudad de Caracas, a los <strong>${d.getDate()}</strong> días del mes de <strong>${meses[d.getMonth()]}</strong> del año <strong>${d.getFullYear()}</strong>.</p>`;
  }

  function updateDocumentPreview() {
    const student = studentNameInput.value.trim() || '[Nombre del Estudiante]';
    const idNum = studentIdInput.value.trim() || '[Cédula/ID]';
    const grade = studentGrade.value;
    const section = studentSection.value;
    const eduLevel = eduLevelInput.value.trim() || '[Educación]';
    const year = schoolYear.value.trim() || '[Año Escolar]';
    const type = certType.value;
    const suscribe = 'Quien suscribe, Profesora Glenda Josefina Hurtado, titular de la Cédula de Identidad N° V-6.220.989, Directora de la Unidad Educativa Nacional "Pedro Felipe Ledezma", por medio de la presente hace constar que';

    if (type === 'estudio') {
      docTitle.innerText = 'Constancia de Estudio';
      docBody.innerHTML = `
        <p>${suscribe} él o la estudiante: <strong>${student}</strong>, titular de la Cédula de Identidad N° <strong>${idNum}</strong>, cursa <strong>${grade} Año</strong> en la Sección <strong>${section}</strong> de Educación <strong>${eduLevel}</strong>, código 31059, en el año escolar: <strong>${year}</strong>, en esta institución.</p>
        ${getClosingParagraph(false)}
      `;
    } else if (type === 'inscripcion') {
      docTitle.innerText = 'Constancia de Inscripción';
      docBody.innerHTML = `
        <p>${suscribe} él o la estudiante: <strong>${student}</strong>, titular de la Cédula de Identidad N° <strong>${idNum}</strong>, fue inscrito(a) en el <strong>${grade} Año</strong> en la Sección <strong>${section}</strong> de Educación <strong>${eduLevel}</strong>, código 31059, en el año escolar: <strong>${year}</strong>, en esta institución.</p>
        ${getClosingParagraph(false)}
      `;
    } else if (type === 'aceptacion') {
      docTitle.innerText = 'Constancia de Aceptación de Cupo';
      docBody.innerHTML = `
        <p>Quien suscribe, Profesora Glenda Josefina Hurtado, titular de la Cédula de Identidad N° V-6.220.989, Directora de la Unidad Educativa Nacional "Pedro Felipe Ledezma", por medio de la presente otorga el cupo al (a la) estudiante: <strong>${student}</strong>, titular de la Cédula de Identidad N° <strong>${idNum}</strong>, para cursar <strong>${grade} Año</strong> de Educación <strong>${eduLevel}</strong>, código 31059, en el año escolar: <strong>${year}</strong>, en esta institución.</p>
        ${getClosingParagraph(false)}
      `;
    } else if (type === 'asistencia') {
      docTitle.innerText = 'Constancia de Asistencia';
      docBody.innerHTML = `
        <p>${suscribe} él o la ciudadano(a): <strong>[Nombre del Representante]</strong>, titular de la Cédula de Identidad N° <strong>[Cédula del Representante]</strong>, representante del estudiante: <strong>${student}</strong>, titular de la Cédula de Identidad N° <strong>${idNum}</strong>, cursante del <strong>${grade} Año</strong> Sección <strong>${section}</strong>, asistió el día de hoy <strong>[fecha]</strong> a la institución para atender asuntos relacionados con su representado.</p>
        ${getClosingParagraph(false)}
      `;
    } else if (type === 'labor_social') {
      docTitle.innerText = 'Constancia de Cumplimiento de Labor Social';
      docBody.innerHTML = `
        <p>Hago constar que el (la) estudiante: <strong>${student}</strong>, portador(a) de la Cédula de Identidad N° <strong>${idNum}</strong>, cursante del <strong>5to Año de Educación Media General</strong> sin mención, Sección <strong>${section}</strong>, en el año escolar: <strong>${year}</strong>. Cumplió con el artículo 27 del R.G.L.O.E, en el cual señala: "Además de los requisitos legales establecidos para la obtención del título de bachiller o de técnico medio (en la nueva LOE: Media General y Media Técnica), se deberá exigir a cada alumno su participación en una actividad que beneficie al respectivo plantel o a la comunidad. El Ministerio de Educación, Cultura y Deportes (ahora Ministerio del Poder Popular para la Educación) impartirán las orientaciones necesarias para el cumplimiento de esta disposición." En ese sentido el/la estudiante cumplió con <strong>[horas]</strong> horas de labor social desde el <strong>[fecha inicio]</strong> hasta <strong>[fecha fin]</strong>.</p>
        <p>Actividades realizadas en beneficio de la comunidad o plantel:</p>
        <ul style="margin: -10px 0 20px 45px;">
          <li>Recuperación de paredes</li>
          <li>Ambientación de aulas de clases</li>
          <li>Recuperación de espacios comunes</li>
          <li>Pintura de murales</li>
          <li>Recuperación de sillas y mesas</li>
        </ul>
      `;
    } else if (type === 'retiro') {
      docTitle.innerText = 'Constancia de Retiro';
      docBody.innerHTML = `
        <p>${suscribe} él o la estudiante: <strong>${student}</strong>, titular de la Cédula de Identidad N° <strong>${idNum}</strong>, cursaba <strong>${grade} Año</strong> de Educación <strong>${eduLevel}</strong>, código 31059, en el año escolar: <strong>${year}</strong>; se retira motivado a <strong>[motivo de retiro]</strong> de esta institución.</p>
        ${getClosingParagraph(false)}
      `;
    }
  }

  certType.addEventListener('change', updateDocumentPreview);
  studentNameInput.addEventListener('input', updateDocumentPreview);
  studentIdInput.addEventListener('input', updateDocumentPreview);
  studentGrade.addEventListener('change', updateDocumentPreview);
  studentSection.addEventListener('input', updateDocumentPreview);
  eduLevelInput.addEventListener('input', updateDocumentPreview);
  schoolYear.addEventListener('input', updateDocumentPreview);

  document.getElementById('printBtn').addEventListener('click', async () => {
    const type = certType.value;
    let cancelled = false;

    if (type === 'retiro') {
      const motivo = prompt('Ingrese el motivo de retiro:');
      if (motivo === null) {
        cancelled = true;
      } else {
        docBody.innerHTML = docBody.innerHTML.replace('[motivo de retiro]', motivo.trim() || '[motivo de retiro]');
      }
    } else if (type === 'labor_social') {
      const horas = prompt('Ingrese la cantidad de horas cumplidas:');
      if (horas === null) {
        cancelled = true;
      } else {
        const desde = prompt('Fecha de inicio (Desde):') || '[fecha inicio]';
        const hasta = prompt('Fecha de fin (Hasta):') || '[fecha fin]';
        docBody.innerHTML = docBody.innerHTML
          .replace('[horas]', horas.trim() || '[horas]')
          .replace('[fecha inicio]', desde.trim())
          .replace('[fecha fin]', hasta.trim());
      }
    } else if (type === 'asistencia') {
      const repNom = prompt('Nombre del representante:');
      if (repNom === null) {
        cancelled = true;
      } else {
        const repCed = prompt('Cédula del representante:') || '[Cédula del Representante]';
        const fechaAsist = prompt('Fecha de asistencia (Ej: 24 de Abril de 2026):') || '[fecha]';
        docBody.innerHTML = docBody.innerHTML
          .replace('[Nombre del Representante]', repNom.trim() || '[Nombre del Representante]')
          .replace('[Cédula del Representante]', repCed.trim())
          .replace('[fecha]', fechaAsist.trim());
      }
    }

    if (cancelled) return;

    try {
      await guardarImpresion();
    } catch (error) {
      alert(error.message);
      return;
    }

    setTimeout(() => {
      window.print();
      updateDocumentPreview();
    }, 300);
  });

  async function cargarHistorial() {
    historial = await api('/api/constancias');
    mostrarHistorial();
  }

  async function guardarImpresion() {
    await api('/api/constancias', {
      method: 'POST',
      body: JSON.stringify({
        tipo: certType.value,
        estudiante: studentNameInput.value.trim() || '(sin nombre)',
        cedula: studentIdInput.value.trim() || '(sin cédula)',
        anio: studentGrade.value,
        seccion: studentSection.value.trim(),
        anioEscolar: schoolYear.value.trim(),
        titulo: docTitle.innerText,
        html: docBody.innerHTML,
      }),
    });
    await cargarHistorial();
  }

  function mostrarHistorial() {
    const filtro = document.getElementById('historySearch').value.trim().toLowerCase();
    const filas = historial.filter((r) =>
      !filtro || [r.estudiante, r.cedula, r.tipo, r.tipoNombre, r.impresoPor]
        .join(' ').toLowerCase().includes(filtro)
    );
    const cuerpo = document.getElementById('historyBody');

    if (filas.length === 0) {
      cuerpo.innerHTML = `<tr><td colspan="8" class="history-empty">${historial.length ? 'No hay resultados para esa búsqueda.' : 'Todavía no se ha impreso ninguna constancia.'}</td></tr>`;
    } else {
      cuerpo.innerHTML = filas.map((r) => `
        <tr>
          <td>${formatearFecha(r.fecha)}</td>
          <td>${escaparHTML(nombreTipo(r.tipo))}</td>
          <td>${escaparHTML(r.estudiante)}</td>
          <td>${escaparHTML(r.cedula)}</td>
          <td>${escaparHTML(r.anio)} / ${escaparHTML(r.seccion)}</td>
          <td>${escaparHTML(r.anioEscolar)}</td>
          <td>${escaparHTML(r.impresoPor)}</td>
          <td>${r.html
            ? `<button type="button" class="ver-btn" data-id="${r.id}">Ver</button>`
            : '<button type="button" class="ver-btn" disabled>No disponible</button>'}</td>
        </tr>`).join('');
    }
    document.getElementById('historyCount').innerText = `Total de constancias impresas: ${historial.length}`;
  }

  document.getElementById('historySearch').addEventListener('input', mostrarHistorial);

  const previewModal = document.getElementById('previewModal');

  function verConstancia(id) {
    const r = historial.find((item) => String(item.id) === String(id));
    if (!r || !r.html) return;
    const hoja = document.getElementById('printArea').cloneNode(true);
    hoja.removeAttribute('id');
    const titulo = hoja.querySelector('#docTitle');
    const cuerpo = hoja.querySelector('#docBody');
    titulo.removeAttribute('id');
    cuerpo.removeAttribute('id');
    titulo.innerText = r.titulo || nombreTipo(r.tipo);
    cuerpo.innerHTML = r.html;
    const contenedor = document.getElementById('previewModalSheet');
    contenedor.innerHTML = '';
    contenedor.appendChild(hoja);
    document.getElementById('previewModalInfo').innerHTML =
      `<strong>${escaparHTML(nombreTipo(r.tipo))}</strong> &middot; ${escaparHTML(r.estudiante)}<br>Impresa el ${formatearFecha(r.fecha)} por ${escaparHTML(r.impresoPor)}`;
    previewModal.classList.add('open');
  }

  function cerrarVista() {
    previewModal.classList.remove('open');
  }

  document.getElementById('historyBody').addEventListener('click', (e) => {
    const boton = e.target.closest('.ver-btn');
    if (boton && !boton.disabled) verConstancia(boton.dataset.id);
  });
  document.getElementById('closePreviewModal').addEventListener('click', cerrarVista);
  previewModal.addEventListener('click', (e) => {
    if (e.target === previewModal) cerrarVista();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      cerrarVista();
      cerrarModalSolicitudes();
    }
  });

  document.getElementById('exportHistoryBtn').addEventListener('click', () => {
    if (historial.length === 0) {
      alert('No hay constancias registradas todavía.');
      return;
    }
    const celda = (v) => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const lineas = [['Fecha y hora', 'Tipo de constancia', 'Estudiante', 'Cédula', 'Año', 'Sección', 'Año escolar', 'Impresa por'].map(celda).join(';')];
    historial.forEach((r) => lineas.push([
      formatearFecha(r.fecha), nombreTipo(r.tipo), r.estudiante, r.cedula,
      r.anio, r.seccion, r.anioEscolar, r.impresoPor,
    ].map(celda).join(';')));
    const archivo = new Blob(['\ufeff' + lineas.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const enlace = document.createElement('a');
    enlace.href = URL.createObjectURL(archivo);
    enlace.download = 'constancias_impresas.csv';
    enlace.click();
    URL.revokeObjectURL(enlace.href);
  });

  function tarjetaSolicitud(s, enModal) {
    const acciones = s.estado === 'pendiente'
      ? `<button type="button" class="accept-btn" data-action="aceptar" data-id="${s.id}">Aceptar</button>
         ${enModal ? '' : `<button type="button" class="reject-btn" data-action="rechazar" data-id="${s.id}">Rechazar</button>`}`
      : `<span class="state-label ${s.estado}">${s.estado === 'aprobada' ? 'Aceptada' : 'Rechazada'}${s.atendidoPor ? ' por ' + escaparHTML(s.atendidoPor) : ''}</span>`;

    return `<div class="request-card ${s.estado}">
      <div class="request-info">
        <strong>${escaparHTML(s.usuarioNombre)}</strong>
        <span class="request-user">@${escaparHTML(s.usuarioUsername)}</span>
        <div class="request-meta">${escaparHTML(s.tipoNombre)}</div>
        <div class="request-meta">C.I. ${escaparHTML(s.usuarioCedula || '—')} · Tel. ${escaparHTML(s.usuarioTelefono || '—')}</div>
        <div class="request-meta">Solicitada el ${formatearFecha(s.creado)}</div>
        ${s.estado === 'rechazada' && s.mensaje ? `<div class="request-meta">Motivo: ${escaparHTML(s.mensaje)}</div>` : ''}
      </div>
      <div class="request-actions">${acciones}</div>
    </div>`;
  }

  function renderSolicitudes() {
    const contenedor = document.getElementById('requestsList');
    if (!solicitudes.length) {
      contenedor.innerHTML = '<div class="history-empty">Todavía no hay solicitudes de constancias.</div>';
      return;
    }
    const pendientes = solicitudes.filter((s) => s.estado === 'pendiente').length;
    contenedor.innerHTML =
      `<div class="request-summary">${pendientes} solicitud(es) pendiente(s) de ${solicitudes.length} en total.</div>` +
      solicitudes.map((s) => tarjetaSolicitud(s, false)).join('');
  }

  async function cargarSolicitudes(auto) {
    try {
      solicitudes = await api('/api/solicitudes');
      renderSolicitudes();

      const pendientes = solicitudes.filter((s) => s.estado === 'pendiente');
      const modalAbierto = document.getElementById('requestModal').classList.contains('open');
      const hayNuevas = pendientes.length > ultimoPendientes;

      if (pendientes.length && (modalAbierto || !auto || hayNuevas)) {
        abrirModalSolicitudes();
      } else if (!pendientes.length) {
        cerrarModalSolicitudes();
      }
      ultimoPendientes = pendientes.length;
    } catch (error) {
      if (!auto) alert(error.message);
    }
  }

  function abrirModalSolicitudes() {
    const pendientes = solicitudes.filter((s) => s.estado === 'pendiente');
    if (!pendientes.length) {
      cerrarModalSolicitudes();
      return;
    }
    document.getElementById('requestModalCount').innerText =
      `${pendientes.length} solicitud(es) esperando aceptación`;
    document.getElementById('requestModalList').innerHTML =
      pendientes.map((s) => tarjetaSolicitud(s, true)).join('');
    document.getElementById('requestModal').classList.add('open');
  }

  function cerrarModalSolicitudes() {
    document.getElementById('requestModal').classList.remove('open');
  }

  async function aceptarSolicitud(id) {
    try {
      await api(`/api/solicitudes/${id}/aceptar`, { method: 'POST' });
      await cargarSolicitudes(true);
    } catch (error) {
      alert(error.message);
    }
  }

  async function rechazarSolicitud(id) {
    const motivo = prompt('Motivo del rechazo (opcional):');
    if (motivo === null) return;
    try {
      await api(`/api/solicitudes/${id}/rechazar`, {
        method: 'POST',
        body: JSON.stringify({ motivo: motivo }),
      });
      await cargarSolicitudes(true);
    } catch (error) {
      alert(error.message);
    }
  }

  async function aceptarTodas() {
    try {
      const resultado = await api('/api/solicitudes/aceptar-todas', { method: 'POST' });
      if (!resultado.aceptadas) {
        alert('No hay solicitudes pendientes.');
      }
      await cargarSolicitudes(true);
    } catch (error) {
      alert(error.message);
    }
  }

  function manejarAccionSolicitud(e) {
    const boton = e.target.closest('button[data-action]');
    if (!boton) return;
    if (boton.dataset.action === 'aceptar') {
      aceptarSolicitud(boton.dataset.id);
    } else if (boton.dataset.action === 'rechazar') {
      rechazarSolicitud(boton.dataset.id);
    }
  }

  document.getElementById('requestsList').addEventListener('click', manejarAccionSolicitud);
  document.getElementById('requestModalList').addEventListener('click', manejarAccionSolicitud);
  document.getElementById('acceptAllBtn').addEventListener('click', aceptarTodas);
  document.getElementById('requestModalAcceptAll').addEventListener('click', aceptarTodas);
  document.getElementById('refreshRequestsBtn').addEventListener('click', () => cargarSolicitudes(false));
  document.getElementById('closeRequestModal').addEventListener('click', cerrarModalSolicitudes);
  document.getElementById('requestModal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('requestModal')) cerrarModalSolicitudes();
  });

  document.getElementById('logoutBtn').addEventListener('click', async () => {
    try {
      await api('/api/logout', { method: 'POST' });
    } catch (error) {
      // La redirección se hace igualmente.
    }
    localStorage.removeItem('activeUser');
    window.location.href = 'index.html';
  });

  async function iniciar() {
    try {
      const { user } = await api('/api/sesion');
      if (!user) {
        alert('Acceso denegado. Por favor, inicia sesión primero.');
        window.location.href = 'index.html';
        return;
      }
      if (!esControl(user)) {
        alert('Acceso denegado. Esta sección es solo para Control de Estudio.');
        window.location.href = 'usuarios.html';
        return;
      }
      activeUser = user;
      document.getElementById('userName').innerText = user.fullName;
      document.getElementById('userRole').innerText = user.role;

      await Promise.all([cargarHistorial(), cargarSolicitudes(false)]);
      setInterval(() => cargarSolicitudes(true), 8000);
    } catch (error) {
      alert(error.message);
      window.location.href = 'index.html';
    }
  }

  updateDocumentPreview();
  iniciar();

  // FIN_CONSTANCIAS_2


})();
