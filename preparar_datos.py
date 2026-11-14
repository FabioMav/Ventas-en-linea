"""Divide el CSV maestro de ventas en los lotes del proyecto.

Lee datos/ventas_regalos_2011.csv (36000 filas, columna 'lote' con valores
referencia/control/nuevo) y exporta cada lote a su propio archivo con las
mismas siete columnas, coma como separador y punto decimal.

Tambien crea datos/actual.csv como copia de control.csv (primera
publicacion = octubre), tal como pide la consigna.
"""
import csv
import shutil

ORIGEN = "datos/ventas_regalos_2011.csv"
ENCABEZADOS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "InvoiceDate",
    "Quantity",
    "UnitPrice",
    "lote",
]
LOTES = ["referencia", "control", "nuevo"]
ARCHIVO_POR_LOTE = {
    "referencia": "datos/referencia.csv",
    "control": "datos/control.csv",
    "nuevo": "datos/nuevo.csv",
}


def main():
    filas_por_lote = {lote: [] for lote in LOTES}

    with open(ORIGEN, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        if lector.fieldnames != ENCABEZADOS:
            raise SystemExit(
                f"Encabezados inesperados en {ORIGEN}: {lector.fieldnames}"
            )
        for fila in lector:
            lote = fila["lote"]
            if lote not in filas_por_lote:
                raise SystemExit(f"Lote desconocido en {ORIGEN}: {lote!r}")
            filas_por_lote[lote].append(fila)

    for lote in LOTES:
        filas = filas_por_lote[lote]
        destino = ARCHIVO_POR_LOTE[lote]
        with open(destino, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=ENCABEZADOS)
            escritor.writeheader()
            escritor.writerows(filas)
        print(f"OK: {destino} generado con {len(filas)} filas (lote={lote}).")

    # Primera publicacion: actual.csv = copia de control.csv (octubre)
    shutil.copyfile(ARCHIVO_POR_LOTE["control"], "datos/actual.csv")
    print("OK: datos/actual.csv creado como copia de control.csv (octubre).")


if __name__ == "__main__":
    main()
