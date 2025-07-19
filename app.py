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

# Colores corporativos
verde_oscuro = "#144C44"
naranja = "#fb9200"
gris_claro = "#F2F2F2"
gris_oscuro = "#333333"
blanco = "#FFFFFF"

# Estilo CSS básico
st.markdown(f"""
    <style>
        .big-font {{
            font-size:40px !important;
            color: {verde_oscuro};
        }}
        .kpi-card {{
            background-color: {gris_claro};
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
    </style>
""", unsafe_allow_html=True)

# Título
st.title("💻 Simulador PyG Financiero para Empresa IT")
st.markdown("Ajusta las variables clave y observa el impacto en tiempo real.")

# Sliders para ajustes globales
st.sidebar.header("🔧 Ajustes Simulación")
facturacion = st.sidebar.slider(
    'Facturación total (€)', 
    min_value=0, 
    max_value=10_000_000, 
    value=result['facturacion_total'], 
    step=50_000
)

costes_fijos = st.sidebar.slider(
    'Costes fijos totales (€)', 
    min_value=0, 
    max_value=2_000_000, 
    value=result['costes_fijos'], 
    step=50_000
)

# Cálculos dinámicos
costes_directos = facturacion * (result['costes_directos'] / result['facturacion_total'])
margen_bruto = facturacion - costes_directos
ebitda = margen_bruto - costes_fijos

# Formatear números europeos
def format_euro(valor):
    return f"{valor:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# KPIs principales
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown('<div class="kpi-card">Facturación Total</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-font">{format_euro(facturacion)}</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="kpi-card">Costes Directos</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-font">{format_euro(costes_directos)}</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="kpi-card">Margen Bruto</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-font">{format_euro(margen_bruto)}</div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="kpi-card">Costes Fijos</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-font">{format_euro(costes_fijos)}</div>', unsafe_allow_html=True)
with col5:
    st.markdown('<div class="kpi-card">EBITDA</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-font">{format_euro(ebitda)}</div>', unsafe_allow_html=True)

# Gráfico cascada
fig = go.Figure(go.Waterfall(
    name = "PyG",
    orientation = "v",
    measure = ["relative", "relative", "relative", "total"],
    x = ["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
    textposition = "outside",
    text = [format_euro(facturacion), format_euro(-costes_directos), format_euro(-costes_fijos), format_euro(ebitda)],
    y = [facturacion, -costes_directos, -costes_fijos, ebitda],
    connector = {"line":{"color":"rgb(63, 63, 63)"}}
))
fig.update_layout(
    title="Cuenta de Resultados - Gráfico Cascada",
    plot_bgcolor=blanco,
    paper_bgcolor=blanco,
    font=dict(color=gris_oscuro)
)
st.plotly_chart(fig, use_container_width=True)
