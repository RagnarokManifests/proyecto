import os
import re

with open('constancias.html', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    'aA±o': 'amarillo',
    'dA-ay': 'display',
    'baA±ound': 'background',
    'traA±on': 'transition',
    'traA±orm': 'transform',
    'shaA±ow': 'shadow',
    'CAcdA-a': 'Cédula',
    'IdA-ad': 'Identidad',
    'idNA': 'idNum',
    'NA': 'N°',
    'aAo': 'año',
    'AAo': 'Año',
    'SecciA3n': 'Sección',
    'instituciA3n': 'institución',
    'motivaAo': 'motivado',
    'laAocial': 'labor_social',
    'LaAor Social': 'Labor Social',
    'saAoriamente': 'satisfactoriamente',
    'perA-odo': 'período',
    'dA-aAo': 'demostrando',
    'peticiA3n': 'petición',
    'repNA': 'repNom',
    'ciudaAo': 'ciudadano',
    'edA-a': 'educativa',
    'dA-a': 'día',
    'shouldA-ate': 'shouldUpdate',
    'BAsica': 'Básica',
    'LedA-a': 'Ledezma',
    'estudA-ante': 'estudiante',
    'updaAocumentPreview': 'updateDocumentPreview',
    'studentNA': 'studentNameInput',
    'studA-ade': 'studentGrade',
    'condA-a': 'conducta',
    'solidAa': 'solidaria',
    'aAon': 'aceptacion',
    'INA(A)': 'INSCRITO(A)',
    'aAos consiguientes': 'efectos consiguientes',
    'dAante': 'durante',
    'acadAas': 'académicas',
    'CaA±o...': 'Cargando...',
    'GeneraA±or': 'Generador',
    'DaA±os': 'Datos',
    'plaA±older': 'placeholder',
    'aA±o;': 'auto;',
    'CONA°': 'CONTENT',
    'PANA°': 'PANEL',
    'DYNA°': 'DYNAMIC'
}

# Apply some fixes carefully
# First fix the CSS / HTML that was broken by 'aA±o' -> 'amarillo'
for old, new in replacements.items():
    content = content.replace(old, new)

# But wait, 'año' was also replaced by 'amarillo' now!
# 'amarillo escolar' -> 'año escolar'
content = content.replace('amarillo escolar', 'año escolar')
content = content.replace('1er amarillo', '1er Año')
content = content.replace('2do amarillo', '2do Año')
content = content.replace('3er amarillo', '3er Año')
content = content.replace('4to amarillo', '4to Año')
content = content.replace('5to amarillo', '5to Año')
content = content.replace('6to amarillo', '6to Año')
content = content.replace('el amarillo', 'el año')
content = content.replace('al amarillo', 'al año')
content = content.replace('0 aA±o', '0 auto')

# 'â?"' -> '—'
content = content.replace('â?"', '—')
content = content.replace('dYZ"', '👤')
content = content.replace('dY-"ï,?', '🖨️')

# Any other CAcdAa without dash
content = content.replace('CAcdAa', 'Cédula')
content = content.replace('IdAad', 'Identidad')
content = content.replace('estudAante', 'estudiante')
content = content.replace('LedAa', 'Ledezma')

with open('constancias.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Attempted to reverse regex damage in constancias.html")
