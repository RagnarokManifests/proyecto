from browser import document, window

# Mobile nav toggle
nav_toggle = document['navToggle']
nav_menu = document['navMenu']

def toggle_nav(event):
    nav_menu.classList.toggle('open')

nav_toggle.bind('click', toggle_nav)

def close_nav(event):
    nav_menu.classList.remove('open')

for link in nav_menu.select('a'):
    link.bind('click', close_nav)

# Sucursales accordion
suc_btn = document['sucBtn']
suc_panel = document['sucPanel']

def toggle_sucursales(event):
    suc_btn.classList.toggle('open')
    suc_panel.classList.toggle('open')

suc_btn.bind('click', toggle_sucursales)

# Reveal on scroll
reveals = document.select('.reveal')

def on_intersection(entries, observer):
    for entry in entries:
        if entry.isIntersecting:
            entry.target.classList.add('visible')
            observer.unobserve(entry.target)

options = {'threshold': 0.12}
observer = window.IntersectionObserver.new(on_intersection, options)

for el in reveals:
    observer.observe(el)
