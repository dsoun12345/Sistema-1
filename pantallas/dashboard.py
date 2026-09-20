import tkinter as tk
import ttkbootstrap as ttk
import estilos
from componentes.tarjeta import crear_tarjeta

def crear_dashboard(padre):
    """Dibuja el dashboard dentro de 'padre'."""
    marco = tk.Frame(padre, bg=estilos.COLOR_FONDO)
    marco.grid(row=0, column=0, sticky="nsew")
    marco.grid_columnconfigure(0, weight=1)
    marco.grid_rowconfigure(3, weight=1)   # la tabla crece

    # --- Banner ---
    banner = tk.Frame(marco, bg=estilos.CARD_MORADO, height=80)
    banner.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
    banner.grid_propagate(False)
    tk.Label(banner, text="Bienvenido, Administrador",
             font=estilos.FUENTE_TITULO, bg=estilos.CARD_MORADO,
             fg="white").pack(anchor="w", padx=20, pady=20)

    # --- Tarjetas ---
    fila_cards = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    fila_cards.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
    fila_cards.grid_rowconfigure(0, minsize=100)
    for i in range(4):
        fila_cards.grid_columnconfigure(i, weight=1, uniform="cards")

    datos_cards = [
        ("0",     "Productos",       estilos.CARD_MORADO),
        ("$0.00", "Ventas del día",  estilos.CARD_ROSA),
        ("$0.00", "Compras del mes", estilos.CARD_CYAN),
        ("0",     "Clientes",        estilos.CARD_VERDE),
    ]
    for col, (num, titulo, color) in enumerate(datos_cards):
        tarjeta = crear_tarjeta(fila_cards, num, titulo, color)
        tarjeta.grid(row=0, column=col, sticky="nsew", padx=8)

    # --- Título tabla ---
    tk.Label(marco, text="Últimas Ventas", font=estilos.FUENTE_SUBTITULO,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO
             ).grid(row=2, column=0, sticky="w", padx=20, pady=(20, 5))

    # --- Tabla ---
    tabla_frame = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    tabla_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
    tabla_frame.grid_columnconfigure(0, weight=1)
    tabla_frame.grid_rowconfigure(0, weight=1)

    columnas = ("id", "cliente", "total", "estado", "fecha")
    tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
    for c, txt in zip(columnas, ["ID", "Cliente", "Total", "Estado", "Fecha"]):
        tabla.heading(c, text=txt)
        tabla.column(c, anchor="center")
    tabla.grid(row=0, column=0, sticky="nsew")

    scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    scroll.grid(row=0, column=1, sticky="ns")

    return marco