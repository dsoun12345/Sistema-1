# estilos.py
# ARCHIVO CENTRAL DE ESTILOS (el "CSS" del proyecto)
# Aquí SOLO van valores: colores, fuentes, tamaños.
# Los componentes (tarjetas, barras, menú) van en la carpeta componentes/.
# NO MODIFICAR sin acordarlo en equipo.

import ttkbootstrap as ttk

TEMA = "cosmo"

# ─── COLORES PRINCIPALES ─────────────────────
COLOR_SIDEBAR        = "#5b4fc4"
COLOR_SIDEBAR_HOVER  = "#4a3fb0"
COLOR_SIDEBAR_ACTIVO = "#8b7fd9"
COLOR_FONDO          = "#f0f1f6"
COLOR_TEXTO          = "#2c2c3a"
COLOR_TEXTO_CLARO    = "#ffffff"

# ─── COLORES DE LAS TARJETAS ─────────────────
CARD_MORADO = "#7b5fd4"
CARD_ROSA   = "#e0518a"
CARD_CYAN   = "#3ec5e0"
CARD_VERDE  = "#3ec98a"

# ─── COLORES DE ESTADO ───────────────────────
COLOR_EXITO       = "#28a745"
COLOR_PELIGRO     = "#dc3545"
COLOR_ADVERTENCIA = "#ffc107"

# ─── FUENTES ─────────────────────────────────
FUENTE_TITULO    = ("Segoe UI", 20, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 14, "bold")
FUENTE_NORMAL    = ("Segoe UI", 11)
FUENTE_MENU      = ("Segoe UI", 11)
FUENTE_BOTON     = ("Segoe UI", 11, "bold")
FUENTE_CARD_NUM  = ("Segoe UI", 24, "bold")
FUENTE_CARD_TXT  = ("Segoe UI", 10)

# ─── TAMAÑOS ─────────────────────────────────
PADDING       = 15
ANCHO_SIDEBAR = 180


def aplicar_estilos(ventana):
    estilo = ttk.Style()
    estilo.configure("Titulo.TLabel", font=FUENTE_TITULO, foreground=COLOR_TEXTO)
    estilo.configure("Subtitulo.TLabel", font=FUENTE_SUBTITULO, foreground=COLOR_TEXTO)
    estilo.configure("Grande.TButton", font=FUENTE_BOTON, padding=10)
    return estilo