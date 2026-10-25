# pantallas/categorias.py
# Categorías de productos creadas por el usuario, anidadas como en Odoo:
#   Abarrotes / Bebidas / Gaseosas / ...
# Cada categoría guarda su padre (padre_id); sin padre = categoría principal.
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from collections import Counter
from tkinter import messagebox
import estilos
from conexion import supabase
from componentes.barra_titulo import crear_barra_dialogo
from componentes.boton import Boton

SEPARADOR = " / "


def cargar_categorias():
    """id -> {id, nombre, padre_id}"""
    resp = supabase.table("categorias").select("id, nombre, padre_id").execute()
    return {c["id"]: c for c in resp.data}


def ruta_de(cat_id, cats):
    """Nombre completo: 'Abarrotes / Bebidas / Gaseosas'. '' si no tiene."""
    partes, vistos = [], set()
    while cat_id in cats and cat_id not in vistos:   # vistos: por si hubiera un ciclo
        vistos.add(cat_id)
        partes.append(cats[cat_id]["nombre"])
        cat_id = cats[cat_id]["padre_id"]
    return SEPARADOR.join(reversed(partes))


def rutas_ordenadas(cats, excluir=()):
    """[(ruta, id)] en orden alfabético."""
    return sorted(((ruta_de(i, cats), i) for i in cats if i not in excluir),
                  key=lambda r: r[0].lower())


def hijos_de(padre_id, cats):
    return sorted((c for c in cats.values() if c["padre_id"] == padre_id),
                  key=lambda c: c["nombre"].lower())


def con_descendientes(cat_id, cats):
    """La categoría y todas las que cuelgan de ella, a cualquier nivel."""
    ids, pendientes = set(), [cat_id]
    while pendientes:
        actual = pendientes.pop()
        if actual not in ids:
            ids.add(actual)
            pendientes += [c["id"] for c in cats.values() if c["padre_id"] == actual]
    return ids


def partir_ruta(texto):
    """'Abarrotes / Bebidas' -> ['Abarrotes', 'Bebidas']"""
    return [p.strip() for p in str(texto or "").split("/") if p.strip()]


def buscar_hija(padre_id, nombre, cats):
    nombre = nombre.strip().lower()
    return next((c for c in cats.values()
                 if c["padre_id"] == padre_id and c["nombre"].lower() == nombre), None)


def buscar_ruta(partes, cats):
    """id de la categoría con esa ruta, o None si alguna parte no existe."""
    padre_id = None
    for nombre in partes:
        cat = buscar_hija(padre_id, nombre, cats)
        if cat is None:
            return None
        padre_id = cat["id"]
    return padre_id


def crear_ruta(partes, cats):
    """Como buscar_ruta, pero crea las partes que falten. Devuelve el id final."""
    padre_id = None
    for nombre in partes:
        cat = buscar_hija(padre_id, nombre, cats)
        if cat is None:
            cat = supabase.table("categorias").insert(
                {"nombre": nombre, "padre_id": padre_id}).execute().data[0]
            cats[cat["id"]] = cat
        padre_id = cat["id"]
    return padre_id


def preparar_dialogo(win, dueno, titulo, ancho, alto):
    """Barra, tamaño centrado, siempre al frente y modal. Al cerrarse,
    la ventana de atrás (si es un diálogo) vuelve a ser la activa."""
    win.title(titulo)
    win.configure(bg=estilos.COLOR_FONDO)
    crear_barra_dialogo(win, titulo).pack(fill="x")
    principal = dueno.winfo_toplevel()
    x = principal.winfo_x() + (principal.winfo_width() - ancho) // 2
    y = principal.winfo_y() + (principal.winfo_height() - alto) // 2
    win.geometry(f"{ancho}x{alto}+{x}+{y}")
    win.attributes("-topmost", True)
    win.grab_set()
    win.focus_force()

    def al_destruir(e):
        if e.widget is win and isinstance(principal, tk.Toplevel) and principal.winfo_exists():
            principal.after_idle(principal.grab_set)
    win.bind("<Destroy>", al_destruir)


