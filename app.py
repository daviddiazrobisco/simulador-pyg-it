import streamlit as st
import json
import plotly.graph_objects as go

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="Simulador PyG IT", page_icon="💻", layout="wide")

# Colores corporativos
COLOR_VERDE = "#144C44"
COLOR_NARANJA = "#fb9200"
COLOR_ROJO = "#D33F49"
COLOR_GRIS = "#F2F2F2"
COLOR_TEXTO = "#333333"
COLOR_FONDO = "#FFFFFF"

# Benchmarks por KPI global y por costes fijos
BENCHMARKS = {
    "Costes Directos": (0.50, 0.55),
    "Margen Bruto": (0.45, 0.50),
    "Costes Fijos": (0.15, 0.20),
    "EBITDA": (0.25, 0.30),
    # Benchmarks por categoría de costes fijos
    "Estructura": (0.05, 0.07),
    "Alquiler": (0.02, 0.03),
    "Marketing": (0.02, 0.04),
    "Suministros": (0.01, 0.02),
    "Software interno": (0.01, 0.03),
    "Otros": (0.005, 0.01)
}

# -------------------------------
# Función formateo números europeos
# -------------------------------
def format_euro(valor):
    """Formatea número con puntos miles, sin decimales y €"""
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

def get_estado(valor_pct, benchmark):
    """Devuelve color e icono según benchmark"""
    min_bm, max_bm = benchmark
    if min_bm <= valor_pct <= max_bm:
        return COLOR_VERDE, "✅"
    elif valor_pct < min_bm:
        return COLOR_ROJO, "❌"
    else:
        return COLOR_NARANJA, "⚠️"

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tooltip=None):
    """Genera una tarjeta KPI con color dinámico y popup"""
    color, icono = COLOR_VERDE, "✅"
    comparativa = ""
    if benchmark:
        color, icono = get_estado(valor_pct, benchmark)
        comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[1]*100)}%</small>"

    html = f"""
    <div class="kpi-card" style="background-color:{COLOR_GRIS}; 
                                  border-left:5px solid {color};
                                  padding:10px; border-radius:8px;
                                  transition: transform 0.2s; position:relative;"
         onmouseover="this.style.transform='scale(1.02)'"
         onmouseout="this.style.transform='scale(1)'"
         title="{tooltip or nombre}">
        <div style="font-size:18px; color:{COLOR_TEXTO};">{nombre} {icono}</div>
        <div style="font-size:26px; font-weight:bold; color:{color};">{format_euro(valor_abs)}</div>
        <div style="font-size:14px; color:{COLOR_TEXTO};">{round(valor_pct*100, 1)}% sobre ventas{comparativa}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------
# Cargar datos desde JSON
# -------------------------------
with open('presupuesto_it_2025.json') as f:
    data = json.load(f)

param = data['parametros']
result = data['resultados']

# -------------------------------
# Ajustes fijos iniciales
# -------------------------------
facturacion = int(result['facturacion_total'])
costes_directos = facturacion * (result['costes_directos'] / result['facturacion_total'])

# -------------------------------
# Cálculo costes fijos detallados (sliders dentro del bloque)
# -------------------------------
st.title("💻 Simulador PyG Financiero para Empresa IT")
st.markdown("Ajusta las variables clave y observa el impacto en tiempo real.")

# Bloque Costes Fijos - Plegable
with st.expander("🏢 Detalle de Costes Fijos", expanded=False):
    st.markdown("Ajusta cada partida para analizar su impacto en la rentabilidad.")
    
    costes_fijos_detalle = {}
    for categoria, valor in param['costes_fijos'].items():
        slider_valor = st.slider(
            f"{categoria.capitalize()} (€)",
            min_value=0,
            max_value=int(valor * 2),
            value=int(valor),
            step=1000,
            format="%d"
        )
        costes_fijos_detalle[categoria] = slider_valor

    # Recalcular total costes fijos
    costes_fijos = sum(costes_fijos_detalle.values())
    costes_fijos_pct = costes_fijos / facturacion

    # Tarjeta KPI total costes fijos
    kpi_card("Total Costes Fijos", costes_fijos, costes_fijos_pct, BENCHMARKS["Costes Fijos"],
             tooltip="Suma de todos los costes fijos")

    # Tarjetas KPI detalle categorías
    detalle_cols = st.columns(len(costes_fijos_detalle))
    for idx, (categoria, valor) in enumerate(costes_fijos_detalle.items()):
        porcentaje = valor / facturacion
        benchmark_categoria = BENCHMARKS.get(categoria.capitalize())
        with detalle_cols[idx]:
            kpi_card(categoria.capitalize(), valor, porcentaje,
                     benchmark=benchmark_categoria,
                     tooltip=f"Coste fijo en {categoria}")

# -------------------------------
# Cálculos dinámicos y KPIs principales
# -------------------------------
margen_bruto = facturacion - costes_directos
ebitda = margen_bruto - costes_fijos

costes_directos_pct = costes_directos / facturacion
margen_bruto_pct = margen_bruto / facturacion
ebitda_pct = ebitda / facturacion

# Layout KPIs principales
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    kpi_card("Facturación Total", facturacion, 1.0, tooltip="Ingresos totales estimados")

with col2:
    kpi_card("Costes Directos", costes_directos, costes_directos_pct, BENCHMARKS["Costes Directos"],
             tooltip="Costes asociados directamente a la producción de servicios")

with col3:
    kpi_card("Margen Bruto", margen_bruto, margen_bruto_pct, BENCHMARKS["Margen Bruto"],
             tooltip="Ingresos menos costes directos")

with col4:
    kpi_card("Costes Fijos", costes_fijos, costes_fijos_pct, BENCHMARKS["Costes Fijos"],
             tooltip="Costes de estructura y operativos")

with col5:
    kpi_card("EBITDA", ebitda, ebitda_pct, BENCHMARKS["EBITDA"],
             tooltip="Beneficio antes de intereses, impuestos, depreciaciones y amortizaciones")

# -------------------------------
# Gráfico cascada
# -------------------------------
fig = go.Figure(go.Waterfall(
    name="PyG",
    orientation="v",
    measure=["relative", "relative", "relative", "total"],
    x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
    textposition="outside",
    text=[format_euro(facturacion), format_euro(-costes_directos),
          format_euro(-costes_fijos), format_euro(ebitda)],
    y=[facturacion, -costes_directos, -costes_fijos, ebitda],
    connector={"line": {"color": "rgb(63, 63, 63)"}}
))
fig.update_layout(
    title="Cuenta de Resultados - Gráfico Cascada",
    plot_bgcolor=COLOR_FONDO,
    paper_bgcolor=COLOR_FONDO,
    font=dict(color=COLOR_TEXTO),
    margin=dict(l=10, r=10, t=40, b=10)
)
st.plotly_chart(fig, use_container_width=True)
