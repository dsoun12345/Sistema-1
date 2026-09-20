import tkinter as tk
from ttkbootstrap.constants import *
import estilos

def crear_menu(padre, al_seleccionar):
    """Crea el menú lateral. 'al_seleccionar' es la función que se llama
    al hacer clic en una opción (la define main.py)."""
    sidebar = tk.Frame(padre, bg=estilos.COLOR_SIDEBAR, width=estilos.ANCHO_SIDEBAR)
    sidebar.grid_propagate(False)

    opciones = ["Dashboard", "Inventario", "Punto de Venta", "Configuración"]
    botones = {}
    activa = {"actual": None}

    def seleccionar(nombre):
        for texto, boton in botones.items():
            boton.configure(bg=estilos.COLOR_SIDEBAR_ACTIVO if texto == nombre
                            else estilos.COLOR_SIDEBAR)
        activa["actual"] = nombre
        al_seleccionar(nombre)  

    def al_entrar(boton, nombre):
        if activa["actual"] != nombre:
            boton.configure(bg=estilos.COLOR_SIDEBAR_HOVER)

    def al_salir(boton, nombre):
        if activa["actual"] != nombre:
            boton.configure(bg=estilos.COLOR_SIDEBAR)

    for opcion in opciones:
        btn = tk.Button(
            sidebar, text=opcion, font=estilos.FUENTE_MENU,
            bg=estilos.COLOR_SIDEBAR, fg=estilos.COLOR_TEXTO_CLARO,
            bd=0, anchor="w", padx=20, pady=12,
            activebackground=estilos.COLOR_SIDEBAR_ACTIVO,
            activeforeground=estilos.COLOR_TEXTO_CLARO,
            cursor="hand2",
            command=lambda o=opcion: seleccionar(o)
        )
        btn.pack(fill=X)
        botones[opcion] = btn
        btn.bind("<Enter>", lambda e, b=btn, o=opcion: al_entrar(b, o))
        btn.bind("<Leave>", lambda e, b=btn, o=opcion: al_salir(b, o))

    seleccionar("Dashboard") 
    return sidebar