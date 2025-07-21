import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="Simulador de Escenarios", page_icon="💻", layout="wide")

# Colores corporativos
COLOR_VERDE = "#144C44"
COLOR_NARANJA = "#fb9200"
COLOR_ESTRELLA = "#FFD700"
COLOR_ROJO = "#D33F49"
COLOR_GRIS = "#F2F2F2"
COLOR_TEXTO = "#333333"
COLOR_FONDO = "#FFFFFF"

# -------------------------------
# Función formateo números europeos
# -------------------------------
def format_euro(valor):
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

# -------------------------------
# Función estado de alerta
# -------------------------------
def get_estado(valor_pct, benchmark, tipo="coste", valor_abs=None):
    if benchmark:
        min_bm, max_bm = benchmark
        if tipo == "tarifa" and valor_abs is not None:
            if valor_abs < min_bm:
                return COLOR_NARANJA, "⚠️"
            elif min_bm <= valor_abs <= max_bm:
                return COLOR_VERDE, "✅"
            else:
                return COLOR_ESTRELLA, "⭐"
        elif valor_pct is not None:
            if tipo == "coste":
                if valor_pct < min_bm:
                    return COLOR_ESTRELLA, "⭐"
                elif min_bm <= valor_pct <= max_bm:
                    return COLOR_VERDE, "✅"
                else:
                    return COLOR_NARANJA, "⚠️"
            else:  # márgenes y EBITDA
                if valor_pct > max_bm:
                    return COLOR_ESTRELLA, "⭐"
                elif min_bm <= valor_pct <= max_bm:
                    return COLOR_VERDE, "✅"
                else:
                    return COLOR_NARANJA, "⚠️"
    return COLOR_TEXTO, ""

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tipo="coste", tooltip=None, show_euro=True):
    color, icono = get_estado(valor_pct, benchmark, tipo, valor_abs=valor_abs if tipo == "tarifa" else None)
    if benchmark:
        comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[1]*100)}%</small>" if tipo != "tarifa" else f"<br><small>Benchmark: {int(benchmark[0])}–{int(benchmark[1])} €</small>"
    else:
        comparativa = "<br><small>Sin benchmark definido</small>"

    valor_mostrado = format_euro(valor_abs) if show_euro else f"{int(valor_abs)}"
    porcentaje = f"{round(valor_pct*100,1)}%" if valor_pct is not None else "—"

    html = f"""
    <div class="kpi-card" style="background-color:{COLOR_GRIS}; 
                                  border-left:5px solid {color};
                                  padding:10px; border-radius:8px;
                                  transition: transform 0.2s; position:relative;"
         onmouseover="this.style.transform='scale(1.02)'"
         onmouseout="this.style.transform='scale(1)'"
         title="{tooltip or nombre}">
        <div style="font-size:18px; color:{COLOR_TEXTO};">{nombre} {icono}</div>
        <div style="font-size:26px; font-weight:bold; color:{color};">{valor_mostrado}</div>
        <div style="font-size:14px; color:{COLOR_TEXTO};">{porcentaje} sobre ventas{comparativa}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------
# Leer datos JSON
# -------------------------------
with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

param = data['parametros']
facturacion_total = data['resultados']['facturacion_total']

# Mapeo líneas de negocio → benchmarks
mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# BLOQUES LÍNEAS DE NEGOCIO
# -------------------------------
resultados_lineas = {}

st.title("💻 SIMULADOR DE ESCENARIOS")
st.subheader("📦 Líneas de Negocio")

for linea_nombre, linea in param['lineas_negocio'].items():
    benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])

    with st.expander(f"🔽 {linea_nombre.upper()}", expanded=False):
        st.markdown("Ajusta los parámetros para analizar el impacto en resultados.")

        cols = st.columns(2)

        # Ticket Medio
        ticket_medio = st.slider(f"{linea_nombre} - Ticket Medio (€)", 
                                 min_value=int(linea['ticket_medio'] * 0.5),
                                 max_value=int(linea['ticket_medio'] * 1.5),
                                 value=int(linea['ticket_medio']),
                                 step=1000,
                                 format="%d")
        kpi_card("Ticket Medio", ticket_medio, None,
                 tooltip="Valor medio por proyecto")

        # Unidades
        nuevo_unidades = st.slider(f"{linea_nombre} - Número de Unidades", 
                                   min_value=0, max_value=int(linea['unidades']*2),
                                   value=int(linea['unidades']), step=1)
        kpi_card("Número de Unidades", nuevo_unidades, None,
                 tooltip="Proyectos o ventas", show_euro=False)

        # Cálculos
        facturacion_linea = ticket_medio * nuevo_unidades
        costes_directos_pct = linea['costes_directos_%']
        costes_directos = facturacion_linea * (costes_directos_pct / 100)
        margen_bruto = facturacion_linea - costes_directos

        resultados_lineas[linea_nombre] = {
            "facturacion": facturacion_linea,
            "costes_directos": costes_directos,
            "margen_bruto": margen_bruto
        }

# -------------------------------
# 📦 Costes Fijos
# -------------------------------
st.subheader("🏢 Costes Fijos")
costes_fijos_detalle = {}
for categoria, valor in param['costes_fijos'].items():
    nuevo_valor = st.slider(
        f"{categoria.capitalize()} (€)",
        min_value=0,
        max_value=int(valor * 2),
        value=int(valor),
        step=1000,
        format="%d"
    )
    costes_fijos_detalle[categoria] = nuevo_valor
    porcentaje = nuevo_valor / facturacion_total
    benchmark_categoria = benchmarks['global'].get(categoria.lower())
    kpi_card(categoria.capitalize(), nuevo_valor, porcentaje,
             benchmark=benchmark_categoria,
             tooltip=f"Coste fijo en {categoria}")

# -------------------------------
# 📊 Resultados Globales
# -------------------------------
st.subheader("📊 Resultados Globales")

total_facturacion = sum([v['facturacion'] for v in resultados_lineas.values()])
total_costes_directos = sum([v['costes_directos'] for v in resultados_lineas.values()])
total_costes_fijos = sum(costes_fijos_detalle.values())
total_margen_bruto = total_facturacion - total_costes_directos
total_ebitda = total_margen_bruto - total_costes_fijos

col1, col2, col3, col4, col5 = st.columns(5)
kpi_card("Facturación Total", total_facturacion, 1.0)
kpi_card("Costes Directos", total_costes_directos, total_costes_directos/total_facturacion if total_facturacion else None)
kpi_card("Margen Bruto", total_margen_bruto, total_margen_bruto/total_facturacion if total_facturacion else None)
kpi_card("Costes Fijos", total_costes_fijos, total_costes_fijos/total_facturacion if total_facturacion else None)
kpi_card("EBITDA", total_ebitda, total_ebitda/total_facturacion if total_facturacion else None)

# Tabla resumen
st.markdown("### 📊 Resumen por Línea de Negocio")
resumen_df = pd.DataFrame([
    {
        "Línea": k,
        "Facturación": format_euro(v["facturacion"]),
        "Costes Directos": f"{format_euro(v['costes_directos'])} ({v['costes_directos']/v['facturacion']*100:.1f}%)" if v['facturacion'] else "—",
        "Margen Bruto": f"{format_euro(v['margen_bruto'])} ({v['margen_bruto']/v['facturacion']*100:.1f}%)" if v['facturacion'] else "—"
    }
    for k, v in resultados_lineas.items()
])
st.table(resumen_df)

# -------------------------------
# 📥 Exportar a PDF
# -------------------------------
if st.button("📤 Exportar a PDF"):
    filename = f"Simulador_PyG_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Simulador de Escenarios - Resumen")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    y = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Resultados Globales")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Facturación Total: {format_euro(total_facturacion)}")
    y -= 15
    c.drawString(50, y, f"Costes Directos: {format_euro(total_costes_directos)}")
    y -= 15
    c.drawString(50, y, f"Margen Bruto: {format_euro(total_margen_bruto)}")
    y -= 15
    c.drawString(50, y, f"Costes Fijos: {format_euro(total_costes_fijos)}")
    y -= 15
    c.drawString(50, y, f"EBITDA: {format_euro(total_ebitda)}")

    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Resumen por Línea de Negocio")
    y -= 20

    c.setFont("Helvetica", 12)
    for _, row in resumen_df.iterrows():
        c.drawString(50, y, f"{row['Línea']}: Facturación={row['Facturación']}, "
                            f"Costes Directos={row['Costes Directos']}, "
                            f"Margen Bruto={row['Margen Bruto']}")
        y -= 15
        if y < 100:
            c.showPage()
            y = height - 50

    c.save()
    st.success(f"📥 PDF exportado: {filename}")
