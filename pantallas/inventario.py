# pantallas/inventario.py
import io
import time
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from PIL import Image, ImageOps, ImageTk
import estilos
from conexion import supabase
from componentes.barra_titulo import crear_barra_dialogo
from componentes.boton import Boton

# Soporte para fotos HEIC/HEIF (iPhone). Si no está instalado, se ignora.
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

BUCKET_IMAGENES = "productos"   # bucket de Supabase Storage
TAM_MAX_IMAGEN = 800            # px: las imágenes se reducen a este tamaño al subir


def cargar_imagen_local(ruta, tam):
    """Abre cualquier imagen que Pillow entienda y devuelve una copia reducida."""
    img = Image.open(ruta)
    img = ImageOps.exif_transpose(img)   # respeta la rotación de fotos del celular
    img.thumbnail((tam, tam))
    return img


def descargar_imagen(ruta, tam):
    """Descarga una imagen del bucket y la devuelve reducida."""
    datos = supabase.storage.from_(BUCKET_IMAGENES).download(ruta)
    return cargar_imagen_local(io.BytesIO(datos), tam)


def imagen_a_webp(img):
    """Convierte la imagen a WEBP (liviano y conserva transparencia)."""
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=85)
    return buffer.getvalue()


def borrar_imagenes(rutas):
    """Borra archivos del bucket; si falla solo se avisa en consola."""
    rutas = [r for r in rutas if r]
    if not rutas:
        return
    try:
        supabase.storage.from_(BUCKET_IMAGENES).remove(rutas)
    except Exception as e:
        print("No se pudieron borrar imágenes:", e)


def numero(valor):
    """100.0 -> '100', 2.5 -> '2.5'"""
    valor = float(valor or 0)
    return str(int(valor)) if valor.is_integer() else str(valor)


def codigos_de(producto):
    return [c["codigo"] for c in producto.get("codigos_barras") or []]


def crear_casilla(marcada, tam=18):
    """Dibuja una casilla de verificación (marcada o vacía) como imagen."""
    from PIL import ImageDraw
    escala = 4   # se dibuja grande y se reduce para que salga suave
    t = tam * escala
    img = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    caja = (escala, escala, t - escala, t - escala)
    if marcada:
        d.rounded_rectangle(caja, radius=3 * escala, fill=estilos.COLOR_SIDEBAR)
        d.line([(t * 0.27, t * 0.52), (t * 0.43, t * 0.68), (t * 0.74, t * 0.34)],
               fill="white", width=int(2.2 * escala), joint="curve")
    else:
        d.rounded_rectangle(caja, radius=3 * escala, fill="white",
                            outline="#b5b5c8", width=int(1.5 * escala))
    return ImageTk.PhotoImage(img.resize((tam, tam), Image.LANCZOS))


