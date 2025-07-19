import streamlit as st
import json
import plotly.graph_objects as go

# Configuración general
st.set_page_config(page_title="Simulador PyG IT", page_icon="💻", layout="wide")

# Cargar datos desde JSON
with open('presupuesto_it_2025.json') as f:
    data = json.load(f)

param = data['parametros']
result = data['resultados']

# Paleta corporativa
verde_oscuro = "#144C44"
naranja = "#fb9200"
rojo = "#FF4B4B"
gris_claro = "#F2F2F2"
gris_oscuro = "#333333"
blanco = "#FFFFFF"

# Función formato europeo
def format_euro(valor):
    return f"{valor:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# Función KPI Card reutilizable
def kpi_card(title, value, porcentaje, benchmark, estado):
    # Color según estado
    if estado == "ok":
        color_valor = verde_oscuro
        icono = "✅"
    elif estado == "warning":
        color_valor = naranja
        icono = "⚠️"
    else:
        color_valor = rojo
        icono = "❌"

    # HTML tarjeta
    st.markdown(f"""
        <div style="
            background-color:{gris_claro};
            padding:15px;
            border-radius:10px;
            text-align:center;
            min-height:150px;
        ">
            <h4 style="color:{gris_oscuro}; margin-bottom:5px;">{title}</h4>
            <p style="font-size:28px; color:{color_valor}; margin:0;"><b>{format_euro(value)}</b></p>
            <p style="font-size:16px; color:{gris_oscuro}; margin:0;">📊 {porcentaje:.1f}% sobre ventas</p>
            <p style="font-size:14px; color:#666666; margin:0;">📈 Benchmark: {benchmark} {icono}</p>
        </div>
    """, unsafe_allow_html=True)

# Sidebar ajustes
st.sidebar.header("🔧 Ajustes Simulación")

facturacion_default = int(result['facturacion_total'])
costes_fijos_default = int(result['costes_fijos'])

facturacion = st.sidebar.slider(
    'Facturación total (€)', 
    min_value=0, 
    max_value=10000000, 
    value=facturacion_default if 0 <= facturacion_default <= 10000000 else 5000000,
    step=50000
)

costes_fijos = st.sidebar.slider(
    'Costes fijos totales (€)', 
    min_value=0, 
    max_value=2000000, 
    value=costes_fijos_default if 0 <= costes_fijos_default <= 2000000 else 500000,
    step=50000
)

# Cálculos dinámicos
costes_directos = facturacion * (result['costes_directos'] / result['facturacion_total'])
margen_bruto = facturacion - costes_directos
ebitda = margen_bruto - costes_fijos

# Benchmarks para comparativa
benchmarks = {
    "Costes Directos": (50, 55),
    "Margen Bruto": (45, 50),
    "Costes Fijos": (15, 20),
    "EBITDA": (25, 30)
}

# Calcula % sobre ventas
pct_costes_directos = (costes_directos / facturacion) * 100 if facturacion else 0
pct_margen_bruto = (margen_bruto / facturacion) * 100 if facturacion else 0
pct_costes_fijos = (costes_fijos / facturacion) * 100 if facturacion else 0
pct_ebitda = (ebitda / facturacion) * 100 if facturacion else 0

# Compara con benchmark
def get_estado(valor, rango):
    if rango[0] <= valor <= rango[1]:
        return "ok"
    elif (valor < rango[0] and valor >= rango[0] - 5) or (valor > rango[1] and valor <= rango[1] + 5):
        return "warning"
    else:
        return "error"

estado_costes_directos = get_estado(pct_costes_directos, benchmarks["Costes Directos"])
estado_margen_bruto = get_estado(pct_margen_bruto, benchmarks["Margen Bruto"])
estado_costes_fijos = get_estado(pct_costes_fijos, benchmarks["Costes Fijos"])
estado_ebitda = get_estado(pct_ebitda, benchmarks["EBITDA"])

# Título principal
st.title("💻 Simulador PyG Financiero para Empresa IT")
st.markdown("Ajusta las variables clave y observa el impacto en tiempo real.")

# Mostrar tarjetas KPI en fila
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Facturación Total", facturacion, 100, "-", "ok")
with col2:
    kpi_card("Costes Directos", costes_directos, pct_costes_directos, "50–55%", estado_costes_directos)
with col3:
    kpi_card("Margen Bruto", margen_bruto, pct_margen_bruto, "45–50%", estado_margen_bruto)
with col4:
    kpi_card("Costes Fijos", costes_fijos, pct_costes_fijos, "15–20%", estado_costes_fijos)
with col5:
    kpi_card("EBITDA", ebitda, pct_ebitda, "25–30%", estado_ebitda)

# Gráfico cascada
fig = go.Figure(go.Waterfall(
    name="PyG",
    orientation="v",
    measure=["relative", "relative", "relative", "total"],
    x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
    textposition="outside",
    text=[format_euro(facturacion), format_euro(-costes_directos), format_euro(-costes_fijos), format_euro(ebitda)],
    y=[facturacion, -costes_directos, -costes_fijos, ebitda],
    connector={"line": {"color": "rgb(63, 63, 63)"}}
))
fig.update_layout(
    title="Cuenta de Resultados - Gráfico Cascada",
    plot_bgcolor=blanco,
    paper_bgcolor=blanco,
    font=dict(color=gris_oscuro)
)
st.plotly_chart(fig, use_container_width=True)
