import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import weasyprint

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
# Cargar datos
# -------------------------------
with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

param = data['parametros']
resultados_globales = data['resultados']
mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# Título principal
# -------------------------------
st.title("💻 SIMULADOR DE ESCENARIOS")

# -------------------------------
# BLOQUES LÍNEAS DE NEGOCIO
# -------------------------------
st.subheader("🏢 Líneas de Negocio")
# [Aquí va tu código existente de líneas de negocio completo con todos los gráficos y KPIs]
# OMITIDO POR ESPACIO - pegamos aquí el bloque que ya tienes funcionando

# -------------------------------
# BLOQUE COSTES FIJOS
# -------------------------------
st.subheader("🏢 Costes Fijos")
# [Aquí va tu código existente de costes fijos completo]
# OMITIDO POR ESPACIO - pegamos aquí el bloque que ya tienes funcionando

# -------------------------------
# BLOQUE RESULTADOS GLOBALES
# -------------------------------
st.subheader("📊 Resultados Globales")
# [Aquí va tu código existente de resultados globales completo]
# OMITIDO POR ESPACIO - pegamos aquí el bloque que ya tienes funcionando

# -------------------------------
# EXPORTACIÓN A PDF
# -------------------------------
st.subheader("📤 Exportación")
if st.button("Exportar a PDF"):
    # Capturamos todo el contenido de la app como HTML
    html_string = """
    <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .kpi-card { margin-bottom: 10px; }
                h1, h2, h3, h4 { color: #333333; }
            </style>
        </head>
        <body>
            """ + st.session_state._main_st_frame._get_session()._get_report_queue().get().page_content + """
        </body>
    </html>
    """

    # Nombre dinámico para el PDF
    now = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"simulador_escenarios_{now}.pdf"

    # Generar el PDF
    weasyprint.HTML(string=html_string).write_pdf(filename)

    # Proporcionar enlace de descarga
    with open(filename, "rb") as f:
        st.download_button(
            label="📥 Descargar PDF",
            data=f,
            file_name=filename,
            mime="application/pdf"
        )