def abrir_gestor_categorias(dueno, al_cambiar=None, al_elegir=None, actual=None):
    """Árbol de categorías para crear, editar y eliminar.
    Con al_elegir sirve además para escoger la categoría de un producto."""
    eligiendo = al_elegir is not None
    titulo = "Elegir categoría" if eligiendo else "Categorías de productos"
    win = tk.Toplevel(dueno)
    preparar_dialogo(win, dueno, titulo, 560, 580)

    # el pie va primero para que el árbol nunca lo tape
    pie = tk.Frame(win, bg=estilos.COLOR_FONDO)
    pie.pack(side="bottom", fill="x", padx=20, pady=15)

    cuerpo = tk.Frame(win, bg=estilos.COLOR_FONDO)
    cuerpo.pack(fill="both", expand=True, padx=20, pady=(15, 0))
    cuerpo.grid_columnconfigure(0, weight=1)
    cuerpo.grid_rowconfigure(2, weight=1)

    tk.Label(cuerpo, text="Crea subcategorías dentro de otras, tantos niveles como "
                          "quieras.\nEj: Abarrotes / Bebidas / Gaseosas",
             font=estilos.FUENTE_CARD_TXT, bg=estilos.COLOR_FONDO, fg="#8a8a9a",
             justify="left").grid(row=0, column=0, sticky="w")

    acciones = tk.Frame(cuerpo, bg=estilos.COLOR_FONDO)
    acciones.grid(row=1, column=0, sticky="ew", pady=10)
    Boton(acciones, "+ Nueva", lambda: nueva(None), pady=4).pack(side="left")
    btn_sub = Boton(acciones, "+ Subcategoría", lambda: nueva(seleccion()),
                    estilo="secundario", pady=4)
    btn_sub.pack(side="left", padx=8)
    btn_eliminar = Boton(acciones, "Eliminar", lambda: eliminar(), estilo="peligro", pady=4)
    btn_eliminar.pack(side="right")
    btn_editar = Boton(acciones, "Editar", lambda: editar(), estilo="secundario", pady=4)
    btn_editar.pack(side="right", padx=8)

    arbol_frame = tk.Frame(cuerpo, bg=estilos.COLOR_FONDO)
    arbol_frame.grid(row=2, column=0, sticky="nsew")
    arbol_frame.grid_columnconfigure(0, weight=1)
    arbol_frame.grid_rowconfigure(0, weight=1)
    arbol = ttk.Treeview(arbol_frame, columns=("productos",), show="tree headings",
                         selectmode="browse", height=8)
    arbol.heading("#0", text="Categoría", anchor="w")
    arbol.heading("productos", text="Productos")
    arbol.column("#0", width=380, anchor="w")
    arbol.column("productos", width=90, anchor="center", stretch=False)
    scroll = ttk.Scrollbar(arbol_frame, orient="vertical", command=arbol.yview)
    arbol.configure(yscrollcommand=scroll.set)
    arbol.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    lbl_vacio = tk.Label(arbol_frame, text="Aún no hay categorías.\n"
                                           "Crea la primera con \"+ Nueva\".",
                         font=estilos.FUENTE_NORMAL, bg="white", fg="#8a8a9a")

    if eligiendo:
        btn_elegir = Boton(pie, "Elegir", lambda: elegir(seleccion()))
        btn_elegir.pack(side="right")
        Boton(pie, "Cancelar", win.destroy, estilo="secundario").pack(side="right", padx=8)
        Boton(pie, "Sin categoría", lambda: elegir(None),
              estilo="secundario").pack(side="left")
    else:
        Boton(pie, "Cerrar", win.destroy).pack(side="right")
        Boton(pie, "Importar / Exportar Excel", lambda: abrir_excel(),
              estilo="secundario").pack(side="left")

    estado = {"cats": {}, "conteo": Counter()}

    def seleccion():
        sel = arbol.selection()
        return int(sel[0]) if sel else None

    def al_seleccionar(_e=None):
        hay = seleccion() is not None
        for b in (btn_sub, btn_editar, btn_eliminar):
            b.activar(hay)
        if eligiendo:
            btn_elegir.activar(hay)

    def recargar(seleccionar=None):
        try:
            estado["cats"] = cargar_categorias()
            resp = supabase.table("productos").select("categoria_id").execute()
            estado["conteo"] = Counter(p["categoria_id"] for p in resp.data)
        except Exception as e:
            messagebox.showerror("Error", "No se pudieron cargar las categorías:\n" + str(e),
                                 parent=win)
            return
        arbol.delete(*arbol.get_children())

        def insertar(padre_id, nodo):
            for c in hijos_de(padre_id, estado["cats"]):
                arbol.insert(nodo, END, iid=str(c["id"]), text="  " + c["nombre"],
                             values=(estado["conteo"].get(c["id"]) or "",), open=True)
                insertar(c["id"], str(c["id"]))
        insertar(None, "")

        if estado["cats"]:
            lbl_vacio.place_forget()
        else:
            lbl_vacio.place(relx=0.5, rely=0.5, anchor="center")
        if seleccionar is not None and arbol.exists(str(seleccionar)):
            arbol.selection_set(str(seleccionar))
            arbol.see(str(seleccionar))
        al_seleccionar()

    def guardado(cat_id):
        recargar(cat_id)
        if al_cambiar:
            al_cambiar()

    def nueva(padre_id):
        abrir_editor_categoria(win, estado["cats"], guardado, padre_id=padre_id)

    def editar():
        cat_id = seleccion()
        if cat_id is not None:
            abrir_editor_categoria(win, estado["cats"], guardado,
                                   categoria=estado["cats"][cat_id])

    def eliminar():
        cat_id = seleccion()
        if cat_id is None:
            return
        cats = estado["cats"]
        nombre = ruta_de(cat_id, cats)
        if hijos_de(cat_id, cats):
            messagebox.showwarning("No se puede eliminar",
                                   f"\"{nombre}\" tiene subcategorías.\n"
                                   "Elimínalas o muévelas primero.", parent=win)
            return
        n = estado["conteo"].get(cat_id, 0)
        if n:
            messagebox.showwarning("No se puede eliminar",
                                   f"\"{nombre}\" tiene {n} producto(s).\n"
                                   "Cámbialos de categoría primero.", parent=win)
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar la categoría \"{nombre}\"?",
                                   parent=win):
            return
        try:
            supabase.table("categorias").delete().eq("id", cat_id).execute()
        except Exception as e:
            messagebox.showerror("Error", "No se pudo eliminar:\n" + str(e), parent=win)
            return
        guardado(None)

    def elegir(cat_id):
        win.destroy()
        al_elegir(cat_id)

    def abrir_excel():
        # import aquí: importar_excel también importa este archivo
        from pantallas.importar_excel import abrir_importador_categorias
        abrir_importador_categorias(win, lambda: guardado(seleccion()))

    arbol.bind("<<TreeviewSelect>>", al_seleccionar)
    arbol.bind("<Double-1>", lambda e: (elegir(seleccion()) if eligiendo else editar())
               if arbol.identify_row(e.y) else None)
    arbol.bind("<Delete>", lambda e: eliminar())
    recargar(actual)


