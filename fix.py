import os

with open('constancias.html', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'CAcdula': 'Cédula',
    'BAsica': 'Básica',
    'NA': 'N°',
    'AAo': 'Año',
    'aAo': 'año',
    'SecciA3n': 'Sección',
    'instituciA3n': 'institución',
    'dA-a': 'día',
    'perA-odo': 'período',
    'peticiA3n': 'petición',
    'sesiA3n': 'sesión',
    'SesiA3n': 'Sesión',
    'InscripciA3n': 'Inscripción',
    'AceptaciA3n': 'Aceptación',
    '?"': '—'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('constancias.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed encoding in constancias.html")