def crear_inventario(padre):
    """Vista de Inventario: tabla de productos + detalle + agregar/editar/eliminar."""
    marco = tk.Frame(padre, bg=estilos.COLOR_FONDO)
    marco.grid(row=0, column=0, sticky="nsew")
    marco.grid_columnconfigure(0, weight=1)
    marco.grid_rowconfigure(2, weight=1)   # la tabla crece

    # ── Barra superior: título + botón agregar ──
    top = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
    top.grid_columnconfigure(0, weight=1)

    tk.Label(top, text="Inventario", font=estilos.FUENTE_TITULO,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO
             ).grid(row=0, column=0, sticky="w")

    btn_agregar = Boton(top, "+  Agregar producto",
                        lambda: abrir_formulario(marco, recargar_actual))
    btn_agregar.grid(row=0, column=1, sticky="e")

    # ── Buscador + acciones sobre la selección ──
    barra_acciones = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    barra_acciones.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
    tk.Label(barra_acciones, text="Buscar:", font=estilos.FUENTE_NORMAL,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO).pack(side="left")
    entrada_busqueda = ttk.Entry(barra_acciones, width=40)
    entrada_busqueda.pack(side="left", padx=8)
    tk.Label(barra_acciones, text="(ID, nombre o código de barras)",
             font=estilos.FUENTE_CARD_TXT, bg=estilos.COLOR_FONDO,
             fg="#8a8a9a").pack(side="left")

    btn_eliminar = Boton(barra_acciones, "Eliminar", lambda: eliminar_seleccion(),
                         estilo="peligro")
    btn_eliminar.pack(side="right")
    btn_editar = Boton(barra_acciones, "Editar", lambda: editar_seleccion(),
                       estilo="secundario")
    btn_editar.pack(side="right", padx=8)
    lbl_seleccion = tk.Label(barra_acciones, text="", font=estilos.FUENTE_CARD_TXT,
                             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO)
    lbl_seleccion.pack(side="right", padx=8)

    # ── Tabla ──
    tabla_frame = tk.Frame(marco, bg=estilos.COLOR_FONDO)
    tabla_frame.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=10)
    tabla_frame.grid_columnconfigure(0, weight=1)
    tabla_frame.grid_rowconfigure(0, weight=1)

    columnas = ("id", "nombre", "codigos", "categoria",
                "precio_costo", "precio_venta", "stock", "stock_minimo")
    # selectmode extended: Ctrl+clic y Shift+clic para elegir varios.
    # "tree" muestra la columna #0, que usamos para las casillas.
    tabla = ttk.Treeview(tabla_frame, columns=columnas, show="tree headings",
                         selectmode="extended")
    casillas = {"si": crear_casilla(True), "no": crear_casilla(False)}
    tabla.casillas = casillas   # guardar referencia para que no se borren
    tabla.column("#0", width=44, minwidth=44, stretch=False, anchor="center")
    tabla.heading("#0", image=casillas["no"], command=lambda: marcar_todos())
    encabezados = {
        "id": "ID", "nombre": "Nombre",
        "codigos": "Códigos de barras", "categoria": "Categoría",
        "precio_costo": "Precio Costo", "precio_venta": "Precio Venta",
        "stock": "Stock", "stock_minimo": "Stock Mín."
    }
    for col in columnas:
        tabla.heading(col, text=encabezados[col])
        tabla.column(col, anchor="center", width=100)
    tabla.column("id", width=50)
    tabla.column("nombre", width=220, anchor="w")
    tabla.column("codigos", width=160, anchor="w")
    tabla.tag_configure("par", background="#ffffff")
    tabla.tag_configure("impar", background="#f0f1f6")

    scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)

    tabla.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")

    # ── Panel de detalle (imagen del producto seleccionado) ──
    detalle = tk.Frame(marco, bg="white", width=260)
    detalle.grid(row=2, column=1, sticky="ns", padx=(0, 20), pady=10)
    detalle.grid_propagate(False)
    detalle.grid_columnconfigure(0, weight=1)

    caja_imagen = tk.Frame(detalle, bg="#f7f7fb", width=230, height=230)
    caja_imagen.grid(row=0, column=0, padx=15, pady=15)
    caja_imagen.pack_propagate(False)   # tamaño fijo, en píxeles
    lbl_imagen = tk.Label(caja_imagen, text="Selecciona un producto",
                          bg="#f7f7fb", fg="#8a8a9a", font=estilos.FUENTE_NORMAL)
    lbl_imagen.pack(expand=True, fill="both")
    lbl_nombre = tk.Label(detalle, text="", bg="white", fg=estilos.COLOR_TEXTO,
                          font=estilos.FUENTE_BOTON, wraplength=230, justify="center")
    lbl_nombre.grid(row=1, column=0, padx=15)
    lbl_info = tk.Label(detalle, text="", bg="white", fg=estilos.COLOR_TEXTO,
                        font=estilos.FUENTE_CARD_TXT, wraplength=230, justify="left")
    lbl_info.grid(row=2, column=0, padx=15, pady=10, sticky="w")

    productos = {}     # id -> fila de Supabase (para detalle y edición)
    cache_imgs = {}    # ruta en Storage -> PhotoImage (no descargar dos veces)

    def seleccionados():
        return [productos[int(tabla.item(i, "values")[0])] for i in tabla.selection()]

    def limpiar_detalle(texto="Selecciona un producto"):
        lbl_imagen.configure(image="", text=texto)
        lbl_nombre.configure(text="")
        lbl_info.configure(text="")

    def marcar_todos():
        filas = tabla.get_children()
        if filas and len(tabla.selection()) == len(filas):
            tabla.selection_remove(filas)
        else:
            tabla.selection_set(filas)

    def clic_tabla(e):
        # clic sobre la casilla: marca/desmarca solo esa fila (sin Ctrl)
        fila = tabla.identify_row(e.y)
        if fila and tabla.identify_column(e.x) == "#0":
            tabla.selection_toggle(fila)
            tabla.focus(fila)
            return "break"

    def al_seleccionar(_evento=None):
        sel_ids = set(tabla.selection())
        filas = tabla.get_children()
        for fila in filas:
            tabla.item(fila, image=casillas["si" if fila in sel_ids else "no"])
        todas = bool(filas) and len(sel_ids) == len(filas)
        tabla.heading("#0", image=casillas["si" if todas else "no"])
        sel = seleccionados()
        n = len(sel)
        btn_editar.activar(n == 1)
        btn_eliminar.activar(n > 0)
        btn_eliminar.configure(text=f"Eliminar ({n})" if n > 1 else "Eliminar")
        lbl_seleccion.configure(text=f"{n} seleccionados" if n > 1 else "")
        if n == 1:
            mostrar_detalle(sel[0])
        elif n > 1:
            limpiar_detalle(f"{n} productos\nseleccionados")
        else:
            limpiar_detalle()

    def mostrar_detalle(p):
        lbl_nombre.configure(text=p.get("nombre", ""))
        codigos = codigos_de(p)
        lbl_info.configure(text=(
            f"ID: {p['id']}\n"
            "Códigos:\n  " + ("\n  ".join(codigos) if codigos else "-")))

        ruta = p.get("imagen")
        if not ruta:
            lbl_imagen.configure(image="", text="Sin imagen")
            return
        if ruta not in cache_imgs:
            try:
                cache_imgs[ruta] = ImageTk.PhotoImage(descargar_imagen(ruta, 230))
            except Exception as e:
                lbl_imagen.configure(image="", text="No se pudo cargar\nla imagen")
                print("Error al descargar imagen:", e)
                return
        lbl_imagen.configure(image=cache_imgs[ruta], text="")

    def editar_seleccion(_evento=None):
        sel = seleccionados()
        if len(sel) == 1:
            abrir_formulario(marco, recargar_actual, producto=sel[0])

    def eliminar_seleccion(_evento=None):
        sel = seleccionados()
        if not sel:
            return
        if len(sel) == 1:
            pregunta = f"¿Eliminar el producto \"{sel[0]['nombre']}\"?"
        else:
            pregunta = f"¿Eliminar los {len(sel)} productos seleccionados?"
        if not messagebox.askyesno("Confirmar", pregunta + "\n\nEsta acción no se puede deshacer."):
            return
        try:
            # los códigos de barras se borran solos (on delete cascade)
            supabase.table("productos").delete() \
                .in_("id", [p["id"] for p in sel]).execute()
        except Exception as e:
            messagebox.showerror("Error", "No se pudo eliminar:\n" + str(e))
            return
        borrar_imagenes([p.get("imagen") for p in sel])
        recargar_actual()

    tabla.bind("<<TreeviewSelect>>", al_seleccionar)
    tabla.bind("<Button-1>", clic_tabla)
    tabla.bind("<Double-1>", lambda e: editar_seleccion()
               if tabla.identify_row(e.y) else None)
    tabla.bind("<Delete>", eliminar_seleccion)
    tabla.bind("<Control-a>", lambda e: (tabla.selection_set(tabla.get_children()), "break")[1])

    # ── Función que carga los productos desde Supabase ──
    def recargar_tabla(filtro=""):
        # limpiar tabla
        for fila in tabla.get_children():
            tabla.delete(fila)
        productos.clear()
        filtro = filtro.strip().lower()
        try:
            resp = (supabase.table("productos")
                    .select("*, codigos_barras(codigo)")
                    .order("id").execute())
            for p in resp.data:
                nombre = p.get("nombre", "")
                codigos = codigos_de(p)
                if filtro and not (filtro == str(p["id"])
                                   or filtro in nombre.lower()
                                   or any(filtro in c.lower() for c in codigos)):
                    continue
                productos[p["id"]] = p
                tag = "par" if len(tabla.get_children()) % 2 == 0 else "impar"
                tabla.insert("", END, tags=(tag,), image=casillas["no"], values=(
                    p.get("id", ""),
                    nombre,
                    ", ".join(codigos) or "-",
                    p.get("categoria_id", "") or "-",
                    f"{float(p.get('precio_costo') or 0):.2f}",
                    f"{float(p.get('precio_venta') or 0):.2f}",
                    numero(p.get("stock")),
                    numero(p.get("stock_minimo")),
                ))
        except Exception as e:
            messagebox.showerror("Error", "No se pudieron cargar los productos:\n" + str(e))
        al_seleccionar()

    def recargar_actual():
        recargar_tabla(entrada_busqueda.get())

    # buscar al escribir
    entrada_busqueda.bind("<KeyRelease>", lambda e: recargar_actual())

    recargar_tabla()   # cargar al abrir
    return marco


