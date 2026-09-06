import ttkbootstrap as ttk
from ttkbootstrap.constants import *

app = ttk.Window(themename="cosmo")
app.title("Sistema de Inventario")
app.geometry("800x600")

ttk.Label(app, text="¡Funciona! 🎉", font=("Arial", 24)).pack(pady=50)
ttk.Button(app, text="Botón de prueba", bootstyle=SUCCESS).pack()

app.mainloop()