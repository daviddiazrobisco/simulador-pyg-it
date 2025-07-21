import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="Simulador de Escenarios", page_icon="💻", layout="wide")

COLOR_VERDE = "#144C44"
COLOR_NARANJA = "#fb9200"
COLOR_ESTRELLA = "#FFD700"
COLOR_ROJO = "#D33F49"
COLOR_GRIS = "#F2F2F2"
COLOR_TEXTO = "#333333"
COLOR_FONDO = "#FFFFFF"

# -------------------------------
# Funciones utilitarias
# -------------------------------
def format_euro(valor):
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

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
result = data['resultados']
facturacion_total = result['facturacion_total']

mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# BLOQUES LÍNEAS DE NEGOCIO
# -------------------------------
st.title("💻 SIMULADOR DE ESCENARIOS")
st.subheader("📦 Líneas de Negocio")
resultados_lineas = {}

for linea_nombre, linea in param['lineas_negocio'].items():
    benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])

    with st.expander(f"🔽 {linea_nombre.upper()}", expanded=False):
        st.markdown("Ajusta los parámetros para analizar el impacto en resultados.")

        # Sliders + KPIs
        cols = st.columns(4)

        # Tarifa / Ticket Medio
        if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
            with cols[0]:
                nueva_tarifa = st.slider("Tarifa (€)", int(linea['tarifa']*0.8), int(linea['tarifa']*1.2), int(linea['tarifa']), 10, format="%d")
                bm_tarifa = benchmark_linea['precio_jornada'] if benchmark_linea else None
                kpi_card("Tarifa", nueva_tarifa, None, benchmark=(bm_tarifa[0], bm_tarifa[2]) if bm_tarifa else None, tipo="tarifa", tooltip="Precio medio jornada")
            with cols[1]:
                jornadas_x_proyecto = linea['ticket_medio'] // linea['tarifa']
                nuevas_jornadas = st.slider("Jornadas/Proyecto", max(1,int(jornadas_x_proyecto*0.5)), int(jornadas_x_proyecto*1.5), int(jornadas_x_proyecto), 1)
                ticket_medio = nueva_tarifa * nuevas_jornadas
                kpi_card("Jornadas/Proyecto", nuevas_jornadas, None, tooltip="Número medio de jornadas", show_euro=False)
        else:
            with cols[0]:
                ticket_medio = st.slider("Ticket Medio (€)", int(linea['ticket_medio']*0.5), int(linea['ticket_medio']*1.5), int(linea['ticket_medio']), 1000, format="%d")
                kpi_card("Ticket Medio", ticket_medio, None, tooltip="Valor medio por proyecto")

        with cols[2]:
            nuevo_unidades = st.slider("Unidades", 0, int(linea['unidades']*2), int(linea['unidades']), 1)
            kpi_card("Unidades", nuevo_unidades, None, tooltip="Proyectos o ventas", show_euro=False)
        if linea['personas'] > 0:
            with cols[3]:
                nuevo_personas = st.slider("Personas", 0, int(linea['personas']*2), int(linea['personas']), 1)
                kpi_card("Personas", nuevo_personas, None, tooltip="Número de personas asignadas", show_euro=False)
            with cols[3]:
                nuevo_coste_medio = st.slider("Coste Medio Persona (€)", int(linea['coste_medio_persona']*0.8), int(linea['coste_medio_persona']*1.2), int(linea['coste_medio_persona']), 1000, format="%d")
                kpi_card("Coste Medio Persona", nuevo_coste_medio, None, tooltip="Coste anual medio por persona")
        else:
            nuevo_personas = 0
            nuevo_coste_medio = 0

        # Cálculos
        facturacion_linea = ticket_medio * nuevo_unidades
        costes_personal = nuevo_personas * nuevo_coste_medio
        costes_directos = facturacion_linea * (linea['costes_directos_%'] / 100) + costes_personal
        margen_bruto = facturacion_linea - costes_directos
        resultados_lineas[linea_nombre] = {
            "facturacion": facturacion_linea,
            "costes_directos": costes_directos,
            "margen_bruto": margen_bruto
        }

