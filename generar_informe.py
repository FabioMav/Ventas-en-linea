"""Genera el sitio publicado en GitHub Pages: la portada (index.html) y el
informe de Evidently que compara Quantity y UnitPrice del lote actual con
septiembre (referencia).

Se ejecuta despues de que validador.py confirmo que referencia.csv y
actual.csv son validos. Si actual.csv trae el lote "control" (octubre) o
"nuevo" (noviembre), el nombre del informe generado identifica ambos meses
("informe_septiembre_vs_octubre.html" / "informe_septiembre_vs_noviembre.html"),
para que la portada enlace al informe correcto con una etiqueta del tipo
"Comparar octubre con septiembre".
"""
import html
import os
from datetime import datetime, timezone

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

RUTA_REFERENCIA = "datos/referencia.csv"
RUTA_ACTUAL = "datos/actual.csv"
CARPETA_SITIO = "public"

COLUMNAS_COMPARAR = ["Quantity", "UnitPrice"]

MESES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre",
    12: "diciembre",
}

AUTOR = "Fabio Mavric"
FUENTE = "Online Retail (UCI) — ventas reales de una tienda de regalos en linea del Reino Unido"


def _mes_de(ruta_csv):
    fecha = pd.read_csv(ruta_csv, usecols=["InvoiceDate"])["InvoiceDate"].iloc[0]
    anio, mes = (int(p) for p in fecha.split(" ")[0].split("-")[:2])
    return anio, mes


def _slug_mes(mes):
    return MESES[mes]


def resumen_lote(ruta_csv):
    df = pd.read_csv(ruta_csv)
    return {
        "n": len(df),
        "mediana_cantidad": df["Quantity"].median(),
        "mediana_precio": df["UnitPrice"].median(),
    }


def calcular_drift(ruta_referencia, ruta_actual):
    ref = pd.read_csv(ruta_referencia, usecols=COLUMNAS_COMPARAR)
    act = pd.read_csv(ruta_actual, usecols=COLUMNAS_COMPARAR)
    reporte = Report(
        metrics=[DataDriftPreset(columns=COLUMNAS_COMPARAR, drift_share=0.5, num_threshold=0.05)]
    )
    snapshot = reporte.run(current_data=act, reference_data=ref)
    return snapshot


def _grafico_metrica(titulo, unidad, v_ref, v_act, etiqueta_ref, etiqueta_act, formato):
    """SVG de dos barras (referencia vs. actual) para UNA sola metrica, con
    su propia escala. Quantity y UnitPrice tienen unidades distintas, asi
    que cada una recibe su propio mini-grafico en vez de compartir un eje.
    """
    ancho, alto_plot, alto_etiquetas = 200, 110, 20
    alto_total = alto_plot + alto_etiquetas
    base_y = alto_plot - 6
    max_valor = max(v_ref, v_act, 0.0001) * 1.25
    escala = (alto_plot - 24) / max_valor

    ancho_barra, separacion = 46, 18
    centro = ancho / 2
    x_ref = centro - separacion / 2 - ancho_barra
    x_act = centro + separacion / 2

    piezas = [f'<line x1="8" y1="{base_y}" x2="{ancho - 8}" y2="{base_y}" class="linea-base" />']
    for x, valor, serie, etiqueta in (
        (x_ref, v_ref, "serie-1", etiqueta_ref),
        (x_act, v_act, "serie-2", etiqueta_act),
    ):
        alto_barra = max(valor * escala, 2)
        y = base_y - alto_barra
        piezas.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho_barra}" height="{alto_barra:.1f}" '
            f'rx="4" class="barra {serie}"><title>{html.escape(etiqueta)}: {formato.format(valor)}</title></rect>'
        )
        piezas.append(
            f'<text x="{x + ancho_barra / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" '
            f'class="valor-barra">{formato.format(valor)}</text>'
        )

    svg_interior = "\n    ".join(piezas)
    return f"""<div class="mini-grafico">
    <p class="mini-titulo">{html.escape(titulo)}</p>
    <svg viewBox="0 0 {ancho} {alto_total}" role="img"
      aria-label="{html.escape(titulo)}: {html.escape(etiqueta_ref)} {formato.format(v_ref)} {unidad}, {html.escape(etiqueta_act)} {formato.format(v_act)} {unidad}">
      {svg_interior}
    </svg>
  </div>"""


