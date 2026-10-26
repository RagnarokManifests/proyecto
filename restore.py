import re
import codecs

with open('constancias.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Extract base64 images
matches = re.findall(r'src="data:image/webp;base64,([^"]+)"', text)
logo_base64 = matches[0] if len(matches) > 0 else ""

html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portal de Constancias — E.B.B. "Pedro Felipe Ledezma"</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400..700&family=Spectral+SC:wght@600&family=Karla:wght@400;500;600;700&display=swap');

    :root {{
      --azul: #0B1F3A;
      --azul-2: #13315c;
      --amarillo: #FFC726;
      --rojo: #C81E3A;
      --crema: #F7F1E3;
      --verde: #1B4332;
      --tinta: #2D2A26;
      --papel-borde: rgba(45,42,38,0.14);
    }}

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Karla', sans-serif; color: var(--tinta); background: var(--crema); min-height: 100vh; display: flex; flex-direction: column; }}
    h1, h2, h3 {{ font-family: 'Fraunces', serif; font-weight: 600; }}

    header {{ background: var(--azul); border-bottom: 3px solid var(--amarillo); position: sticky; top: 0; z-index: 100; }}
    .header-inner {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 28px; max-width: 1200px; margin: 0 auto; width: 100%; }}
    .brand {{ display: flex; align-items: center; gap: 14px; }}
    .logo-chip {{ width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .logo-chip img {{ width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15)); }}
    .brand-text {{ color: var(--crema); }}
    .brand-text .school-name {{ font-family: 'Fraunces', serif; font-size: 1.05rem; font-weight: 600; line-height: 1.15; }}
    .brand-text .school-sub {{ font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--amarillo); margin-top: 2px; }}
    nav {{ display: flex; gap: 20px; align-items: center; }}
    nav a {{ color: var(--crema); font-size: 0.92rem; font-weight: 500; opacity: 0.88; transition: opacity 0.2s, color 0.2s; }}
    nav a:hover {{ opacity: 1; color: var(--amarillo); }}
    .logout-btn {{ background: var(--rojo); color: white; padding: 8px 16px; border-radius: 6px; font-size: 0.88rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s, transform 0.1s; border: none; }}
    .logout-btn:hover {{ background: #a0182e; transform: translateY(-1px); }}

    main {{ flex: 1; max-width: 1200px; margin: 0 auto; padding: 30px 20px 60px; width: 100%; }}
    .welcome-bar {{ background: var(--azul); color: white; padding: 20px 28px; border-radius: 14px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 10px 24px rgba(11, 31, 58, 0.12); }}
    .welcome-bar h2 {{ font-size: 1.4rem; }}
    .welcome-bar h2 span {{ color: var(--amarillo); }}
    .role-badge {{ background: rgba(255, 255, 255, 0.15); border: 1px solid var(--amarillo); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 6px; }}

    .portal-grid {{ display: grid; grid-template-columns: 1fr 1.3fr; gap: 30px; align-items: start; }}
    @media (max-width: 900px) {{ .portal-grid {{ grid-template-columns: 1fr; }} }}

    .form-panel {{ background: white; padding: 30px; border-radius: 16px; border: 1px solid var(--papel-borde); box-shadow: 0 6px 16px rgba(0, 0, 0, 0.04); }}
    .form-panel h3 {{ font-size: 1.3rem; margin-bottom: 10px; color: var(--azul); border-bottom: 2px solid var(--crema); padding-bottom: 12px; }}
    .form-group {{ margin-bottom: 18px; }}
    .form-group label {{ display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; color: var(--tinta); letter-spacing: 0.03em; }}
    .form-group input, .form-group select {{ width: 100%; padding: 11px 14px; border: 1.5px solid var(--papel-borde); border-radius: 8px; font-family: inherit; font-size: 0.95rem; color: var(--tinta); background-color: #faf9f6; transition: border-color 0.2s, background-color 0.2s; }}
    .form-group input:focus, .form-group select:focus {{ outline: none; border-color: var(--azul); background-color: white; }}

    .print-action-btn {{ width: 100%; background: var(--amarillo); color: var(--azul); padding: 14px; border: none; border-radius: 8px; font-size: 1rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; transition: background-color 0.2s, transform 0.1s, box-shadow 0.2s; margin-top: 10px; }}
    .print-action-btn:hover {{ background: #ffdb58; box-shadow: 0 6px 16px rgba(255, 199, 38, 0.3); transform: translateY(-1px); }}

    .preview-container {{ display: flex; flex-direction: column; align-items: center; }}
    .preview-header-label {{ font-size: 0.8rem; font-weight: 600; color: rgba(45, 42, 38, 0.5); margin-bottom: 8px; align-self: flex-start; text-transform: uppercase; letter-spacing: 0.05em; }}
    
    .document-sheet {{ background: white; width: 100%; aspect-ratio: 1 / 1.29; border: 1px solid var(--papel-borde); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08); border-radius: 4px; padding: 60px 50px; display: flex; flex-direction: column; position: relative; overflow: hidden; color: #000; }}
    .doc-header {{ display: flex; align-items: center; gap: 15px; border-bottom: 2px double #000; padding-bottom: 15px; margin-bottom: 30px; }}
    .doc-logo {{ width: 75px; height: 75px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
    .doc-logo img {{ width: 100%; height: 100%; object-fit: contain; }}
    .doc-header-text {{ font-size: 0.72rem; font-weight: 700; line-height: 1.3; text-transform: uppercase; font-family: Arial, sans-serif; }}
    .doc-title {{ text-align: center; font-family: 'Fraunces', serif; font-size: 1.6rem; font-weight: 700; margin-bottom: 40px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #000; display: inline-block; align-self: center; padding-bottom: 4px; }}
    .doc-body {{ font-family: Times, "Times New Roman", serif; font-size: 1.05rem; line-height: 1.8; text-align: justify; flex: 1; margin-bottom: 40px; }}
    .doc-body p {{ text-indent: 30px; margin-bottom: 20px; }}
    .doc-date {{ margin-top: 30px; font-family: Times, "Times New Roman", serif; font-size: 1.05rem; text-align: right; margin-bottom: 50px; }}
    .doc-footer {{ display: flex; justify-content: space-around; margin-top: auto; text-align: center; }}
    .signature-box {{ width: 220px; border-top: 1px solid #000; padding-top: 8px; font-size: 0.85rem; font-family: Arial, sans-serif; line-height: 1.4; }}

    @media print {{
      body {{ background: white; color: black; }}
      header, main > .welcome-bar, .form-panel, .preview-header-label, nav {{ display: none !important; }}
      main {{ padding: 0; margin: 0; max-width: 100%; width: 100%; }}
      .portal-grid {{ grid-template-columns: 1fr; gap: 0; }}
      .document-sheet {{ border: none; box-shadow: none; padding: 0; margin: 0; width: 100%; aspect-ratio: auto; }}
    }}
  </style>
</head>
<body>

<header>
  <div class="header-inner">
    <div class="brand">
      <div class="logo-chip">
        <img src="data:image/webp;base64,{logo_base64}" alt="Logo">
      </div>
      <div class="brand-text">
        <div class="school-name">E.B.B. "Pedro Felipe Ledezma"</div>
        <div class="school-sub">Control de Constancias</div>
      </div>
    </div>
    <nav>
      <a href="pedro-felipe-ledezma.html">Volver al Inicio</a>
      <button class="logout-btn" id="logoutBtn">Cerrar Sesión</button>
    </nav>
  </div>
</header>

<main>
  <div class="welcome-bar">
    <div>
      <h2>Bienvenido/a, <span id="userName">Cargando...</span></h2>
      <p style="font-size: 0.9rem; margin-top: 4px; opacity: 0.9;">Generador oficial de documentos escolares en línea.</p>
    </div>
    <div class="role-badge">
      <span>👤</span> <span id="userRole">Rol</span>
    </div>
  </div>

  <div class="portal-grid">
    <div class="form-panel">
      <h3>Datos de la Constancia</h3>
      
      <div class="form-group" style="margin-top: 15px;">
        <label for="certType">Tipo de Documento</label>
        <select id="certType">
          <option value="estudio">Constancia de Estudio</option>
          <option value="conducta">Constancia de Conducta</option>
          <option value="inscripcion">Constancia de Inscripción</option>
          <option value="aceptacion">Constancia de Aceptación</option>
          <option value="asistencia">Constancia de Asistencia</option>
          <option value="labor_social">Constancia de Labor Social</option>
          <option value="retiro">Constancia de Retiro</option>
        </select>
      </div>

      <div class="form-group">
        <label for="studentName">Nombre Completo del Estudiante</label>
        <input type="text" id="studentName" placeholder="Ej. Pedro Felipe Ledezma">
      </div>

      <div class="form-group">
        <label for="studentId">Cédula de Identidad o Escolar</label>
        <input type="text" id="studentId" placeholder="Ej. V-32.456.789 o Escolar">
      </div>

      <div class="form-group">
        <label for="studentGrade">Año</label>
        <select id="studentGrade">
          <option value="1er">1er Año</option>
          <option value="2do">2do Año</option>
          <option value="3er">3er Año</option>
          <option value="4to">4to Año</option>
          <option value="5to">5to Año</option>
          <option value="6to">6to Año</option>
        </select>
      </div>

      <div class="form-group">
        <label for="studentSection">Sección</label>
        <input type="text" id="studentSection" placeholder="Ej. A, B, U..." value="A">
      </div>

      <div class="form-group">
        <label for="schoolYear">Año Escolar</label>
        <input type="text" id="schoolYear" value="2025-2026">
      </div>

      <button class="print-action-btn" id="printBtn">
        <span>🖨️</span> Imprimir / Guardar PDF
      </button>
    </div>

    <div class="preview-container">
      <div class="preview-header-label">Vista Previa del Documento Oficial</div>
      
      <div class="document-sheet" id="printArea">
        <div class="doc-header">
          <div class="doc-logo">
            <img src="data:image/webp;base64,{logo_base64}" alt="E.B.B. Pedro Felipe Ledezma">
          </div>
          <div class="doc-header-text">
            República Bolivariana de Venezuela<br>
            Ministerio del Poder Popular para la Educación<br>
            Escuela Básica Bolivariana "Pedro Felipe Ledezma"<br>
            Carapita - Antímano, Caracas
          </div>
        </div>

        <div class="doc-title" id="docTitle">Constancia de Estudio</div>

        <div class="doc-body" id="docBody">
          <!-- Will be generated dynamically -->
        </div>

        <div class="doc-date" id="docDate">
          <!-- Generated date -->
        </div>

        <div class="doc-footer">
          <div class="signature-box">
            <br><br><br>
            <strong>Firma del Director(a)</strong><br>
            Sello de la Institución
          </div>
        </div>
      </div>
    </div>
  </div>
</main>

<script>
  // Auth check
  const activeUser = JSON.parse(localStorage.getItem('activeUser'));
  if (!activeUser) {{
    alert('Acceso denegado. Por favor, inicia sesión primero.');
    window.location.href = 'pedro-felipe-ledezma.html';
  }} else {{
    document.getElementById('userName').innerText = activeUser.fullName;
    document.getElementById('userRole').innerText = activeUser.role;
  }}

  // Logout handler
  document.getElementById('logoutBtn').addEventListener('click', () => {{
    localStorage.removeItem('activeUser');
    window.location.href = 'pedro-felipe-ledezma.html';
  }});

  // DOM Elements for dynamic filling
  const certType = document.getElementById('certType');
  const studentNameInput = document.getElementById('studentName');
  const studentIdInput = document.getElementById('studentId');
  const studentGrade = document.getElementById('studentGrade');
  const studentSection = document.getElementById('studentSection');
  const schoolYear = document.getElementById('schoolYear');

  const docTitle = document.getElementById('docTitle');
  const docBody = document.getElementById('docBody');
  const docDate = document.getElementById('docDate');

  // Month names in Spanish
  const meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
  ];

  // Helper to format the current date in legal school format
  function getFormattedDate() {{
    const d = new Date();
    return `Caracas, a los ${{d.getDate()}} días del mes de ${{meses[d.getMonth()]}} de ${{d.getFullYear()}}.`;
  }}

  // Core function to update the preview sheet
  function updateDocumentPreview() {{
    const student = studentNameInput.value.trim() || "[Nombre del Estudiante]";
    const idNum = studentIdInput.value.trim() || "[Cédula/ID]";
    const grade = studentGrade.value;
    const section = studentSection.value;
    const year = schoolYear.value.trim() || "[Año Escolar]";
    const type = certType.value;

    docDate.innerText = getFormattedDate();

    if (type === 'estudio') {{
      docTitle.innerText = "Constancia de Estudio";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, cursa regularmente sus estudios en esta institución en el <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, durante el año escolar <strong>${{year}}</strong>.</p>
        <p>Constancia que se expide a petición de la parte interesada en la ciudad de Caracas.</p>
      `;
    }} else if (type === 'conducta') {{
      docTitle.innerText = "Carta de Conducta";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, cursando el <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong> en el período escolar <strong>${{year}}</strong>, ha observado una conducta <strong>excelente, solidaria y respetuosa</strong>, cumpliendo cabalmente con las normas de convivencia de nuestro plantel escolar.</p>
        <p>Constancia que se expide a petición de la parte interesada en la ciudad de Caracas.</p>
      `;
    }} else if (type === 'inscripcion') {{
      docTitle.innerText = "Constancia de Inscripción";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, se encuentra formalmente <strong>INSCRITO(A)</strong> en esta unidad educativa para cursar el <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong> para el año escolar <strong>${{year}}</strong>.</p>
        <p>Constancia que se expide para los fines legales y efectos consiguientes en la ciudad de Caracas.</p>
      `;
    }} else if (type === 'aceptacion') {{
      docTitle.innerText = "Constancia de Aceptación";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, ha sido <strong>ACEPTADO(A)</strong> en esta institución para cursar el <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, durante el año escolar <strong>${{year}}</strong>.</p>
        <p>Constancia que se expide a petición de la parte interesada en la ciudad de Caracas.</p>
      `;
    }} else if (type === 'asistencia') {{
      docTitle.innerText = "Constancia de Asistencia";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, cursante del <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, durante el año escolar <strong>${{year}}</strong>, asiste regular y puntualmente a las actividades académicas programadas por la institución.</p>
        <p>Constancia que se expide a petición de la parte interesada en la ciudad de Caracas.</p>
      `;
    }} else if (type === 'labor_social') {{
      docTitle.innerText = "Constancia de Labor Social";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, cursante del <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, ha cumplido satisfactoriamente con las horas reglamentarias de <strong>Labor Social</strong> correspondientes al año escolar <strong>${{year}}</strong>, demostrando responsabilidad y compromiso.</p>
        <p>Constancia que se expide a petición de la parte interesada en la ciudad de Caracas.</p>
      `;
    }} else if (type === 'retiro') {{
      docTitle.innerText = "Constancia de Retiro";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, quien cursaba el <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, en el año escolar <strong>${{year}}</strong>, ha sido <strong>RETIRADO(A)</strong> formalmente de esta institución por voluntad de su representante legal.</p>
        <p>Constancia que se expide a los fines legales consiguientes en la ciudad de Caracas.</p>
      `;
    }}
  }}

  // Event Listeners for live update
  certType.addEventListener('change', updateDocumentPreview);
  studentNameInput.addEventListener('input', updateDocumentPreview);
  studentIdInput.addEventListener('input', updateDocumentPreview);
  studentGrade.addEventListener('change', updateDocumentPreview);
  studentSection.addEventListener('input', updateDocumentPreview);
  schoolYear.addEventListener('input', updateDocumentPreview);

  document.getElementById('printBtn').addEventListener('click', () => {{
    const type = certType.value;
    const student = studentNameInput.value.trim() || "[Nombre del Estudiante]";
    const idNum = studentIdInput.value.trim() || "[Cédula/ID]";
    const grade = studentGrade.value;
    const section = studentSection.value;
    const year = schoolYear.value.trim() || "[Año Escolar]";
    
    let shouldUpdate = false;

    if (type === 'retiro') {{
      const motivo = prompt("Ingrese el motivo de retiro:") || "__________________________";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, quien cursaba el <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, en el año escolar <strong>${{year}}</strong>, ha sido <strong>RETIRADO(A)</strong> formalmente de esta institución motivado a: <strong>${{motivo}}</strong>.</p>
        <p>Constancia que se expide a los fines legales consiguientes en la ciudad de Caracas.</p>
      `;
      shouldUpdate = true;
    }} else if (type === 'labor_social') {{
      const horas = prompt("Ingrese la cantidad de horas:") || "___";
      const desde = prompt("Fecha de inicio (Desde):") || "____________";
      const hasta = prompt("Fecha de fin (Hasta):") || "__________";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el (la) estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, cursante del <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, ha cumplido satisfactoriamente con <strong>${{horas}}</strong> horas reglamentarias de <strong>Labor Social</strong> correspondientes al año escolar <strong>${{year}}</strong>, en el período comprendido desde el <strong>${{desde}}</strong> hasta el <strong>${{hasta}}</strong>, demostrando responsabilidad y compromiso.</p>
        <p>Constancia que se expide a petición de la parte interesada en la ciudad de Caracas.</p>
      `;
      shouldUpdate = true;
    }} else if (type === 'asistencia') {{
      const repNom = prompt("Nombre del representante:") || "_______________________";
      const repCed = prompt("Cédula del representante:") || "_________________";
      const fechaAsist = prompt("Fecha de asistencia (Ej: 24 de Abril de 2026):") || "___ de ______ de 202_";
      docBody.innerHTML = `
        <p>Quien suscribe, Director(a) de la <strong>Escuela Básica Bolivariana "Pedro Felipe Ledezma"</strong>, hace constar por medio de la presente que el ciudadano(a) <strong>${{repNom}}</strong>, titular de la Cédula de Identidad N° <strong>${{repCed}}</strong>, representante legal del estudiante <strong>${{student}}</strong>, titular de la Cédula Escolar/Identidad N° <strong>${{idNum}}</strong>, cursante del <strong>${{grade}} Año</strong>, <strong>Sección "${{section}}"</strong>, asistió a nuestra institución educativa el día <strong>${{fechaAsist}}</strong>.</p>
        <p>Constancia que se expide a petición de la parte interesada en la ciudad de Caracas.</p>
      `;
      shouldUpdate = true;
    }}

    if (shouldUpdate) {{
      setTimeout(() => {{
        window.print();
        updateDocumentPreview();
      }}, 300);
    }} else {{
      window.print();
    }}
  }});

  // Initial render
  updateDocumentPreview();
</script>
</body>
</html>
"""

with open('constancias.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("constancias.html rewritten completely.")
