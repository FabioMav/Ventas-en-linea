"""Pruebas automatizadas de validador.py con datos pequenos e independientes."""
import os
import shutil
import tempfile
import unittest

from validador import DatosInvalidos, validar

ENCABEZADO = "InvoiceNo,StockCode,Description,InvoiceDate,Quantity,UnitPrice,lote\n"


def _fila_referencia(invoice="565080", fecha="2011-09-01 08:25:00", cantidad="8", precio="1.25"):
    return f"{invoice},20677,PINK POLKADOT BOWL,{fecha},{cantidad},{precio},referencia\n"


def _fila_actual(invoice="570001", fecha="2011-10-01 10:00:00", precio="2.10"):
    return f"{invoice},21212,PACK OF 72 RETROSPOT CAKE CASES,{fecha},12,{precio},control\n"


class TestValidador(unittest.TestCase):
    def setUp(self):
        self.dir_temp = tempfile.mkdtemp()
        self.ruta_referencia = os.path.join(self.dir_temp, "referencia.csv")
        self.ruta_actual = os.path.join(self.dir_temp, "actual.csv")

    def tearDown(self):
        shutil.rmtree(self.dir_temp, ignore_errors=True)

    def _escribir(self, ruta, contenido):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)

    def _validar(self):
        validar(ruta_referencia=self.ruta_referencia, ruta_actual=self.ruta_actual)

    # 1. Archivo valido: no debe lanzar ninguna excepcion.
    def test_archivo_valido_pasa(self):
        self._escribir(self.ruta_referencia, ENCABEZADO + _fila_referencia())
        self._escribir(self.ruta_actual, ENCABEZADO + _fila_actual())
        self._validar()  # no debe lanzar

    # 2. Encabezado faltante.
    def test_encabezado_faltante_falla(self):
        encabezado_incompleto = "InvoiceNo,StockCode,Description,InvoiceDate,Quantity,UnitPrice\n"
        self._escribir(
            self.ruta_referencia,
            encabezado_incompleto + "565080,20677,PINK POLKADOT BOWL,2011-09-01 08:25:00,8,1.25\n",
        )
        self._escribir(self.ruta_actual, ENCABEZADO + _fila_actual())
        with self.assertRaises(DatosInvalidos) as ctx:
            self._validar()
        mensaje = "\n".join(ctx.exception.errores)
        self.assertIn("faltan encabezados", mensaje)
        self.assertIn("lote", mensaje)

    # 3. Fecha imposible (el 31 de noviembre no existe).
    def test_fecha_imposible_falla(self):
        self._escribir(self.ruta_referencia, ENCABEZADO + _fila_referencia())
        self._escribir(
            self.ruta_actual,
            ENCABEZADO + _fila_actual(fecha="2011-11-31 09:00:00"),
        )
        with self.assertRaises(DatosInvalidos) as ctx:
            self._validar()
        mensaje = "\n".join(ctx.exception.errores)
        self.assertIn("InvoiceDate", mensaje)
        self.assertIn("2011-11-31", mensaje)

    # 4. Cantidad no valida (cero no es un entero positivo).
    def test_cantidad_invalida_falla(self):
        self._escribir(self.ruta_referencia, ENCABEZADO + _fila_referencia())
        self._escribir(self.ruta_actual, ENCABEZADO + _fila_actual().replace(",12,", ",0,"))
        with self.assertRaises(DatosInvalidos) as ctx:
            self._validar()
        mensaje = "\n".join(ctx.exception.errores)
        self.assertIn("Quantity", mensaje)

    # 5. Precio negativo.
    def test_precio_negativo_falla(self):
        self._escribir(self.ruta_referencia, ENCABEZADO + _fila_referencia())
        self._escribir(self.ruta_actual, ENCABEZADO + _fila_actual(precio="-2.10"))
        with self.assertRaises(DatosInvalidos) as ctx:
            self._validar()
        mensaje = "\n".join(ctx.exception.errores)
        self.assertIn("UnitPrice", mensaje)
        self.assertIn("mayor que cero", mensaje)

    # 6. Factura repetida: DEBE aceptarse (una factura con varios productos
    # genera varias filas con el mismo InvoiceNo).
    def test_factura_repetida_se_acepta(self):
        self._escribir(self.ruta_referencia, ENCABEZADO + _fila_referencia())
        self._escribir(
            self.ruta_actual,
            ENCABEZADO
            + _fila_actual(invoice="570001")
            + "570001,22423,REGENCY CAKESTAND 3 TIER,2011-10-01 10:00:00,3,12.75,control\n",
        )
        self._validar()  # no debe lanzar

    # Pruebas extra, utiles para la demo en clase.
    def test_descripcion_vacia_falla(self):
        fila = _fila_referencia().replace("PINK POLKADOT BOWL", "")
        self._escribir(self.ruta_referencia, ENCABEZADO + fila)
        self._escribir(self.ruta_actual, ENCABEZADO + _fila_actual())
        with self.assertRaises(DatosInvalidos) as ctx:
            self._validar()
        self.assertIn("Description", "\n".join(ctx.exception.errores))

    def test_mezcla_de_lotes_en_actual_falla(self):
        self._escribir(self.ruta_referencia, ENCABEZADO + _fila_referencia())
        self._escribir(
            self.ruta_actual,
            ENCABEZADO
            + _fila_actual(invoice="570001")
            + "580001,22423,REGENCY CAKESTAND 3 TIER,2011-11-01 10:00:00,3,12.75,nuevo\n",
        )
        with self.assertRaises(DatosInvalidos) as ctx:
            self._validar()
        self.assertIn("mezcla mas de un lote", "\n".join(ctx.exception.errores))

    def test_archivo_sin_filas_falla(self):
        self._escribir(self.ruta_referencia, ENCABEZADO)
        self._escribir(self.ruta_actual, ENCABEZADO + _fila_actual())
        with self.assertRaises(DatosInvalidos) as ctx:
            self._validar()
        self.assertIn("no tiene ninguna fila", "\n".join(ctx.exception.errores))


class TestValidadorContraProyecto(unittest.TestCase):
    """Corre la validacion sobre los CSV reales del proyecto (datos/)."""

    def test_csv_del_proyecto_son_validos(self):
        validar()  # usa datos/referencia.csv y datos/actual.csv por defecto


if __name__ == "__main__":
    unittest.main()