def abrir_formulario(padre, al_guardar, producto=None):
    """Ventana emergente para agregar un producto nuevo o editar uno existente."""
    editando = producto is not None
    titulo = "Editar Producto" if editando else "Agregar Producto"

    ventana = tk.Toplevel(padre)
    ventana.title(titulo)
    ventana.configure(bg=estilos.COLOR_FONDO)
    crear_barra_dialogo(ventana, titulo).pack(fill="x")

    # centrar sobre la ventana principal
    ancho, alto = 720, 540
    principal = padre.winfo_toplevel()
    x = principal.winfo_x() + (principal.winfo_width() - ancho) // 2
    y = principal.winfo_y() + (principal.winfo_height() - alto) // 2
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
    # sin barra de Windows la ventana puede quedar detrás de la principal,
    # así que la dejamos siempre al frente mientras esté abierta
    ventana.attributes("-topmost", True)
    ventana.grab_set()   # bloquea la ventana de atrás hasta cerrar esta
    ventana.focus_force()

    tk.Label(ventana, text="Editar Producto" if editando else "Nuevo Producto",
             font=estilos.FUENTE_SUBTITULO,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO).pack(pady=15)

    # cuerpo: datos a la izquierda, imagen a la derecha
    cuerpo = tk.Frame(ventana, bg=estilos.COLOR_FONDO)
    cuerpo.pack(fill="both", expand=True, padx=30)
    cuerpo.grid_columnconfigure((0, 1), weight=1, uniform="campos")

    campos = {}

    def agregar_campo(etiqueta, fila, columna, valor_inicial="", ancho_col=1):
        tk.Label(cuerpo, text=etiqueta, font=estilos.FUENTE_NORMAL,
                 bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO,
                 anchor="w").grid(row=fila * 2, column=columna, columnspan=ancho_col,
                                  sticky="w", padx=(0, 10))
        entrada = ttk.Entry(cuerpo)
        entrada.insert(0, valor_inicial)
        entrada.grid(row=fila * 2 + 1, column=columna, columnspan=ancho_col,
                     sticky="ew", padx=(0, 10), pady=(0, 10))
        return entrada

    p = producto or {}
    # el ID lo asigna Supabase: solo se muestra, no se puede escribir
    campo_id = agregar_campo("ID", 0, 0, str(p["id"]) if editando else "Automático")
    campo_id.configure(state="readonly")
    campos["unidad_base"] = agregar_campo("Unidad base", 0, 1,
                                          p.get("unidad_base") or "unidad")
    campos["nombre"] = agregar_campo("Nombre del producto", 1, 0,
                                     p.get("nombre", ""), ancho_col=2)
    # códigos de barras: se ven aquí y se gestionan en una ventana aparte
    codigos_lista = codigos_de(p)
    tk.Label(cuerpo, text="Códigos de barras", font=estilos.FUENTE_NORMAL,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO,
             anchor="w").grid(row=4, column=0, columnspan=2, sticky="w", padx=(0, 10))
    fila_codigos = tk.Frame(cuerpo, bg=estilos.COLOR_FONDO)
    fila_codigos.grid(row=5, column=0, columnspan=2, sticky="ew",
                      padx=(0, 10), pady=(0, 10))
    campo_codigos = ttk.Entry(fila_codigos)
    campo_codigos.pack(side="left", fill="x", expand=True)

    def mostrar_codigos():
        campo_codigos.configure(state="normal")
        campo_codigos.delete(0, "end")
        campo_codigos.insert(0, ", ".join(codigos_lista) or "Sin códigos")
        campo_codigos.configure(state="readonly")

    def gestionar_codigos(_e=None):
        def al_aceptar(nuevos):
            codigos_lista[:] = nuevos
            mostrar_codigos()
        abrir_editor_codigos(ventana, codigos_lista, p.get("id"), al_aceptar)

    Boton(fila_codigos, "Gestionar", gestionar_codigos, estilo="secundario",
          pady=4).pack(side="left", padx=(8, 0))
    campo_codigos.bind("<Button-1>", gestionar_codigos)
    mostrar_codigos()
    campos["precio_costo"] = agregar_campo("Precio de costo", 3, 0,
                                           numero(p.get("precio_costo")))
    campos["precio_venta"] = agregar_campo("Precio de venta", 3, 1,
                                           numero(p.get("precio_venta")))
    campos["stock"] = agregar_campo("Stock actual", 4, 0, numero(p.get("stock")))
    campos["stock_minimo"] = agregar_campo("Stock mínimo", 4, 1,
                                           numero(p.get("stock_minimo")))

    # ── Imagen ──
    imagen_frame = tk.Frame(cuerpo, bg=estilos.COLOR_FONDO)
    imagen_frame.grid(row=0, column=2, rowspan=10, sticky="n", padx=(10, 0))
    caja_previa = tk.Frame(imagen_frame, bg="white", width=200, height=200)
    caja_previa.pack()
    caja_previa.pack_propagate(False)   # tamaño fijo, en píxeles
    vista_previa = tk.Label(caja_previa, text="Sin imagen", bg="white",
                            fg="#8a8a9a", font=estilos.FUENTE_NORMAL)
    vista_previa.pack(expand=True, fill="both")
    # img: imagen nueva elegida | foto: referencia para tkinter | cambio: hay que guardar
    imagen = {"img": None, "foto": None, "cambio": False}

    def mostrar_previa(img):
        miniatura = img.copy()
        miniatura.thumbnail((200, 200))
        imagen["foto"] = ImageTk.PhotoImage(miniatura)
        vista_previa.configure(image=imagen["foto"], text="")
        btn_quitar.pack(fill="x", pady=(5, 0))

    def elegir_imagen():
        ruta = filedialog.askopenfilename(
            parent=ventana, title="Elegir imagen del producto",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.gif *.bmp "
                                    "*.tif *.tiff *.ico *.heic *.heif *.avif"),
                       ("Todos los archivos", "*.*")])
        if not ruta:
            return
        try:
            img = cargar_imagen_local(ruta, TAM_MAX_IMAGEN)
            img.load()
        except Exception:
            messagebox.showwarning("Imagen inválida",
                                   "No se pudo abrir ese archivo como imagen.",
                                   parent=ventana)
            return
        imagen.update(img=img, cambio=True)
        mostrar_previa(img)

    def quitar_imagen():
        imagen.update(img=None, foto=None, cambio=True)
        vista_previa.configure(image="", text="Sin imagen")
        btn_quitar.pack_forget()

    ttk.Button(imagen_frame, text="Elegir imagen", bootstyle="secondary",
               command=elegir_imagen).pack(fill="x", pady=(10, 0))
    btn_quitar = ttk.Button(imagen_frame, text="Quitar imagen",
                            bootstyle="secondary-outline", command=quitar_imagen)

    imagen_anterior = p.get("imagen")
    if imagen_anterior:
        try:
            mostrar_previa(descargar_imagen(imagen_anterior, 200))
        except Exception as e:
            vista_previa.configure(text="No se pudo cargar\nla imagen")
            print("Error al descargar imagen:", e)

    def guardar():
        nombre = campos["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Falta información", "El nombre es obligatorio.",
                                   parent=ventana)
            return
        codigos = list(codigos_lista)
        try:
            datos = {
                "nombre": nombre,
                "unidad_base": campos["unidad_base"].get().strip() or "unidad",
                "precio_costo": float(campos["precio_costo"].get() or 0),
                "precio_venta": float(campos["precio_venta"].get() or 0),
                "stock": float(campos["stock"].get() or 0),
                "stock_minimo": float(campos["stock_minimo"].get() or 0),
            }
        except ValueError:
            messagebox.showwarning("Dato inválido",
                                   "Precios y stock deben ser números.",
                                   parent=ventana)
            return

        codigos_antes = codigos_de(p)
        codigos_nuevos = [c for c in codigos if c not in codigos_antes]
        codigos_quitados = [c for c in codigos_antes if c not in codigos]

        producto_id = p.get("id")
        try:
            if editando:
                # primero los códigos nuevos: si alguno está repetido falla
                # antes de tocar el producto
                if codigos_nuevos:
                    supabase.table("codigos_barras").insert(
                        [{"producto_id": producto_id, "codigo": c} for c in codigos_nuevos]
                    ).execute()
                supabase.table("productos").update(datos).eq("id", producto_id).execute()
                if codigos_quitados:
                    supabase.table("codigos_barras").delete() \
                        .eq("producto_id", producto_id) \
                        .in_("codigo", codigos_quitados).execute()
            else:
                datos["activo"] = True
                resp = supabase.table("productos").insert(datos).execute()
                producto_id = resp.data[0]["id"]
                if codigos_nuevos:
                    supabase.table("codigos_barras").insert(
                        [{"producto_id": producto_id, "codigo": c} for c in codigos_nuevos]
                    ).execute()

            if imagen["cambio"]:
                ruta = None
                if imagen["img"] is not None:
                    ruta = f"{producto_id}_{int(time.time())}.webp"
                    supabase.storage.from_(BUCKET_IMAGENES).upload(
                        ruta, imagen_a_webp(imagen["img"]),
                        {"content-type": "image/webp", "upsert": "true"})
                supabase.table("productos").update({"imagen": ruta}) \
                    .eq("id", producto_id).execute()
                borrar_imagenes([imagen_anterior])
        except Exception as e:
            # si un producto nuevo falló a medias, no dejarlo incompleto
            if not editando and producto_id is not None:
                try:
                    supabase.table("productos").delete().eq("id", producto_id).execute()
                except Exception:
                    pass
            texto = str(e)
            if "duplicate" in texto.lower() or "23505" in texto:
                texto = "Alguno de los códigos de barras ya existe en otro producto.\n\n" + texto
            messagebox.showerror("Error", "No se pudo guardar:\n" + texto,
                                 parent=ventana)
            return

        messagebox.showinfo("Listo", "Producto actualizado correctamente." if editando
                            else "Producto agregado correctamente.", parent=ventana)
        ventana.destroy()
        al_guardar()   # recargar la tabla

    ttk.Button(ventana, text="Guardar", bootstyle="success",
               command=guardar).pack(pady=20, ipadx=20)


