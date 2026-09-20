import ttkbootstrap as ttk
import tkinter as tk
import estilos
from componentes.menu_lateral import crear_menu
from pantallas.dashboard import crear_dashboard
from componentes.barra_titulo import crear_barra

app = ttk.Window(themename=estilos.TEMA)
app.title("Sistema de Inventario")
app.geometry("1100x680")
app.minsize(800, 500)
app.configure(bg=estilos.COLOR_FONDO)
estilos.aplicar_estilos(app)

app.grid_columnconfigure(0, weight=0)
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=0)   # barra: fija
app.grid_rowconfigure(1, weight=1)   # contenido: crece

# Barra de título propia (fila 0, ocupa ancho completo)
barra = crear_barra(app, "Sistema de Inventario")
barra.grid(row=0, column=0, columnspan=2, sticky="ew")

# Contenedor donde se van mostrando las pantallas (fila 1)
contenido = tk.Frame(app, bg=estilos.COLOR_FONDO)
contenido.grid(row=1, column=1, sticky="nsew")
contenido.grid_columnconfigure(0, weight=1)   
contenido.grid_rowconfigure(0, weight=1)    

def _placeholder(padre, texto):
    tk.Label(padre, text="Pantalla: " + texto + "\n(en construcción)",
             font=estilos.FUENTE_TITULO, bg=estilos.COLOR_FONDO,
             fg=estilos.COLOR_TEXTO, justify="center").grid(row=0, column=0)

# ── ROUTER: decide qué pantalla mostrar según el menú ──
def mostrar_pantalla(nombre):
    for w in contenido.winfo_children():   
        w.destroy()
    if nombre == "Dashboard":
        crear_dashboard(contenido)
    else:
        _placeholder(contenido, nombre)   


menu = crear_menu(app, mostrar_pantalla)
menu.grid(row=1, column=0, sticky="ns")

app.mainloop()