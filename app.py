import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="Simulador de Escenarios", page_icon="📊", layout="wide")

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

resultados_lineas = {}

# -------------------------------
# LÍNEAS DE NEGOCIO
# -------------------------------
st.title("📊 SIMULADOR DE ESCENARIOS")
st.subheader("💼 LÍNEAS DE NEGOCIO")

for linea_nombre, linea in param['lineas_negocio'].items():
    benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])
    with st.expander(f"🔽 {linea_nombre.upper()}", expanded=False):
        cols = st.columns(4)

        # Tarifa / Ticket Medio
        if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
            with cols[0]:
                nueva_tarifa = st.slider("Tarifa (€)", int(linea['tarifa']*0.8), int(linea['tarifa']*1.2), int(linea['tarifa']), step=10)
                bm_tarifa = benchmark_linea['precio_jornada'] if benchmark_linea else None
                kpi_card("Tarifa", nueva_tarifa, None, benchmark=(bm_tarifa[0], bm_tarifa[2]) if bm_tarifa else None, tipo="tarifa", tooltip="Precio medio jornada")
            with cols[1]:
                jornadas_x_proyecto = linea['ticket_medio'] // linea['tarifa']
                nuevas_jornadas = st.slider("Jornadas/Proyecto", int(jornadas_x_proyecto*0.5), int(jornadas_x_proyecto*1.5), int(jornadas_x_proyecto), step=1)
                ticket_medio = nueva_tarifa * nuevas_jornadas
                kpi_card("Jornadas/Proyecto", nuevas_jornadas, None, tooltip="Número medio de jornadas por proyecto", show_euro=False)
        else:
            with cols[0]:
                ticket_medio = st.slider("Ticket Medio (€)", int(linea['ticket_medio']*0.5), int(linea['ticket_medio']*1.5), int(linea['ticket_medio']), step=1000)
                kpi_card("Ticket Medio", ticket_medio, None, tooltip="Valor medio por proyecto")

        # Unidades
        with cols[2]:
            nuevo_unidades = st.slider("Número de Unidades", 0, linea['unidades']*2, linea['unidades'], step=1)
            kpi_card("Número de Unidades", nuevo_unidades, None, tooltip="Proyectos o ventas", show_euro=False)

        # Personas
        if linea['personas'] > 0:
            with cols[3]:
                nuevo_personas = st.slider("Personas", 0, linea['personas']*2, linea['personas'], step=1)
                kpi_card("Personas", nuevo_personas, None, tooltip="Número de personas asignadas", show_euro=False)

        # Coste Medio Persona
        if linea['personas'] > 0:
            with cols[0]:
                nuevo_coste_medio = st.slider("Coste Medio Persona (€)", int(linea['coste_medio_persona']*0.8), int(linea['coste_medio_persona']*1.2), int(linea['coste_medio_persona']), step=1000)
                kpi_card("Coste Medio Persona", nuevo_coste_medio, None, tooltip="Coste anual medio por persona")

        # Cálculos
        facturacion_linea = ticket_medio * nuevo_unidades
        costes_personal = nuevo_personas * nuevo_coste_medio if linea['personas'] > 0 else 0
        costes_directos_pct = linea['costes_directos_%']
        costes_directos = facturacion_linea * (costes_directos_pct / 100) + costes_personal
        margen_bruto = facturacion_linea - costes_directos

        resultados_lineas[linea_nombre] = {
            "facturacion": facturacion_linea,
            "costes_directos": costes_directos,
            "margen_bruto": margen_bruto
        }

        # 📊 KPIs resultados
        st.subheader("📊 KPIs Resultados")
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_card("Facturación", facturacion_linea, None)
        with col2:
            kpi_card("Costes Directos", costes_directos, (costes_directos / facturacion_linea) if facturacion_linea else None)
        with col3:
            kpi_card("Margen Bruto", margen_bruto, (margen_bruto / facturacion_linea) if facturacion_linea else None, benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None, tipo="margen")

# -------------------------------
# 📦 Costes Fijos
# -------------------------------
st.subheader("🏢 COSTES FIJOS")
# ... (Aquí se mantiene la lógica de costes fijos con sliders y KPIs) ...

# -------------------------------
# 📊 Resultados Globales
# -------------------------------
st.subheader("📊 RESULTADOS GLOBALES")
# ... (Aquí se muestran KPIs globales, gráfico cascada, tabla resumen) ...

# -------------------------------
# Exportar PDF
# -------------------------------
if st.button("📥 Exportar a PDF"):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("Simulador_Escenarios")
    pdf.drawString(50, 800, "Simulador de Escenarios - Exportación PDF")
    pdf.save()
    buffer.seek(0)
    st.download_button("Descargar PDF", buffer, file_name="Simulador_Escenarios.pdf", mime="application/pdf")
