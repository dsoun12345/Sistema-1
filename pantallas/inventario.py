# pantallas/inventario.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import estilos
from conexion import supabase
from componentes.barra_titulo import crear_barra_dialogo


def crear_inventario(padre):
    """Vista de Inventario: tabla de productos + botón para agregar."""
    marco = tk.Frame(padre, bg=estilos.COLOR_FONDO)
    marco.grid(row=0, column=0, sticky="nsew")
    marco.grid_columnconfigure(0, weight=1)
    marco.grid_rowconfigure(2, weight=1)   # la tabla crece

    # ── Barra superior: título + botón agregar ──
    top = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
    top.grid_columnconfigure(0, weight=1)

    tk.Label(top, text="Inventario", font=estilos.FUENTE_TITULO,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO
             ).grid(row=0, column=0, sticky="w")

    btn_agregar = ttk.Button(top, text="  + Agregar Producto  ",
                             bootstyle="primary",
                             command=lambda: abrir_formulario(marco, recargar_tabla))
    btn_agregar.grid(row=0, column=1, sticky="e", ipady=6)

    # ── Buscador ──
    buscador_frame = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    buscador_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
    tk.Label(buscador_frame, text="Buscar:", font=estilos.FUENTE_NORMAL,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO).pack(side="left")
    entrada_busqueda = ttk.Entry(buscador_frame, width=40)
    entrada_busqueda.pack(side="left", padx=8)

    # ── Tabla ──
    tabla_frame = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    tabla_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
    tabla_frame.grid_columnconfigure(0, weight=1)
    tabla_frame.grid_rowconfigure(0, weight=1)

    columnas = ("id", "nombre", "categoria", "precio_costo", "precio_venta",
                "stock", "stock_minimo")
    tabla = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
    encabezados = {
        "id": "ID", "nombre": "Nombre", "categoria": "Categoría",
        "precio_costo": "Precio Costo", "precio_venta": "Precio Venta",
        "stock": "Stock", "stock_minimo": "Stock Mín."
    }
    for col in columnas:
        tabla.heading(col, text=encabezados[col])
        tabla.column(col, anchor="center")
    tabla.column("id", width=50)
    tabla.column("nombre", width=250, anchor="w")
    tabla.tag_configure("par", background="#ffffff")
    tabla.tag_configure("impar", background="#f0f1f6")

    scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)

    tabla.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")

    # ── Función que carga los productos desde Supabase ──
    def recargar_tabla(filtro=""):
        # limpiar tabla
        for fila in tabla.get_children():
            tabla.delete(fila)
        try:
            resp = supabase.table("productos").select("*").order("id").execute()
            for p in resp.data:
                nombre = p.get("nombre", "")
                if filtro and filtro.lower() not in nombre.lower():
                    continue
                tag = "par" if len(tabla.get_children()) % 2 == 0 else "impar"
                tabla.insert("", END, tags=(tag,), values=(
                p.get("id", ""),
                nombre,
                p.get("categoria_id", "") or "-",
                f"{float(p.get('precio_costo') or 0):.2f}",
                f"{float(p.get('precio_venta') or 0):.2f}",
                p.get("stock", 0),
                p.get("stock_minimo", 0),
            ))
        except Exception as e:
            messagebox.showerror("Error", "No se pudieron cargar los productos:\n" + str(e))

    # buscar al escribir
    entrada_busqueda.bind("<KeyRelease>",
                          lambda e: recargar_tabla(entrada_busqueda.get()))

    recargar_tabla()   # cargar al abrir
    return marco


def abrir_formulario(padre, al_guardar):
    """Ventana emergente para agregar un producto nuevo."""
    ventana = tk.Toplevel(padre)
    ventana.title("Agregar Producto")
    ventana.configure(bg=estilos.COLOR_FONDO)
    crear_barra_dialogo(ventana, "Agregar Producto").pack(fill="x")

    # centrar sobre la ventana principal
    ancho, alto = 400, 580
    principal = padre.winfo_toplevel()
    x = principal.winfo_x() + (principal.winfo_width() - ancho) // 2
    y = principal.winfo_y() + (principal.winfo_height() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
    # sin barra de Windows la ventana puede quedar detrás de la principal,
    # así que la dejamos siempre al frente mientras esté abierta
    ventana.attributes("-topmost", True)
    ventana.grab_set()   # bloquea la ventana de atrás hasta cerrar esta
    ventana.focus_force()

    tk.Label(ventana, text="Nuevo Producto", font=estilos.FUENTE_SUBTITULO,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO).pack(pady=15)

    campos = {}

    def agregar_campo(etiqueta, valor_inicial=""):
        tk.Label(ventana, text=etiqueta, font=estilos.FUENTE_NORMAL,
                 bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO,
                 anchor="w").pack(fill="x", padx=30)
        entrada = ttk.Entry(ventana)
        entrada.insert(0, valor_inicial)
        entrada.pack(fill="x", padx=30, pady=(0, 10))
        return entrada

    campos["nombre"] = agregar_campo("Nombre del producto")
    campos["unidad_base"] = agregar_campo("Unidad base", "unidad")
    campos["precio_costo"] = agregar_campo("Precio de costo", "0")
    campos["precio_venta"] = agregar_campo("Precio de venta", "0")
    campos["stock"] = agregar_campo("Stock actual", "0")
    campos["stock_minimo"] = agregar_campo("Stock mínimo", "0")

    def guardar():
        nombre = campos["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Falta información", "El nombre es obligatorio.",
                                   parent=ventana)
            return
        try:
            nuevo = {
                "nombre": nombre,
                "unidad_base": campos["unidad_base"].get().strip() or "unidad",
                "precio_costo": float(campos["precio_costo"].get() or 0),
                "precio_venta": float(campos["precio_venta"].get() or 0),
                "stock": float(campos["stock"].get() or 0),
                "stock_minimo": float(campos["stock_minimo"].get() or 0),
                "activo": True,
            }
            supabase.table("productos").insert(nuevo).execute()
            messagebox.showinfo("Listo", "Producto agregado correctamente.",
                                parent=ventana)
            ventana.destroy()
            al_guardar()   # recargar la tabla
        except ValueError:
            messagebox.showwarning("Dato inválido",
                                   "Precios y stock deben ser números.",
                                   parent=ventana)
        except Exception as e:
            messagebox.showerror("Error", "No se pudo guardar:\n" + str(e),
                                 parent=ventana)

    ttk.Button(ventana, text="Guardar", bootstyle="success",
               command=guardar).pack(pady=20, ipadx=20)