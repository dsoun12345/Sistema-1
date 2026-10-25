# config.py
# Ajustes del negocio (Perú). Aquí van datos, no estilos (esos están en estilos.py).

MONEDA = "S/"
IGV = 0.18   # 18 %

# True  -> los precios de costo y venta ya incluyen IGV (lo normal en Perú:
#          Régimen General, RMT o RER).
# False -> el negocio no cobra IGV (p. ej. Nuevo RUS): la ganancia es la misma.
PRECIOS_INCLUYEN_IGV = True


def soles(monto):
    """3.5 -> 'S/ 3.50'"""
    return f"{MONEDA} {float(monto or 0):,.2f}"


def calcular_margen(costo, venta):
    """Rentabilidad de un producto. Devuelve un dict con:
    ganancia          -> venta - costo (por unidad)
    ganancia_sin_igv  -> lo que queda para el negocio después de pagar el IGV
    margen            -> % sobre el precio de venta   (ganancia / venta)
    sobre_costo       -> % sobre el costo, el "le gano X%"   (ganancia / costo)
    margen y sobre_costo son None si no se pueden calcular (venta o costo en 0)."""
    costo, venta = float(costo or 0), float(venta or 0)
    ganancia = venta - costo
    # con IGV incluido, a SUNAT se le paga el IGV de la diferencia
    sin_igv = ganancia / (1 + IGV) if PRECIOS_INCLUYEN_IGV else ganancia
    return {
        "ganancia": ganancia,
        "ganancia_sin_igv": sin_igv,
        "margen": ganancia / venta * 100 if venta > 0 else None,
        "sobre_costo": ganancia / costo * 100 if costo > 0 else None,
    }


def porcentaje(valor):
    return "-" if valor is None else f"{valor:.1f}%"