def generar_portada(
    anio_actual,
    mes_actual,
    resumen_referencia,
    resumen_actual,
    nombre_informe,
    commit,
    fecha_generacion,
):
    mes_nombre = _slug_mes(mes_actual).capitalize()
    titulo_mes = f"{mes_nombre} {anio_actual}"
    etiqueta_ref = "Septiembre (referencia)"
    etiqueta_act = f"{mes_nombre} (publicado)"

    grafico_cantidad = _grafico_metrica(
        "Mediana de unidades por fila", "u.",
        resumen_referencia["mediana_cantidad"], resumen_actual["mediana_cantidad"],
        etiqueta_ref, etiqueta_act, "{:.0f}",
    )
    grafico_precio = _grafico_metrica(
        "Mediana de precio unitario", "GBP",
        resumen_referencia["mediana_precio"], resumen_actual["mediana_precio"],
        etiqueta_ref, etiqueta_act, "£{:.2f}",
    )

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitoreo de ventas de regalos en linea</title>
<style>
:root {{
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #33322f;
  --ink-muted: #6b6b66; --border: rgba(11,11,11,0.10); --series-1: #2a78d6;
  --series-2: #eb6834; --series-3: #1baf7a;
  --tint-1: rgba(42,120,214,0.08); --tint-3: rgba(27,175,122,0.08);
  --grid: #e1e0d9; --baseline: #c3c2b7;
  --header-start: #184f95; --header-end: #256abf; --header-ink: #ffffff;
  --header-ink-muted: rgba(255,255,255,0.82);
  --shadow: 0 1px 2px rgba(11,11,11,0.06), 0 8px 24px rgba(11,11,11,0.05);
}}
:root:where(:not([data-theme="light"])) {{
  @media (prefers-color-scheme: dark) {{
    --page: #0d0d0d; --surface: #1a1a19; --ink: #f0efec; --ink-2: #d7d5cf;
    --ink-muted: #9a988f; --border: rgba(255,255,255,0.10); --series-1: #3987e5;
    --series-2: #d95926; --series-3: #199e70;
    --tint-1: rgba(57,135,229,0.14); --tint-3: rgba(25,158,112,0.14);
    --grid: #2c2c2a; --baseline: #383835;
    --header-start: #0d366b; --header-end: #256abf; --header-ink: #ffffff;
    --header-ink-muted: rgba(255,255,255,0.80);
    --shadow: 0 1px 2px rgba(0,0,0,0.3), 0 8px 24px rgba(0,0,0,0.3);
  }}
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--page); color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
  padding: 32px 16px;
}}
main {{
  max-width: 880px; margin: 0 auto; background: var(--surface);
  border: 1px solid var(--border); border-radius: 16px; box-shadow: var(--shadow);
  overflow: hidden;
}}
.banda-header {{
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, var(--header-start), var(--header-end));
  color: var(--header-ink);
  padding: 30px clamp(20px, 5vw, 48px) 26px;
}}
.banda-header::before {{
  content: ""; position: absolute; inset: 0;
  background:
    radial-gradient(520px 220px at 88% -20%, rgba(255,255,255,0.20), transparent 60%),
    radial-gradient(360px 200px at 102% 115%, rgba(255,255,255,0.12), transparent 65%);
  pointer-events: none;
}}
.banda-header > * {{ position: relative; }}
.banda-header h1 {{ font-size: 1.5rem; margin: 0 0 6px; letter-spacing: -0.01em; }}
.banda-header .subtitulo {{ color: var(--header-ink-muted); margin: 0; font-size: 0.95rem; }}
.banda-header .subtitulo strong {{ color: var(--header-ink); }}
.contenido {{ padding: 28px clamp(20px, 5vw, 48px) 32px; }}
.indicadores {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; margin: 24px 0;
}}
.indicador {{ background: var(--tint-1); border-radius: 12px; padding: 14px 16px; }}
.indicador .valor {{ font-size: 1.4rem; font-weight: 700; font-variant-numeric: tabular-nums; }}
.indicador .etiqueta {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-muted); }}
.meta {{ color: var(--ink-muted); font-size: 0.9rem; line-height: 1.7; margin-top: 24px; }}
.meta code {{ background: var(--tint-1); padding: 1px 6px; border-radius: 4px; }}
a.boton {{
  display: inline-block; margin-top: 20px; padding: 11px 20px; border-radius: 10px;
  background: linear-gradient(135deg, var(--header-start), var(--header-end));
  color: white; text-decoration: none; font-weight: 600;
  box-shadow: 0 4px 14px rgba(37,106,191,0.35);
}}
.grafico-seccion {{ margin: 28px 0 8px; }}
.grafico-seccion h2 {{ font-size: 1rem; margin: 0 0 14px; color: var(--ink-2); }}
.graficos-fila {{ display: flex; gap: 28px; flex-wrap: wrap; }}
.mini-grafico {{ flex: 1 1 200px; max-width: 220px; }}
.mini-titulo {{ font-size: 0.82rem; color: var(--ink-muted); margin: 0 0 4px; }}
.mini-grafico svg {{ width: 100%; height: auto; display: block; }}
.linea-base {{ stroke: var(--baseline); stroke-width: 1; }}
.barra.serie-1 {{ fill: var(--series-1); }}
.barra.serie-2 {{ fill: var(--series-2); }}
.valor-barra {{ font-size: 12px; fill: var(--ink-2); font-variant-numeric: tabular-nums; }}
.leyenda {{ display: flex; gap: 18px; margin-top: 14px; font-size: 0.82rem; color: var(--ink-2); }}
.leyenda-item {{ display: inline-flex; align-items: center; gap: 6px; }}
.leyenda-item .punto {{ width: 10px; height: 10px; border-radius: 3px; }}
</style>
</head>
<body>
<main>
  <div class="banda-header">
    <h1>Monitoreo de ventas &mdash; tienda de regalos en linea</h1>
    <p class="subtitulo">Ultimo lote publicado: <strong>{html.escape(titulo_mes)}</strong></p>
  </div>

  <div class="contenido">
    <div class="indicadores">
      <div class="indicador">
        <div class="valor">{resumen_actual['n']:,}</div>
        <div class="etiqueta">Filas analizadas</div>
      </div>
      <div class="indicador">
        <div class="valor">{resumen_actual['mediana_cantidad']:.0f} u.</div>
        <div class="etiqueta">Mediana unidades por fila</div>
      </div>
      <div class="indicador">
        <div class="valor">&pound;{resumen_actual['mediana_precio']:.2f}</div>
        <div class="etiqueta">Mediana precio unitario</div>
      </div>
    </div>

    <div class="grafico-seccion">
      <h2>Septiembre vs. {html.escape(mes_nombre)}</h2>
      <div class="graficos-fila">
        {grafico_cantidad}
        {grafico_precio}
      </div>
      <div class="leyenda">
        <span class="leyenda-item"><span class="punto" style="background: var(--series-1)"></span>{html.escape(etiqueta_ref)}</span>
        <span class="leyenda-item"><span class="punto" style="background: var(--series-2)"></span>{html.escape(etiqueta_act)}</span>
      </div>
    </div>

    <a class="boton" href="{html.escape(nombre_informe)}">Comparar {_slug_mes(mes_actual)} con septiembre</a>

    <p class="meta">
      autor <strong>{html.escape(AUTOR)}</strong> &middot;
      fuente {html.escape(FUENTE)} &middot;
      generado el {fecha_generacion} &middot;
      commit <code>{html.escape(commit)}</code>
    </p>
  </div>
