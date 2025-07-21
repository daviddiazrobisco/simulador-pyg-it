import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import plotly.io as pio

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="SIMULADOR DE ESCENARIOS", page_icon="📊", layout="wide")

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
            else:
                if valor_pct > max_bm:
                    return COLOR_ESTRELLA, "⭐"
                elif min_bm <= valor_pct <= max_bm:
                    return COLOR_VERDE, "✅"
                else:
                    return COLOR_NARANJA, "⚠️"
    return COLOR_TEXTO, ""

def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tipo="coste", tooltip=None, show_euro=True):
    color, icono = get_estado(valor_pct, benchmark, tipo, valor_abs=valor_abs if tipo == "tarifa" else None)
    comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[1]*100)}%</small>" if benchmark and tipo != "tarifa" else f"<br><small>Benchmark: {int(benchmark[0])}–{int(benchmark[1])} €</small>" if benchmark else "<br><small>Sin benchmark definido</small>"
    valor_mostrado = format_euro(valor_abs) if show_euro else f"{int(valor_abs)}"
    porcentaje = f"{round(valor_pct*100,1)}%" if valor_pct is not None else "—"
    html = f"""
    <div class="kpi-card" style="background-color:{COLOR_GRIS}; border-left:5px solid {color}; padding:10px; border-radius:8px; transition: transform 0.2s; position:relative;"
         onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'" title="{tooltip or nombre}">
        <div style="font-size:18px; color:{COLOR_TEXTO};">{nombre} {icono}</div>
        <div style="font-size:26px; font-weight:bold; color:{color};">{valor_mostrado}</div>
        <div style="font-size:14px; color:{COLOR_TEXTO};">{porcentaje} sobre ventas{comparativa}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------
# Cargar datos
# -------------------------------
with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

param = data['parametros']
facturacion_total = data['resultados']['facturacion_total']
resultados_lineas = {}

# -------------------------------
# Función para exportar PDF
# -------------------------------
def exportar_pdf():
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Título
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(50, height - 50, "SIMULADOR DE ESCENARIOS")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 70, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Resumen KPIs Globales
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 110, "KPIs Globales")

    y_pos = height - 130
    for kpi, val in [
        ("Facturación Total", facturacion_total),
        ("Costes Directos", data['resultados']['costes_directos']),
        ("Margen Bruto", data['resultados']['margen_bruto']),
        ("Costes Fijos", data['resultados']['costes_fijos']),
        ("EBITDA", data['resultados']['ebitda'])]:
        pdf.setFont("Helvetica", 12)
        pdf.drawString(60, y_pos, f"{kpi}: {format_euro(val)}")
        y_pos -= 20

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer

# -------------------------------
# Layout Streamlit
# -------------------------------
st.title("📊 SIMULADOR DE ESCENARIOS")

st.subheader("💼 LÍNEAS DE NEGOCIO")
# (Aquí código para mostrar líneas de negocio con KPIs, sliders, gráficos)

st.subheader("🏢 COSTES FIJOS")
# (Aquí código para mostrar costes fijos con KPIs y sliders)

st.subheader("📊 RESULTADOS GLOBALES")
# (Aquí código para mostrar KPIs globales, gráfico cascada, tabla resumen)

# -------------------------------
# Botón Exportar PDF
# -------------------------------
pdf_file = exportar_pdf()
st.download_button(label="📥 Exportar a PDF", data=pdf_file, file_name=f"Simulador_Escenarios_{datetime.now().strftime('%Y-%m-%d')}.pdf", mime="application/pdf")
