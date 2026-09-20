# componentes/tarjeta.py
# Tarjeta redondeada con degradado, responsiva.
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk, ImageFont
import estilos

RADIO_CARD = 18

def _hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _aclarar(rgb, factor=0.35):
    return tuple(int(c + (255 - c) * factor) for c in rgb)

def crear_tarjeta(padre, numero, titulo, color_hex):
    """Tarjeta redondeada con degradado que se redibuja al cambiar de tamaño.
    Devuelve el widget; colócalo con .grid(...) desde la pantalla."""
    contenedor = tk.Label(padre, bg=estilos.COLOR_FONDO, bd=0)
    contenedor._img_ref = None

    color1 = _hex_a_rgb(color_hex)
    color2 = _aclarar(color1, 0.35)

    def _redibujar(evento):
        ancho, alto = evento.width, evento.height
        if ancho < 10 or alto < 10:
            return

        base = Image.new("RGB", (ancho, alto), color1)
        px = base.load()
        for y in range(alto):
            for x in range(ancho):
                t = (x / ancho + y / alto) / 2
                px[x, y] = (
                    int(color1[0] + (color2[0] - color1[0]) * t),
                    int(color1[1] + (color2[1] - color1[1]) * t),
                    int(color1[2] + (color2[2] - color1[2]) * t),
                )

        mascara = Image.new("L", (ancho, alto), 0)
        ImageDraw.Draw(mascara).rounded_rectangle(
            [0, 0, ancho - 1, alto - 1], radius=RADIO_CARD, fill=255)

        img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
        img.paste(base, (0, 0), mascara)

        dibujo = ImageDraw.Draw(img)
        try:
            fnt_num = ImageFont.truetype("segoeuib.ttf", 26)
            fnt_txt = ImageFont.truetype("segoeui.ttf", 12)
        except:
            fnt_num = ImageFont.load_default()
            fnt_txt = ImageFont.load_default()
        dibujo.text((18, 16), str(numero), font=fnt_num, fill="white")
        dibujo.text((18, alto - 32), str(titulo), font=fnt_txt, fill="white")

        tk_img = ImageTk.PhotoImage(img)
        contenedor.configure(image=tk_img)
        contenedor._img_ref = tk_img

    contenedor.bind("<Configure>", _redibujar)
    return contenedor