</main>
</body>
</html>
"""


def main():
    os.makedirs(CARPETA_SITIO, exist_ok=True)

    anio_actual, mes_actual = _mes_de(RUTA_ACTUAL)
    resumen_referencia = resumen_lote(RUTA_REFERENCIA)
    resumen_actual = resumen_lote(RUTA_ACTUAL)

    nombre_informe = f"informe_septiembre_vs_{_slug_mes(mes_actual)}.html"
    ruta_informe = os.path.join(CARPETA_SITIO, nombre_informe)

    snapshot = calcular_drift(RUTA_REFERENCIA, RUTA_ACTUAL)
    snapshot.save_html(ruta_informe)

    commit = os.environ.get("GITHUB_SHA", "local")[:7] if os.environ.get("GITHUB_SHA") else "local"
    fecha_generacion = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    portada = generar_portada(
        anio_actual=anio_actual,
        mes_actual=mes_actual,
        resumen_referencia=resumen_referencia,
        resumen_actual=resumen_actual,
        nombre_informe=nombre_informe,
        commit=commit,
        fecha_generacion=fecha_generacion,
    )
    with open(os.path.join(CARPETA_SITIO, "index.html"), "w", encoding="utf-8") as f:
        f.write(portada)

    print(f"OK: {CARPETA_SITIO}/index.html generado (lote: {_slug_mes(mes_actual)} {anio_actual}).")
    print(f"OK: {ruta_informe} generado (comparacion septiembre vs. {_slug_mes(mes_actual)}).")


if __name__ == "__main__":
    main()