def abrir_editor_categoria(dueno, cats, al_guardar, categoria=None, padre_id=None):
    """Ventana para crear o editar una categoría: nombre + categoría padre."""
    editando = categoria is not None
    titulo = "Editar categoría" if editando else "Nueva categoría"
    win = tk.Toplevel(dueno)
    preparar_dialogo(win, dueno, titulo, 460, 480)
    if editando:
        padre_id = categoria["padre_id"]

    pie = tk.Frame(win, bg=estilos.COLOR_FONDO)
    pie.pack(side="bottom", fill="x", padx=20, pady=15)
    Boton(pie, "Guardar", lambda: guardar()).pack(side="right")
    Boton(pie, "Cancelar", win.destroy, estilo="secundario").pack(side="right", padx=8)

    cuerpo = tk.Frame(win, bg=estilos.COLOR_FONDO)
    cuerpo.pack(fill="both", expand=True, padx=20, pady=(15, 0))
    cuerpo.grid_columnconfigure(0, weight=1)
    cuerpo.grid_rowconfigure(3, weight=1)

    tk.Label(cuerpo, text="Nombre", font=estilos.FUENTE_NORMAL, bg=estilos.COLOR_FONDO,
             fg=estilos.COLOR_TEXTO).grid(row=0, column=0, sticky="w")
    entrada = ttk.Entry(cuerpo)
    entrada.insert(0, categoria["nombre"] if editando else "")
    entrada.grid(row=1, column=0, sticky="ew", pady=(0, 12))

    tk.Label(cuerpo, text="¿Dentro de qué categoría va?", font=estilos.FUENTE_NORMAL,
             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_TEXTO).grid(row=2, column=0, sticky="w")
    # lista en vez de combobox: el desplegable puede quedar detrás de esta ventana
    caja = tk.Frame(cuerpo, bg="white", highlightthickness=1, highlightbackground="#d0d0dc")
    caja.grid(row=3, column=0, sticky="nsew", pady=(4, 0))
    lbl_resultado = tk.Label(cuerpo, text="", font=estilos.FUENTE_CARD_TXT,
                             bg=estilos.COLOR_FONDO, fg=estilos.COLOR_SIDEBAR,
                             anchor="w", justify="left", wraplength=400)
    lbl_resultado.grid(row=4, column=0, sticky="ew", pady=(8, 0))
    listbox = tk.Listbox(caja, font=("Segoe UI", 10), bd=0, highlightthickness=0,
                         activestyle="none", exportselection=False,
                         selectbackground=estilos.COLOR_SIDEBAR_ACTIVO,
                         selectforeground="white", fg=estilos.COLOR_TEXTO)
    barra = ttk.Scrollbar(caja, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=barra.set)
    listbox.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)
    barra.pack(side="right", fill="y")

    # una categoría no puede quedar dentro de sí misma ni de sus subcategorías
    excluir = con_descendientes(categoria["id"], cats) if editando else ()
    opciones = [("— En ninguna (es una categoría principal) —", None)] + \
        rutas_ordenadas(cats, excluir)
    for texto, _ in opciones:
        listbox.insert("end", texto)
    indice = next((i for i, (_, cid) in enumerate(opciones) if cid == padre_id), 0)
    listbox.selection_set(indice)
    listbox.see(indice)

    def mostrar_resultado(_e=None):
        """Vista previa del nombre completo: 'awa / awa de coco'."""
        sel = listbox.curselection()
        padre = opciones[sel[0]][1] if sel else None
        nombre = " ".join(entrada.get().split()) or "(sin nombre)"
        ruta = ruta_de(padre, cats) + SEPARADOR + nombre if padre is not None else nombre
        principal = "  (categoría principal)" if padre is None else ""
        lbl_resultado.configure(text=f"Quedará así:  {ruta}{principal}")

    listbox.bind("<<ListboxSelect>>", mostrar_resultado)
    entrada.bind("<KeyRelease>", mostrar_resultado)
    mostrar_resultado()

    def guardar():
        nombre = " ".join(entrada.get().split())
        if not nombre:
            messagebox.showwarning("Falta información", "Escribe un nombre.", parent=win)
            return
        if "/" in nombre:
            messagebox.showwarning("Nombre inválido",
                                   "El nombre no puede llevar \"/\".\n"
                                   "Para subcategorías elige la categoría padre abajo.",
                                   parent=win)
            return
        sel = listbox.curselection()
        nuevo_padre = opciones[sel[0]][1] if sel else None
        repetida = buscar_hija(nuevo_padre, nombre, cats)
        if repetida and (not editando or repetida["id"] != categoria["id"]):
            messagebox.showwarning("Categoría repetida",
                                   f"Ya existe \"{ruta_de(repetida['id'], cats)}\".",
                                   parent=win)
            return
        datos = {"nombre": nombre, "padre_id": nuevo_padre}
        try:
            if editando:
                supabase.table("categorias").update(datos).eq("id", categoria["id"]).execute()
                cat_id = categoria["id"]
            else:
                cat_id = supabase.table("categorias").insert(datos).execute().data[0]["id"]
        except Exception as e:
            messagebox.showerror("Error", "No se pudo guardar:\n" + str(e), parent=win)
            return
        win.destroy()
        al_guardar(cat_id)

    entrada.bind("<Return>", lambda e: guardar())
    entrada.focus_set()
