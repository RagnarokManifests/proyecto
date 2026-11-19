(function () {
  'use strict';

  const modal = document.getElementById('loginModal');
  const msg = document.getElementById('modalStatusMsg');
  const formLogin = document.getElementById('loginFormContainer');
  const formRegistro = document.getElementById('registerFormContainer');
  const formRecuperar = document.getElementById('recuperarFormContainer');

  const btnLogin = document.getElementById('openLoginModal');
  const linkConstancias = document.getElementById('constanciasLink');
  const linkUserModule = document.getElementById('userModuleLink');
  const cajaSesion = document.getElementById('userSessionContainer');

  let identificadorRecuperacion = '';

  function mostrarMensaje(texto, tipo) {
    msg.innerText = texto;
    msg.style.display = 'block';
    msg.style.background = tipo === 'ok' ? '#d4edda' : '#f8d7da';
    msg.style.color = tipo === 'ok' ? '#155724' : '#721c24';
  }

  function ocultarMensaje() {
    msg.style.display = 'none';
  }

  function mostrar(form) {
    ocultarMensaje();
    formLogin.style.display = 'none';
    formRegistro.style.display = 'none';
    formRecuperar.style.display = 'none';
    form.style.display = 'block';
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

  btnLogin.addEventListener('click', (e) => {
    e.preventDefault();
    mostrar(formLogin);
    modal.classList.add('open');
  });

  document.getElementById('closeLoginModal').addEventListener('click', () => {
    modal.classList.remove('open');
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('open');
  });

  document.getElementById('switchToRegister').addEventListener('click', (e) => {
    e.preventDefault();
    mostrar(formRegistro);
  });

  document.getElementById('switchToLogin').addEventListener('click', (e) => {
    e.preventDefault();
    mostrar(formLogin);
  });

  document.getElementById('togglePwd').addEventListener('click', () => {
    const campo = document.getElementById('loginPwd');
    campo.type = campo.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('toggleRegPwd').addEventListener('click', () => {
    const tipo = document.getElementById('regPwd').type === 'password' ? 'text' : 'password';
    document.getElementById('regPwd').type = tipo;
    document.getElementById('regPwdConfirm').type = tipo;
  });

  document.getElementById('toggleRecPwd').addEventListener('click', () => {
    const tipo = document.getElementById('recPwd').type === 'password' ? 'text' : 'password';
    document.getElementById('recPwd').type = tipo;
    document.getElementById('recPwdConfirm').type = tipo;
  });

  document.getElementById('regSubmitBtn').addEventListener('click', async () => {
    const nombre = document.getElementById('regFullName').value.trim();
    const cedula = document.getElementById('regCedula').value.trim();
    const correo = document.getElementById('regEmail').value.trim();
    const telefono = document.getElementById('regPhone').value.trim();
    const usuario = document.getElementById('regUser').value.trim().toLowerCase();
    const clave = document.getElementById('regPwd').value;
    const clave2 = document.getElementById('regPwdConfirm').value;

    if (!nombre || !cedula || !correo || !telefono || !usuario || !clave || !clave2) {
      mostrarMensaje('Faltan datos por llenar.', 'error');
      return;
    }
    if (clave.length < 6) {
      mostrarMensaje('La contraseña debe tener al menos 6 caracteres.', 'error');
      return;
    }
    if (!/[^a-zA-Z0-9\s]/.test(clave)) {
      mostrarMensaje('La contraseña debe tener al menos un carácter especial (ejemplo: !@#$%&*).', 'error');
      return;
    }
    if (clave !== clave2) {
      mostrarMensaje('Las contraseñas no son iguales.', 'error');
      return;
    }
    if (telefono.replace(/\D/g, '').length < 7) {
      mostrarMensaje('Escribe un número de teléfono válido.', 'error');
      return;
    }
    if (cedula.replace(/\D/g, '').length < 5) {
      mostrarMensaje('Escribe una cédula válida.', 'error');
      return;
    }

    try {
      await api('/api/registro', {
        method: 'POST',
        body: JSON.stringify({
          fullName: nombre,
          cedula: cedula,
          email: correo,
          phone: telefono,
          username: usuario,
          password: clave,
        }),
      });
      ['regFullName', 'regCedula', 'regEmail', 'regPhone', 'regUser', 'regPwd', 'regPwdConfirm']
        .forEach((id) => { document.getElementById(id).value = ''; });
      mostrarMensaje('Cuenta de estudiante creada. Ya puedes iniciar sesión.', 'ok');
      setTimeout(() => mostrar(formLogin), 1600);
    } catch (error) {
      mostrarMensaje(error.message, 'error');
    }
  });

  document.getElementById('loginSubmitBtn').addEventListener('click', async () => {
    const usuario = document.getElementById('loginUser').value.trim().toLowerCase();
    const clave = document.getElementById('loginPwd').value;

    if (!usuario || !clave) {
      mostrarMensaje('Escribe tu usuario y contraseña.', 'error');
      return;
    }

    try {
      const datos = await api('/api/login', {
        method: 'POST',
        body: JSON.stringify({ username: usuario, password: clave }),
      });
      localStorage.setItem('activeUser', JSON.stringify(datos.user));
      document.getElementById('loginUser').value = '';
      document.getElementById('loginPwd').value = '';
      window.location.href = esControl(datos.user) ? 'constancias.html' : 'usuarios.html';
    } catch (error) {
      mostrarMensaje(error.message, 'error');
      const linkRec = document.getElementById('switchToRecuperar');
      if (linkRec) {
        linkRec.style.color = 'var(--rojo)';
        linkRec.style.fontWeight = '700';
      }
    }
  });

  document.getElementById('switchToRecuperar').addEventListener('click', (e) => {
    e.preventDefault();
    mostrar(formRecuperar);
    const usuarioIngresado = document.getElementById('loginUser').value.trim();
    if (usuarioIngresado) {
      document.getElementById('recUserOrEmail').value = usuarioIngresado;
    }
    document.getElementById('recuperarPaso1').style.display = 'block';
    document.getElementById('recuperarPaso2').style.display = 'none';
  });

  document.getElementById('recBuscarBtn').addEventListener('click', async () => {
    const valor = document.getElementById('recUserOrEmail').value.trim();
    if (!valor) {
      mostrarMensaje('Escribe tu usuario, correo o cédula.', 'error');
      return;
    }
    try {
      const datos = await api('/api/recuperar', {
        method: 'POST',
        body: JSON.stringify({ identifier: valor }),
      });
      identificadorRecuperacion = valor;
      document.getElementById('recTargetUser').value = valor;
      document.getElementById('recCorreoTexto').innerText = datos.email || 'tu correo registrado';
      document.getElementById('recuperarPaso1').style.display = 'none';
      document.getElementById('recuperarPaso2').style.display = 'block';
      mostrarMensaje('Se envió un código de recuperación al correo registrado.', 'ok');
    } catch (error) {
      mostrarMensaje(error.message, 'error');
    }
  });

  document.getElementById('recRestablecerBtn').addEventListener('click', async () => {
    const codigo = document.getElementById('recCodigo').value.trim();
    const clave = document.getElementById('recPwd').value;
    const clave2 = document.getElementById('recPwdConfirm').value;

    if (!codigo || !clave || !clave2) {
      mostrarMensaje('Faltan datos por llenar.', 'error');
      return;
    }
    if (clave.length < 6) {
      mostrarMensaje('La contraseña debe tener al menos 6 caracteres.', 'error');
      return;
    }
    if (!/[^a-zA-Z0-9\s]/.test(clave)) {
      mostrarMensaje('La contraseña debe tener al menos un carácter especial (ejemplo: !@#$%&*).', 'error');
      return;
    }
    if (clave !== clave2) {
      mostrarMensaje('Las contraseñas no son iguales.', 'error');
      return;
    }

    try {
      await api('/api/restablecer', {
        method: 'POST',
        body: JSON.stringify({
          identifier: identificadorRecuperacion || document.getElementById('recTargetUser').value,
          codigo: codigo,
          password: clave,
        }),
      });
      ['recCodigo', 'recPwd', 'recPwdConfirm', 'recUserOrEmail'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.value = '';
      });
      mostrarMensaje('Contraseña actualizada con éxito. Ya puedes iniciar sesión.', 'ok');
      setTimeout(() => {
        mostrar(formLogin);
        document.getElementById('loginPwd').value = '';
      }, 1800);
    } catch (error) {
      mostrarMensaje(error.message, 'error');
    }
  });

  document.getElementById('recVolverLogin').addEventListener('click', (e) => {
    e.preventDefault();
    mostrar(formLogin);
  });

  async function revisarSesion() {
    try {
      const { user } = await api('/api/sesion');
      if (user) {
        btnLogin.style.display = 'none';
        cajaSesion.style.display = 'flex';
        document.getElementById('sessionUserName').innerText =
          (user.fullName || user.username).split(' ')[0];
        if (esControl(user)) {
          linkConstancias.style.display = 'inline-block';
          linkUserModule.style.display = 'none';
        } else {
          linkConstancias.style.display = 'none';
          linkUserModule.style.display = 'inline-block';
        }
      } else {
        btnLogin.style.display = 'inline-block';
        linkConstancias.style.display = 'none';
        linkUserModule.style.display = 'none';
        cajaSesion.style.display = 'none';
      }
    } catch (error) {
      btnLogin.style.display = 'inline-block';
      linkConstancias.style.display = 'none';
      linkUserModule.style.display = 'none';
      cajaSesion.style.display = 'none';
    }
  }

  document.getElementById('logoutBtn').addEventListener('click', async (e) => {
    e.preventDefault();
    try {
      await api('/api/logout', { method: 'POST' });
    } catch (error) {
      // La sesión local se limpia igualmente.
    }
    localStorage.removeItem('activeUser');
    revisarSesion();
  });

  revisarSesion();

  // FIN_AUTH_1

})();
