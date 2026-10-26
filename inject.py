import re

with open('pedro-felipe-ledezma.html', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'src="data:image/webp;base64,([^"]+)"', text)
logo_base64 = matches[0] if len(matches) > 0 else ""

if not logo_base64:
    print("Could not find logo in pedro-felipe-ledezma.html")
else:
    with open('constancias.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    html = html.replace('src="data:image/webp;base64,"', f'src="data:image/webp;base64,{logo_base64}"')
    
    with open('constancias.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Injected base64 logo into constancias.html")
