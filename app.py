import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import fitz  # PyMuPDF
from io import BytesIO

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
# Función formateo números europeos
# -------------------------------
def format_euro(valor):
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

# -------------------------------
# Función exportar a PDF
# -------------------------------
def exportar_pdf(html_content, nombre_pdf):
    pdf_buffer = BytesIO()
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 tamaño
    text_rect = fitz.Rect(50, 50, 545, 792)
    page.insert_textbox(text_rect, html_content, fontsize=10, color=(0, 0, 0))
    doc.save(pdf_buffer)
    doc.close()
    st.download_button(
        label="📥 Descargar PDF",
        data=pdf_buffer.getvalue(),
        file_name=nombre_pdf,
        mime="application/pdf"
    )

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tipo="coste", tooltip=None, show_euro=True):
    color, icono = COLOR_VERDE, "✅"
    comparativa = ""
    if benchmark:
        min_bm, max_bm = benchmark
        if tipo == "coste":
            if valor_pct < min_bm:
                color, icono = COLOR_ESTRELLA, "⭐"
            elif min_bm <= valor_pct <= max_bm:
                color, icono = COLOR_VERDE, "✅"
            else:
                color, icono = COLOR_NARANJA, "⚠️"
        else:
            color, icono = COLOR_TEXTO, ""
        comparativa = f"<br><small>Benchmark: {int(min_bm*100)}–{int(max_bm*100)}%</small>"
    else:
        comparativa = "<br><small>Sin benchmark definido</small>"

    valor_mostrado = format_euro(valor_abs) if show_euro else f"{int(valor_abs)}"
    porcentaje = f"{round(valor_pct*100,1)}%" if valor_pct is not None else "—"

    html = f"""
    <div style="background-color:{COLOR_GRIS}; border-left:5px solid {color};
                padding:10px; border-radius:8px; margin-bottom:5px;">
        <div style="font-size:18px; color:{COLOR_TEXTO};">{nombre} {icono}</div>
        <div style="font-size:26px; font-weight:bold; color:{color};">{valor_mostrado}</div>
        <div style="font-size:14px; color:{COLOR_TEXTO};">{porcentaje} sobre ventas{comparativa}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------
# Cargar datos desde JSON
# -------------------------------
with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

param = data['parametros']
result = data['resultados']
facturacion_total = result['facturacion_total']

# -------------------------------
# Simulador de escenarios
# -------------------------------
st.title("📊 SIMULADOR DE ESCENARIOS")

st.header("🏢 Líneas de Negocio")
# Aquí irían los bloques por línea de negocio (como antes)
st.markdown("Aquí irán los sliders, KPIs, gráficos por línea de negocio...")

st.header("🏢 Costes Fijos")
# Aquí iría el bloque de costes fijos (como antes)
st.markdown("Aquí irán los sliders, KPIs y gráficos de costes fijos...")

st.header("📊 Resultados Globales")
# KPIs globales
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Facturación Total", facturacion_total, 1.0)
with col2:
    kpi_card("Costes Directos", result["costes_directos"], result["costes_directos"]/facturacion_total)
with col3:
    kpi_card("Margen Bruto", result["margen_bruto"], result["margen_bruto"]/facturacion_total)
with col4:
    kpi_card("Costes Fijos", result["costes_fijos"], result["costes_fijos"]/facturacion_total)
with col5:
    kpi_card("EBITDA", result["ebitda"], result["ebitda_%"]/100)

# Gráfico cascada global
fig_global = go.Figure(go.Waterfall(
    name="PyG",
    orientation="v",
    measure=["relative", "relative", "relative", "total"],
    x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
    textposition="outside",
    y=[facturacion_total, -result["costes_directos"], -result["costes_fijos"], result["ebitda"]],
    connector={"line": {"color": "rgb(63, 63, 63)"}}
))
st.plotly_chart(fig_global, use_container_width=True)

# Tabla resumen por línea de negocio
st.subheader("📋 Resumen por Línea de Negocio")
resumen_df = pd.DataFrame({
    "Línea": ["Implantación", "Licencias", "Hot line"],
    "Facturación": [format_euro(1000000), format_euro(2000000), format_euro(2000000)],
    "Costes Directos": [format_euro(500000), format_euro(1200000), format_euro(1100000)],
    "Margen Bruto": [format_euro(500000), format_euro(800000), format_euro(900000)]
})
st.table(resumen_df)

# -------------------------------
# Exportar PDF
# -------------------------------
st.header("📤 Exportar Informe")
if st.button("Generar PDF"):
    now = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_pdf = f"Simulador_{now}.pdf"
    exportar_pdf(st.session_state["page_content"] if "page_content" in st.session_state else "Simulador PyG IT", nombre_pdf)