def abrir_editor_codigos(dueno, codigos, producto_id, al_aceptar):
    """Ventana con la lista de códigos de barras de un producto.
    Un código no puede repetirse en la lista ni pertenecer a otro producto."""
    win = tk.Toplevel(dueno)
    win.title("Códigos de barras")
    win.configure(bg=estilos.COLOR_FONDO)
    crear_barra_dialogo(win, "Códigos de barras").pack(fill="x")

    ancho, alto = 420, 480
    x = dueno.winfo_x() + (dueno.winfo_width() - ancho) // 2
    y = dueno.winfo_y() + (dueno.winfo_height() - alto) // 2
    win.geometry(f"{ancho}x{alto}+{x}+{y}")
    win.attributes("-topmost", True)
    win.grab_set()

    # al cerrarse (Aceptar, Cancelar o ✕) el formulario vuelve a ser el activo
    def al_destruir(e):
        if e.widget is win and dueno.winfo_exists():
            dueno.after_idle(dueno.grab_set)
    win.bind("<Destroy>", al_destruir)

    lista = list(codigos)

    cuerpo = tk.Frame(win, bg=estilos.COLOR_FONDO)
    cuerpo.pack(fill="both", expand=True, padx=20, pady=(15, 0))
    cuerpo.grid_columnconfigure(0, weight=1)
    cuerpo.grid_rowconfigure(2, weight=1)

    tk.Label(cuerpo, text="Escanea o escribe un código y presiona Enter",
             font=estilos.FUENTE_NORMAL, bg=estilos.COLOR_FONDO,
             fg=estilos.COLOR_TEXTO, anchor="w").grid(row=0, column=0, sticky="w")

    fila = tk.Frame(cuerpo, bg=estilos.COLOR_FONDO)
    fila.grid(row=1, column=0, sticky="ew", pady=(5, 10))
    entrada = ttk.Entry(fila)
    entrada.pack(side="left", fill="x", expand=True)
    Boton(fila, "Agregar", lambda: agregar(), pady=4).pack(side="left", padx=(8, 0))

    caja = tk.Frame(cuerpo, bg="white", highlightthickness=1,
                    highlightbackground="#d0d0dc")
    caja.grid(row=2, column=0, sticky="nsew")
    listbox = tk.Listbox(caja, font=("Segoe UI", 11), bd=0, highlightthickness=0,
                         selectmode="extended", activestyle="none",
                         selectbackground=estilos.COLOR_SIDEBAR_ACTIVO,
                         selectforeground="white", fg=estilos.COLOR_TEXTO)
    barra = ttk.Scrollbar(caja, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=barra.set)
    listbox.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)
    barra.pack(side="right", fill="y")

    pie_lista = tk.Frame(cuerpo, bg=estilos.COLOR_FONDO)
    pie_lista.grid(row=3, column=0, sticky="ew", pady=(8, 0))
    lbl_total = tk.Label(pie_lista, text="", font=estilos.FUENTE_CARD_TXT,
                         bg=estilos.COLOR_FONDO, fg="#8a8a9a")
    lbl_total.pack(side="left")
    btn_quitar = Boton(pie_lista, "Quitar", lambda: quitar(), estilo="peligro", pady=4)
    btn_quitar.pack(side="right")

    def actualizar():
        n = len(lista)
        lbl_total.configure(text="Sin códigos" if n == 0 else
                            f"{n} código" + ("s" if n != 1 else ""))
        btn_quitar.activar(bool(listbox.curselection()))

    def avisar(titulo, texto):
        messagebox.showwarning(titulo, texto, parent=win)
        entrada.focus_set()
        entrada.select_range(0, "end")

    def agregar():
        codigo = entrada.get().strip()
        if not codigo:
            return
        if codigo in lista:
            listbox.selection_clear(0, "end")
            listbox.selection_set(lista.index(codigo))
            listbox.see(lista.index(codigo))
            actualizar()
            avisar("Código repetido", f"El código {codigo} ya está en la lista.")
            return
        # ¿lo tiene otro producto? (la base de datos también lo impide al guardar)
        try:
            resp = (supabase.table("codigos_barras")
                    .select("producto_id, productos(nombre)")
                    .eq("codigo", codigo).execute())
            otro = next((r for r in resp.data if r["producto_id"] != producto_id), None)
        except Exception as e:
            print("No se pudo verificar el código:", e)
            otro = None
        if otro:
            nombre = (otro.get("productos") or {}).get("nombre", "")
            avisar("Código en uso",
                   f"El código {codigo} ya pertenece al producto "
                   f"#{otro['producto_id']} - {nombre}.\n\n"
                   "Un código de barras solo puede tener un producto.")
            return
        lista.append(codigo)
        listbox.insert("end", codigo)
        listbox.see("end")
        entrada.delete(0, "end")
        entrada.focus_set()
        actualizar()

    def quitar(_e=None):
        for i in reversed(listbox.curselection()):
            listbox.delete(i)
            del lista[i]
        actualizar()

    def aceptar():
        al_aceptar(lista)
        win.destroy()

    for c in lista:
        listbox.insert("end", c)
    entrada.bind("<Return>", lambda e: agregar())
    listbox.bind("<<ListboxSelect>>", lambda e: actualizar())
    listbox.bind("<Delete>", quitar)

    pie = tk.Frame(win, bg=estilos.COLOR_FONDO)
    pie.pack(fill="x", padx=20, pady=15)
    Boton(pie, "Aceptar", aceptar).pack(side="right")
    Boton(pie, "Cancelar", win.destroy, estilo="secundario").pack(side="right", padx=8)

    actualizar()
    entrada.focus_force()
