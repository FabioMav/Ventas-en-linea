"""Valida los lotes de ventas antes de publicar el sitio.

Reglas (ver consigna del Trabajo 3 - Unidad 5):
  - El archivo debe poder leerse, tener las siete columnas y al menos una fila.
  - InvoiceNo, StockCode y Description deben tener contenido (no vacios).
  - InvoiceDate debe ser una fecha y hora real con formato
    "AAAA-MM-DD HH:MM:SS" y corresponder al mes/anio del lote.
  - Quantity debe ser un entero positivo.
  - UnitPrice debe ser un numero finito mayor que cero.
  - referencia.csv solo debe contener el lote "referencia".
  - actual.csv solo debe contener el lote "control" o el lote "nuevo"
    (un unico lote, sin mezclar).
  - InvoiceNo PUEDE repetirse (una factura con varios productos genera
    varias filas con el mismo numero) - no se valida unicidad.

Ante cualquier error se identifica archivo, fila y campo cuando corresponde,
se explica el motivo, se acumulan TODOS los errores encontrados y el
programa termina con error (exit code != 0).
"""
import csv
import math
import sys
from datetime import datetime

RUTA_REFERENCIA = "datos/referencia.csv"
RUTA_ACTUAL = "datos/actual.csv"

COLUMNAS_OBLIGATORIAS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "InvoiceDate",
    "Quantity",
    "UnitPrice",
    "lote",
]

COLUMNAS_TEXTO_OBLIGATORIO = ["InvoiceNo", "StockCode", "Description"]

# Mes y anio que le corresponde a cada lote, segun la consigna.
MES_POR_LOTE = {
    "referencia": (2011, 9),
    "control": (2011, 10),
    "nuevo": (2011, 11),
}

LOTES_REFERENCIA = {"referencia"}
LOTES_ACTUAL = {"control", "nuevo"}

FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


class DatosInvalidos(Exception):
    """Agrupa todos los errores de validacion encontrados."""

    def __init__(self, errores):
        self.errores = errores
        super().__init__("\n".join(errores))


def _leer_filas(ruta, errores):
    """Lee el CSV y devuelve (encabezados_ok, lista_de_filas)."""
    try:
        with open(ruta, newline="", encoding="utf-8") as f:
            lector = csv.DictReader(f, restkey="__columnas_de_mas__")
            encabezados = lector.fieldnames
            if encabezados is None:
                errores.append(f"{ruta}: el archivo esta vacio (sin encabezados).")
                return False, []
            faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in encabezados]
            if faltantes:
                errores.append(
                    f"{ruta}: faltan encabezados obligatorios: {', '.join(faltantes)}."
                )
                return False, []
            filas = list(lector)
    except FileNotFoundError:
        errores.append(f"{ruta}: no se encontro el archivo.")
        return False, []

    if not filas:
        errores.append(f"{ruta}: el archivo no tiene ninguna fila de datos.")
        return True, []

    return True, filas


def _validar_fecha(valor, lote_fila, ruta, num_fila, errores):
    try:
        fecha_obj = datetime.strptime(valor, FORMATO_FECHA)
    except (ValueError, TypeError):
        errores.append(
            f"{ruta}, fila {num_fila}, campo 'InvoiceDate': '{valor}' no es una fecha y "
            "hora real con formato AAAA-MM-DD HH:MM:SS."
        )
        return

    esperado = MES_POR_LOTE.get(lote_fila)
    if esperado is not None and (fecha_obj.year, fecha_obj.month) != esperado:
        anio_e, mes_e = esperado
        errores.append(
            f"{ruta}, fila {num_fila}, campo 'InvoiceDate': '{valor}' no corresponde al "
            f"mes/anio del lote '{lote_fila}' (se esperaba {anio_e}-{mes_e:02d})."
        )


def validar_archivo(ruta, lotes_permitidos, errores):
    ok_encabezados, filas = _leer_filas(ruta, errores)
    if not ok_encabezados or not filas:
        return

    lotes_vistos = set()

    for i, fila in enumerate(filas, start=2):  # fila 1 = encabezado
        if fila.get("__columnas_de_mas__"):
            errores.append(f"{ruta}, fila {i}: tiene mas columnas de las esperadas.")

        for campo in COLUMNAS_OBLIGATORIAS:
            if fila.get(campo) is None or fila.get(campo) == "":
                errores.append(f"{ruta}, fila {i}, campo '{campo}': falta el valor.")

        for campo in COLUMNAS_TEXTO_OBLIGATORIO:
            valor = fila.get(campo)
            if valor is not None and valor.strip() == "":
                errores.append(
                    f"{ruta}, fila {i}, campo '{campo}': no puede estar vacio."
                )

        # lote
        lote_fila = fila.get("lote")
        if lote_fila:
            if lote_fila not in lotes_permitidos:
                errores.append(
                    f"{ruta}, fila {i}, campo 'lote': '{lote_fila}' no es valido aqui "
                    f"(se esperaba uno de: {', '.join(sorted(lotes_permitidos))})."
                )
            else:
                lotes_vistos.add(lote_fila)

            if lote_fila in MES_POR_LOTE:
                fecha_valor = fila.get("InvoiceDate")
                if fecha_valor:
                    _validar_fecha(fecha_valor, lote_fila, ruta, i, errores)

        # Quantity: entero positivo
        cantidad = fila.get("Quantity")
        if cantidad:
            try:
                cantidad_num = int(cantidad)
                if cantidad_num <= 0:
                    errores.append(
                        f"{ruta}, fila {i}, campo 'Quantity': '{cantidad}' debe ser un "
                        "entero positivo."
                    )
            except ValueError:
                errores.append(
                    f"{ruta}, fila {i}, campo 'Quantity': '{cantidad}' no es un entero."
                )

        # UnitPrice: numero finito mayor que cero
        precio = fila.get("UnitPrice")
        if precio:
            try:
                precio_num = float(precio)
                if not math.isfinite(precio_num):
                    errores.append(
                        f"{ruta}, fila {i}, campo 'UnitPrice': '{precio}' no es un numero finito."
                    )
                elif precio_num <= 0:
                    errores.append(
                        f"{ruta}, fila {i}, campo 'UnitPrice': '{precio}' debe ser mayor que cero."
                    )
            except ValueError:
                errores.append(
                    f"{ruta}, fila {i}, campo 'UnitPrice': '{precio}' no es un numero."
                )

    if len(lotes_vistos) > 1:
        errores.append(
            f"{ruta}: mezcla mas de un lote ({', '.join(sorted(lotes_vistos))}); "
            "debe contener un unico lote."
        )


def validar(ruta_referencia=RUTA_REFERENCIA, ruta_actual=RUTA_ACTUAL):
    errores = []
    validar_archivo(ruta_referencia, LOTES_REFERENCIA, errores)
    validar_archivo(ruta_actual, LOTES_ACTUAL, errores)
    if errores:
        raise DatosInvalidos(errores)


def main():
    try:
        validar()
    except DatosInvalidos as exc:
        print("Validacion fallida. Se encontraron los siguientes errores:")
        for error in exc.errores:
            print(f"  - {error}")
        sys.exit(1)
    print(f"OK: {RUTA_REFERENCIA} y {RUTA_ACTUAL} son validos.")


if __name__ == "__main__":
    main()
