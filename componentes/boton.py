# componentes/boton.py
# Botón plano con el estilo del programa (mismo morado que el menú lateral).
# Estilos disponibles:
#   "primario"   -> morado relleno (acción principal, ej: Agregar)
#   "secundario" -> blanco con borde morado (ej: Editar)
#   "peligro"    -> blanco con borde rojo, se pone rojo al pasar el mouse (ej: Eliminar)
import tkinter as tk
import estilos

COLOR_DESACTIVADO_BG = "#e4e4ee"
COLOR_DESACTIVADO_FG = "#a5a5b8"
COLOR_PELIGRO_HOVER  = "#c82333"

# estilo -> (fondo, texto, borde, fondo_hover, texto_hover)
ESTILOS = {
    "primario":   (estilos.COLOR_SIDEBAR, "white", estilos.COLOR_SIDEBAR,
                   estilos.COLOR_SIDEBAR_HOVER, "white"),
    "secundario": ("white", estilos.COLOR_SIDEBAR, estilos.COLOR_SIDEBAR,
                   estilos.COLOR_SIDEBAR, "white"),
    "peligro":    ("white", estilos.COLOR_PELIGRO, estilos.COLOR_PELIGRO,
                   estilos.COLOR_PELIGRO, "white"),
}


class Boton(tk.Label):
    """Botón plano. Usar .activar(True/False) para habilitarlo o deshabilitarlo."""

    def __init__(self, padre, texto, comando, estilo="primario", **kwargs):
        self._colores = ESTILOS[estilo]
        self._comando = comando
        self._activo = True
        fondo, texto_color, borde, _, _ = self._colores
        opciones = dict(font=("Segoe UI", 10, "bold"), padx=18, pady=7)
        opciones.update(kwargs)   # permite cambiar padx/pady/font al crearlo
        super().__init__(padre, text=texto, bg=fondo, fg=texto_color,
                         cursor="hand2", highlightthickness=1,
                         highlightbackground=borde, highlightcolor=borde,
                         **opciones)
        self.bind("<Enter>", self._al_entrar)
        self.bind("<Leave>", self._al_salir)
        self.bind("<Button-1>", self._al_clic)

    def activar(self, activo=True):
        self._activo = activo
        if activo:
            fondo, texto_color, borde, _, _ = self._colores
            self.configure(bg=fondo, fg=texto_color, cursor="hand2",
                           highlightbackground=borde, highlightcolor=borde)
        else:
            self.configure(bg=COLOR_DESACTIVADO_BG, fg=COLOR_DESACTIVADO_FG,
                           cursor="arrow", highlightbackground=COLOR_DESACTIVADO_BG,
                           highlightcolor=COLOR_DESACTIVADO_BG)

    def _al_entrar(self, _e):
        if self._activo:
            _, _, _, fondo_hover, texto_hover = self._colores
            self.configure(bg=fondo_hover, fg=texto_hover)

    def _al_salir(self, _e):
        if self._activo:
            fondo, texto_color, _, _, _ = self._colores
            self.configure(bg=fondo, fg=texto_color)

    def _al_clic(self, _e):
        if self._activo and self._comando:
            self._comando()
