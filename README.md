# Monitoreo de ventas de una tienda de regalos en línea — CI/CD + Evidently

Trabajo 3 (Unidad de Aprendizaje 5): un sistema que valida lotes de ventas,
compara `Quantity` y `UnitPrice` con **Evidently** contra un mes de
referencia (septiembre de 2011) y publica el informe del último lote
válido en **GitHub Pages**, automatizado con **GitHub Actions**. Aplica el
mismo flujo de la práctica de Ruta Exprés a un dataset público más grande
(Online Retail, UCI).

## El caso

Al cierre de cada mes, el equipo de ventas consulta una página con el
último lote publicado. Si el patrón de cantidades o precios cambia
respecto a septiembre, revisa los productos antes de tomar decisiones de
inventario.

## Fuente y preparación de los lotes

El CSV `datos/ventas_regalos_2011.csv` contiene 36.000 filas de ventas
reales del Reino Unido (fuente: [Online Retail, UCI](https://archive.ics.uci.edu/dataset/352/online+retail)),
12.000 por mes, con una columna `lote` que ya indica a qué grupo pertenece
cada fila (la muestra excluye cancelaciones y líneas con cantidad o precio
no positivos):

| Mes | Lote | Archivo | Filas | Función |
|---|---|---|---|---|
| Septiembre 2011 | `referencia` | `datos/referencia.csv` | 12.000 | Fijo durante todas las pruebas |
| Octubre 2011 | `control` | `datos/control.csv` | 12.000 | `actual.csv` = copia de este (primera publicación) |
| Noviembre 2011 | `nuevo` | `datos/nuevo.csv` | 12.000 | `actual.csv` = copia de este (actualización válida) |

`preparar_datos.py` hace esta división una sola vez (ya está corrida; los
cuatro CSV de `datos/` ya existen en esta entrega):

```bash
python preparar_datos.py
```

GitHub Actions lee del commit únicamente los dos archivos que se comparan:
`referencia.csv` (septiembre, fijo) y `actual.csv` (octubre o noviembre,
según qué se haya publicado por última vez).

## Reglas de validación (`validador.py`)

Se valida **completo** `datos/referencia.csv` y `datos/actual.csv` (no una
muestra). Un archivo es inválido si:

- No se puede leer, le faltan columnas obligatorias, o no tiene ninguna
  fila de datos (debe tener las siete: `InvoiceNo, StockCode, Description,
  InvoiceDate, Quantity, UnitPrice, lote`).
- `InvoiceNo`, `StockCode` o `Description` están vacíos.
- `InvoiceDate` no es una fecha y hora real con formato
  `AAAA-MM-DD HH:MM:SS` (por ejemplo, `2011-11-31 09:00:00` no existe: 31
  de noviembre no es un día válido), o no corresponde al mes/año que le
  toca a su lote (septiembre para `referencia`, octubre para `control`,
  noviembre para `nuevo`).
- `Quantity` no es un entero positivo.
- `UnitPrice` no es un número finito mayor que cero.
- `referencia.csv` trae un lote distinto de `referencia`.
- `actual.csv` mezcla `control` y `nuevo` en el mismo archivo, o trae un
  valor de lote que no es ninguno de los dos.

**`InvoiceNo` puede repetirse** a propósito: una factura con varios
productos genera varias filas con el mismo número, así que no se valida
unicidad sobre esa columna.

Ante cualquier error se identifica el archivo, la fila y el campo, se
explica el motivo, se juntan **todos** los errores encontrados (no se
corta en el primero) y el programa termina con código de salida distinto
de cero — así, en CI, el job falla y la publicación queda bloqueada.

```bash
python validador.py
```

### Pruebas automatizadas (`test_validador.py`)

Diez pruebas con datos chicos e independientes, más una que corre la
validación contra los CSV del proyecto:

- archivo válido (pasa)
- encabezado faltante (falla)
- fecha imposible — 31 de noviembre (falla)
- cantidad no válida — cero (falla)
- precio negativo (falla)
- **factura repetida — debe aceptarse** (pasa)
- descripción vacía (falla)
- mezcla de lotes en `actual.csv` (falla)
- archivo sin filas de datos (falla)
- validación contra `datos/referencia.csv` y `datos/actual.csv` reales (pasa)

```bash
python -m unittest discover -v
```

## El informe de Evidently (`generar_informe.py`)

Compara `Quantity` y `UnitPrice` de `actual.csv` contra `referencia.csv`
(septiembre), cada columna por separado, con la **misma configuración** en
las dos ejecuciones: `DataDriftPreset(columns=["Quantity", "UnitPrice"],
drift_share=0.5, num_threshold=0.05)`. Evidently eligió automáticamente la
distancia de Wasserstein normalizada como método: una columna se marca con
drift cuando esa distancia supera 0.05, y el dataset completo se marca con
drift cuando la proporción de columnas con drift alcanza 0.5 (con 2
columnas, basta con que 1 de las 2 tenga drift).

Resultados reales obtenidos en esta entrega:

| Comparación | Mediana unidades (ref. / actual) | Mediana precio (ref. / actual) | Distancia Wasserstein (cantidad / precio) | ¿Drift? |
|---|---|---|---|---|
| Septiembre vs. Octubre | 4 / 3 u. | £2.08 / £2.08 | 0.033 / 0.054 | Sí, en precio (1 de 2 columnas, share 0.5 — justo en el límite) |
| Septiembre vs. Noviembre | 4 / 3 u. | £2.08 / £2.08 | 0.061 / 0.051 | Sí, en las dos columnas (share 1.0) |

Esto vale la pena explicarlo en el informe tal como pide la consigna
("explica lo que observas aunque el resultado difiera de tu expectativa"):
las medianas se ven casi iguales a simple vista, pero Evidently mide la
distribución **completa**, no solo la mediana — y ahí sí detecta un
cambio real en cómo se reparten las cantidades y los precios entre
septiembre y los meses siguientes, aunque el valor típico (la mediana) casi
no se mueva.

```bash
python generar_informe.py
```

Genera `public/index.html` (la portada) y
`public/informe_septiembre_vs_<mes>.html` (el informe completo de
Evidently). La portada muestra el último mes publicado, las filas
analizadas, la mediana de unidades por fila, la mediana de precio unitario
(en libras esterlinas), la fecha de generación, el commit, el autor, la
fuente, dos gráficos pequeños (cantidad y precio tienen escalas distintas,
así que cada uno tiene su propio eje) y un botón "Comparar `<mes>` con
septiembre" que enlaza al informe correspondiente.

## Estructura del repositorio

```
ventas-cicd/
├── datos/
│   ├── ventas_regalos_2011.csv   (CSV original, no tocar)
│   ├── referencia.csv             (septiembre — fijo)
│   ├── control.csv                 (octubre)
│   ├── nuevo.csv                    (noviembre)
│   └── actual.csv                  (el lote publicado ahora: copia de control.csv o nuevo.csv)
├── preparar_datos.py
├── validador.py
├── test_validador.py
├── generar_informe.py
├── requirements.txt
├── .gitignore
├── githooks/post-commit
├── .github/workflows/ventas-cicd.yml
└── README.md
```

## Instalación y ejecución local

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate        # macOS / Linux

pip install -r requirements.txt

python -m unittest discover -v     # pruebas
python validador.py                 # validacion
python generar_informe.py           # portada + informe (queda en public/)
```

Abrí `public/index.html` en el navegador para ver la portada publicada.

## Credenciales y archivos temporales

Este proyecto no usa ninguna clave ni contraseña: GitHub Actions se
autentica contra GitHub Pages con un token temporal que genera automática­
mente (`permissions: pages: write, id-token: write`), nunca con un secreto
guardado a mano. El `.gitignore` excluye el entorno virtual (`.venv/`), la
carpeta generada (`public/`), el caché de Python (`__pycache__/`) y,
preventivamente, cualquier archivo `.env` o `*.key` que llegara a crearse.

## Git hook opcional (push automático tras cada commit)

```bash
git config core.hooksPath githooks
```

## CI/CD (`.github/workflows/ventas-cicd.yml`)

- **`ci`**: en cada push a `main`, instala dependencias, corre las pruebas,
  valida `referencia.csv` y `actual.csv`, y si todo pasa genera
  `public/index.html` y el informe de Evidently, subiendo esa carpeta como
  artefacto de GitHub Pages.
- **`cd`** (`needs: ci`): publica ese artefacto en GitHub Pages. Si `ci`
  falla (por ejemplo, una fecha imposible), `cd` **no se ejecuta** y GitHub
  Pages conserva automáticamente el sitio del último commit que sí pasó.

## Pasos para crear el repositorio y publicarlo

1. Creá un repositorio público nuevo en GitHub (por ejemplo `ventas-cicd`).
2. En esta carpeta:
   ```bash
   git init
   git add .
   git commit -m "Primera version: monitoreo de ventas de regalos en linea"
   git branch -M main
   git remote add origin https://github.com/<tu-usuario>/ventas-cicd.git
   git push -u origin main
   ```
3. En GitHub: **Settings → Pages → Source → GitHub Actions**, antes de que
   corra el primer workflow.
4. Pestaña **Actions**: `ci` y después `cd` en verde, y el sitio queda en
   `https://<tu-usuario>.github.io/ventas-cicd/`.

## Identificar la última versión publicada y recuperar una válida

La última versión publicada es la que muestra la portada en GitHub Pages
(el commit aparece al pie de `index.html`), y coincide con la última
ejecución en Actions donde `ci` **y** `cd` terminaron en verde. Para
recuperar una versión válida después de un error: corregís el dato que
causó el fallo (o restaurás el valor original), hacés commit y push de
nuevo — el flujo vuelve a correr completo y, si pasa, `cd` publica esa
nueva versión. Mientras tanto, como `cd` nunca llegó a ejecutarse con el
dato malo, Pages nunca mostró nada incorrecto: siguió sirviendo la última
versión válida todo ese tiempo.

## Los cuatro escenarios de la demostración

Hacé un commit y push por escenario, anotando antes qué esperás que pase,
y guardá el enlace de Actions y las capturas de cada uno.

### 1. Primera publicación (ya viene lista en esta entrega)

`datos/actual.csv` ya es una copia de `control.csv` (octubre).

```bash
git add .
git commit -m "Primera publicacion: octubre 2011 vs septiembre"
git push
```

Verificá: la portada muestra **Octubre 2011**, y el informe
(`informe_septiembre_vs_octubre.html`) lo compara con septiembre — en
nuestra prueba local, con drift en precio (`UnitPrice`, justo en el límite
del umbral) pero no en cantidad.

### 2. Actualización válida (noviembre)

```powershell
copy datos\nuevo.csv datos\actual.csv     # Windows
# cp datos/nuevo.csv datos/actual.csv      # macOS / Linux

git add datos/actual.csv
git commit -m "Actualizacion: noviembre 2011 vs septiembre"
git push
```

Verificá: la portada muestra **Noviembre 2011** con un commit nuevo, y el
informe (`informe_septiembre_vs_noviembre.html`) — en nuestra prueba
local, con drift en las dos columnas.

### 3. Error controlado

Abrí `datos/actual.csv`, elegí cualquier fila y anotá su `InvoiceDate`
original. Cambiala por una fecha imposible (por ejemplo
`2011-11-31 09:00:00`, que no existe) y subí el cambio a propósito:

```bash
git add datos/actual.csv
git commit -m "Error intencional: fecha imposible"
git push
```

Verificá: `ci` falla en el paso "Validar referencia.csv y actual.csv"
señalando exactamente el archivo, la fila y el campo (`InvoiceDate`); `cd`
queda omitido; y GitHub Pages sigue mostrando la última versión válida
(noviembre, del escenario 2). (Confirmado localmente: con esa fecha,
`validador.py` termina con código de salida 1 y el mensaje identifica el
archivo, la fila y el campo exactos.)

### 4. Recuperación

Restaurá la fecha original que anotaste:

```bash
git add datos/actual.csv
git commit -m "Correccion: fecha restaurada"
git push
```

Verificá: `ci` y `cd` vuelven a quedar en verde, y la portada vuelve a
publicar noviembre, ahora con este nuevo commit.

## Evidencias a entregar (PDF único, por Teams)

Según la consigna, el PDF final debe incluir: portada y enlaces, la
propuesta (objetivo, a quién sirve, backlog con criterios de aceptación,
diagrama push→Pages, qué bloquea vs. qué es una señal de monitoreo),
preparación de los datos (tabla mes/archivo/filas/función), implementación
de CI/CD (estructura, workflow, captura de una ejecución exitosa),
monitoreo con Evidently (capturas de octubre y noviembre frente a
septiembre, qué observás en cada una), pruebas y resultados (captura de
las pruebas locales + tabla de los 4 escenarios), evidencias de
publicación y recuperación (portadas, error con CD omitido, sitio que
conserva la última versión válida, recuperación) y una conclusión breve.
También los enlaces al repositorio público y a GitHub Pages, verificando
que abran, dejando `main` con datos válidos al final.
