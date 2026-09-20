# componentes/barra_titulo.py
# Barra de título propia estilo Chrome/Brave: sin la barra gris de Windows,
# pero conservando arrastrar, maximizar (doble clic o subir arriba) y
# redimensionar desde los bordes/esquinas.
import tkinter as tk
import estilos

BORDE = 6   # grosor de la zona sensible para redimensionar (en píxeles)

def crear_barra(ventana, titulo="Sistema de Inventario"):
    ventana.overrideredirect(True)
    ventana.update_idletasks()

    estado = {"max": False, "geo": ""}

    # ── Barra superior morada ──
    barra = tk.Frame(ventana, bg=estilos.COLOR_SIDEBAR, height=40)

    lbl = tk.Label(barra, text=titulo, bg=estilos.COLOR_SIDEBAR, fg="white",
                   font=estilos.FUENTE_BOTON, padx=15)
    lbl.pack(side="left")

    # ── Funciones de los botones ──
    def cerrar():
        ventana.destroy()

    def minimizar():
        ventana.overrideredirect(False)
        ventana.iconify()

    def _al_volver(e=None):
        if ventana.state() == "normal":
            ventana.overrideredirect(True)
    ventana.bind("<Map>", _al_volver)

    def maximizar():
        if not estado["max"]:
            estado["geo"] = ventana.geometry()
            sw = ventana.winfo_screenwidth()
            sh = ventana.winfo_screenheight()
            ventana.geometry(f"{sw}x{sh-48}+0+0")  # -48 deja ver la barra de tareas
            estado["max"] = True
        else:
            ventana.geometry(estado["geo"])
            estado["max"] = False

    def crear_btn(texto, comando, hover):
        b = tk.Label(barra, text=texto, bg=estilos.COLOR_SIDEBAR, fg="white",
                     font=("Segoe UI", 12), width=4, cursor="hand2")
        b.pack(side="right", fill="y")
        b.bind("<Button-1>", lambda e: comando())
        b.bind("<Enter>", lambda e: b.configure(bg=hover))
        b.bind("<Leave>", lambda e: b.configure(bg=estilos.COLOR_SIDEBAR))
    crear_btn("✕", cerrar, estilos.COLOR_PELIGRO)
    crear_btn("▢", maximizar, estilos.COLOR_SIDEBAR_HOVER)
    crear_btn("─", minimizar, estilos.COLOR_SIDEBAR_HOVER)

    # ── Arrastrar la ventana + snap al subir arriba ──
    arrastre = {"x": 0, "y": 0}

    def iniciar(e):
        arrastre["x"] = e.x_root - ventana.winfo_x()
        arrastre["y"] = e.y_root - ventana.winfo_y()

    def mover(e):
        if estado["max"]:      # si está maximizada y la arrastras, se restaura
            maximizar()
        x = e.x_root - arrastre["x"]
        y = e.y_root - arrastre["y"]
        ventana.geometry(f"+{x}+{y}")

    def soltar(e):
        # Snap: si soltaste pegado al borde superior, maximiza
        if e.y_root <= 3 and not estado["max"]:
            maximizar()

    for w in (barra, lbl):
        w.bind("<Button-1>", iniciar)
        w.bind("<B1-Motion>", mover)
        w.bind("<ButtonRelease-1>", soltar)
        w.bind("<Double-Button-1>", lambda e: maximizar())

    # ── Redimensionar desde los bordes y esquinas ──
    resize = {"activo": None, "x": 0, "y": 0, "gx": 0, "gy": 0, "gw": 0, "gh": 0}

    def _zona(e):
        w, h = ventana.winfo_width(), ventana.winfo_height()
        x, y = e.x_root - ventana.winfo_x(), e.y_root - ventana.winfo_y()
        izq, der = x <= BORDE, x >= w - BORDE
        arr, aba = y <= BORDE, y >= h - BORDE
        if der and aba: return "se"
        if izq and aba: return "sw"
        if der and arr: return "ne"
        if izq and arr: return "nw"
        if der: return "e"
        if izq: return "w"
        if aba: return "s"
        if arr: return "n"
        return None

    cursores = {"e": "sb_h_double_arrow", "w": "sb_h_double_arrow",
                "n": "sb_v_double_arrow", "s": "sb_v_double_arrow",
                "se": "size_nw_se", "nw": "size_nw_se",
                "ne": "size_ne_sw", "sw": "size_ne_sw"}

    def _cursor(e):
        if resize["activo"]:
            return
        z = _zona(e)
        ventana.configure(cursor=cursores.get(z, ""))

    def _iniciar_resize(e):
        z = _zona(e)
        if z:
            resize.update(activo=z, x=e.x_root, y=e.y_root,
                          gx=ventana.winfo_x(), gy=ventana.winfo_y(),
                          gw=ventana.winfo_width(), gh=ventana.winfo_height())

    def _hacer_resize(e):
        z = resize["activo"]
        if not z:
            return
        dx = e.x_root - resize["x"]
        dy = e.y_root - resize["y"]
        gx, gy, gw, gh = resize["gx"], resize["gy"], resize["gw"], resize["gh"]
        minw, minh = 800, 500
        nx, ny, nw, nh = gx, gy, gw, gh
        if "e" in z: nw = max(minw, gw + dx)
        if "s" in z: nh = max(minh, gh + dy)
        if "w" in z:
            nw = max(minw, gw - dx)
            nx = gx + (gw - nw)
        if "n" in z:
            nh = max(minh, gh - dy)
            ny = gy + (gh - nh)
        ventana.geometry(f"{nw}x{nh}+{nx}+{ny}")

    def _fin_resize(e):
        resize["activo"] = None

    ventana.bind("<Motion>", _cursor)
    ventana.bind("<Button-1>", _iniciar_resize, add="+")
    ventana.bind("<B1-Motion>", _hacer_resize, add="+")
    ventana.bind("<ButtonRelease-1>", _fin_resize, add="+")

    return barra