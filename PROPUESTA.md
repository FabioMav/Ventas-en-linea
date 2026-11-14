# Propuesta (sección 2 del informe PDF)

> Pensado para pegarse casi tal cual como primera sección de contenido del
> PDF. Ajustalo con tus propias palabras si querés.

## Objetivo, a quién serviría y qué decisión apoya

El objetivo es que el equipo de ventas de la tienda de regalos en línea
tenga, al cierre de cada mes, una página que le diga de un vistazo si el
patrón de cantidades vendidas por línea de factura (`Quantity`) o de
precios unitarios (`UnitPrice`) cambió respecto a septiembre (el mes de
referencia). Lo consultaría el equipo de ventas o de inventario: si
Evidently marca un cambio de distribución importante, revisan qué
productos están detrás de ese cambio antes de decidir reposición de stock,
ajustes de precio o promociones. Si no hay cambios relevantes, no hace
falta ninguna acción.

## Backlog breve (tareas priorizadas, entregas, criterios de aceptación)

1. **Preparar los lotes** — Entrega: `datos/referencia.csv`,
   `datos/control.csv`, `datos/nuevo.csv` con 12.000 filas cada uno y las
   siete columnas originales. Criterio de aceptación: los tres archivos
   pasan una revisión manual de conteo de filas y encabezados.
2. **Validador y pruebas** — Entrega: `validador.py` +
   `test_validador.py`. Criterio de aceptación: al menos seis pruebas
   automatizadas pasan, y el validador corre sin errores contra los CSV
   reales del proyecto.
3. **Informe de Evidently y portada** — Entrega: `generar_informe.py`.
   Criterio de aceptación: genera `index.html` con los datos pedidos
   (mes, filas, medianas, autor, fuente, fecha, commit) y un informe HTML
   de Evidently que compara `Quantity` y `UnitPrice`.
4. **Workflow de CI/CD** — Entrega: `.github/workflows/ventas-cicd.yml`.
   Criterio de aceptación: un push con datos válidos deja `ci` y `cd` en
   verde y publica el sitio; un push con datos inválidos deja `ci` en rojo
   y `cd` sin ejecutarse.
5. **Demostración de los cuatro escenarios** — Entrega: commits, capturas
   y enlaces de Actions de cada uno. Criterio de aceptación: los cuatro
   escenarios se comportan exactamente como se describe en la consigna.
6. **Documentación** — Entrega: README.md + informe PDF final.

## Diagrama: del push a la publicación

```
git push a main
      │
      ▼
┌─────────────┐   falla   ┌────────────────────────────┐
│   job: ci   │ ────────▶ │ cd NO se ejecuta.          │
│ valida      │           │ GitHub Pages conserva el   │
│ referencia  │           │ ultimo sitio valido.       │
│ y actual,   │           └────────────────────────────┘
│ corre       │
│ pruebas,    │
│ compara con │
│ Evidently,  │
│ genera HTML │
└──────┬──────┘
       │ pasa
       ▼
┌─────────────┐
│   job: cd   │  publica el artefacto de ESTA ejecucion
│ (needs: ci) │  en GitHub Pages
└─────────────┘
```

Qué revisa cada parte: **CI** valida que `referencia.csv` y `actual.csv`
sean estructuralmente correctos (columnas, fechas reales, cantidades y
precios válidos) y corre las pruebas automatizadas. **Evidently** compara
las distribuciones completas de `Quantity` y `UnitPrice` del mes publicado
contra septiembre — esto nunca bloquea nada, es solo una señal. **CD**
publica en GitHub Pages el artefacto que generó esa misma ejecución de
`ci`, y solo si `ci` terminó bien.

## Qué bloquea la publicación vs. qué es una señal de monitoreo

- **Bloquea la publicación**: cualquier error que detecta `validador.py`
  (un encabezado faltante, una fecha imposible, una cantidad o un precio
  inválido, una mezcla de lotes). Esto hace fallar `ci`, `cd` queda
  omitido y Pages conserva la última versión válida.
- **Es una señal de monitoreo, no un bloqueo**: que Evidently detecte
  drift en `Quantity` o `UnitPrice`. El dato es válido, así que el sitio
  se publica igual — pero el equipo de ventas sabe que vale la pena mirar
  con más detalle qué productos o qué rango de precios está cambiando.

## Cuándo revisaría los informes y quién atendería una señal

El equipo de ventas revisaría el informe de Evidently cada vez que se
publica un mes nuevo (en la práctica, con cada push a `main`). Atendería
la señal quien haga de analista de datos del equipo: si el informe marca
drift en `UnitPrice`, por ejemplo, revisaría si hubo una promoción, un
cambio de proveedor o una temporada (como noviembre, que suele traer
compras de fin de año) que explique el cambio.

## Cómo identificar la última versión publicada y recuperar una válida

La última versión publicada es la que muestra la portada en GitHub Pages
(el commit aparece al pie de la página), y coincide con la última
ejecución de Actions donde `ci` y `cd` terminaron en verde. Para
recuperar una versión válida: se corrige el dato que causó el error (o se
restaura el valor original), se hace commit y push, y el flujo corre de
nuevo completo — si pasa, `cd` publica esa versión corregida. Como `cd`
nunca llegó a ejecutarse mientras el dato estaba mal, el sitio nunca
mostró información incorrecta: siguió sirviendo la última versión válida
durante todo ese tiempo.

## Credenciales y archivos temporales fuera del repositorio

El repositorio no necesita ninguna contraseña ni clave: GitHub Actions se
autentica contra GitHub Pages con un token temporal (OIDC) que genera
automáticamente en cada ejecución, declarado en el workflow como
`permissions: pages: write, id-token: write` — nunca se guarda un secreto
a mano. El archivo `.gitignore` excluye el entorno virtual (`.venv/`), la
carpeta generada en cada build (`public/`), el caché de Python
(`__pycache__/`) y, preventivamente, cualquier archivo `.env` o `*.key`
que llegara a crearse por error.