# -------------------------------
# Costes Fijos
# -------------------------------
st.subheader("🏢 Costes Fijos")
costes_fijos_detalle = {k: v for k, v in param['costes_fijos'].items()}
cols_cf = st.columns(2)
for idx, (categoria, valor) in enumerate(costes_fijos_detalle.items()):
    with cols_cf[idx % 2]:
        nuevo_valor = st.slider(f"{categoria.capitalize()} (€)", 0, int(valor*2), int(valor), 1000, format="%d")
        costes_fijos_detalle[categoria] = nuevo_valor
        porcentaje = nuevo_valor / facturacion_total
        benchmark_categoria = benchmarks['global'].get(categoria.lower())
        kpi_card(categoria.capitalize(), nuevo_valor, porcentaje, benchmark=benchmark_categoria, tooltip=f"Coste fijo en {categoria}")

# -------------------------------
# Resultados Globales
# -------------------------------
st.subheader("📊 Resultados Globales")
costes_fijos_totales = sum(costes_fijos_detalle.values())
costes_directos_totales = sum([v['costes_directos'] for v in resultados_lineas.values()])
margen_bruto_total = sum([v['margen_bruto'] for v in resultados_lineas.values()])
ebitda_total = margen_bruto_total - costes_fijos_totales

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Facturación Total", facturacion_total, 1.0, tooltip="Ingresos totales estimados")
with col2:
    kpi_card("Costes Directos", costes_directos_totales, costes_directos_totales/facturacion_total, benchmark=(0.50,0.55), tooltip="Costes directos")
with col3:
    kpi_card("Margen Bruto", margen_bruto_total, margen_bruto_total/facturacion_total, benchmark=(0.45,0.50), tipo="margen", tooltip="Margen sobre ventas")
with col4:
    kpi_card("Costes Fijos", costes_fijos_totales, costes_fijos_totales/facturacion_total, benchmark=(0.15,0.20), tooltip="Suma de costes fijos")
with col5:
    kpi_card("EBITDA", ebitda_total, ebitda_total/facturacion_total, benchmark=(0.25,0.30), tipo="margen", tooltip="Beneficio antes de intereses y amortizaciones")

# -------------------------------
# Botón Exportar PDF
# -------------------------------
def generar_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 12)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.drawString(50, 800, f"Simulador PyG IT - {now}")

    y = 780
    c.drawString(50, y, "KPIs Globales:")
    y -= 20
    c.drawString(60, y, f"Facturación Total: {format_euro(facturacion_total)}")
    y -= 20
    c.drawString(60, y, f"Costes Directos: {format_euro(costes_directos_totales)}")
    y -= 20
    c.drawString(60, y, f"Margen Bruto: {format_euro(margen_bruto_total)}")
    y -= 20
    c.drawString(60, y, f"Costes Fijos: {format_euro(costes_fijos_totales)}")
    y -= 20
    c.drawString(60, y, f"EBITDA: {format_euro(ebitda_total)}")
    y -= 40

    c.drawString(50, y, "Costes Fijos Detalle:")
    for categoria, valor in costes_fijos_detalle.items():
        y -= 20
        c.drawString(60, y, f"{categoria}: {format_euro(valor)}")
    y -= 40

    c.drawString(50, y, "Resumen por Línea de Negocio:")
    for linea, valores in resultados_lineas.items():
        y -= 20
        c.drawString(60, y, f"{linea}: Facturación {format_euro(valores['facturacion'])}, Costes Directos {format_euro(valores['costes_directos'])}, Margen Bruto {format_euro(valores['margen_bruto'])}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

st.markdown("---")
if st.button("📥 Exportar PDF"):
    pdf_buffer = generar_pdf()
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    st.download_button("Descargar Simulación en PDF", data=pdf_buffer, file_name=f"Simulador_PyG_{now}.pdf", mime="application/pdf")

