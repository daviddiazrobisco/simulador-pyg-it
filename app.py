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

# Benchmarks
BENCHMARKS = {
    "Costes Directos": (0.50, 0.55),
    "Margen Bruto": (0.45, 0.50),
    "Costes Fijos": (0.15, 0.20),
    "EBITDA": (0.25, 0.30),
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
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

def get_estado(valor_pct, benchmark):
    min_bm, max_bm = benchmark
    if min_bm <= valor_pct <= max_bm:
        return COLOR_VERDE, "✅"
    elif valor_pct < min_bm:
        return COLOR_ROJO, "❌"
    else:
        return COLOR_NARANJA, "⚠️"

# -------------------------------
# Componente KPI con slider integrado (solo para detalle)
# -------------------------------
def kpi_card_slider(nombre, valor, facturacion, benchmark=None, tooltip=None, max_valor=None):
    porcentaje = valor / facturacion
    color, icono = get_estado(porcentaje, benchmark) if benchmark else (COLOR_VERDE, "✅")
    comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[1]*100)}%</small>" if benchmark else ""

    # Tarjeta KPI con slider integrado arriba
    html = f"""
    <div style="background-color:{COLOR_GRIS}; border-left:5px solid {color};
                padding:10px; border-radius:8px; transition: transform 0.2s; 
                display:flex; flex-direction:column; align-items:center;
                justify-content:space-between; min-height:240px;"
         onmouseover="this.style.transform='scale(1.02)'"
         onmouseout="this.style.transform='scale(1)'"
         title="{tooltip or nombre}">
        <div style="width:100%; margin-bottom:10px;">
            <small style="color:{COLOR_TEXTO}; font-size:12px;">Ajustar {nombre} (€)</small>
        </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    nuevo_valor = st.slider(
        "",  # Sin etiqueta porque ya la pusimos arriba
        min_value=0,
        max_value=int(max_valor or valor*2),
        value=int(valor),
        step=1000,
        format="%d",
        key=f"slider_{nombre}"
    )

    html_bottom = f"""
        <div style="font-size:18px; color:{COLOR_TEXTO}; margin-top:5px;">{nombre} {icono}</div>
        <div style="font-size:26px; font-weight:bold; color:{color}; margin-top:5px;">{format_euro(nuevo_valor)}</div>
        <div style="font-size:14px; color:{COLOR_TEXTO}; margin-top:5px;">{round(porcentaje*100,1)}% sobre ventas{comparativa}</div>
    </div>
    """
    st.markdown(html_bottom, unsafe_allow_html=True)
    return nuevo_valor

# -------------------------------
# Cargar datos desde JSON
# -------------------------------
with open('presupuesto_it_2025.json') as f:
    data = json.load(f)

param = data['parametros']
result = data['resultados']

# Variables principales
facturacion_default = int(result['facturacion_total'])
costes_fijos_default = param['costes_fijos']

# Inicializar session_state
if "costes_fijos_detalle" not in st.session_state:
    st.session_state.costes_fijos_detalle = dict(costes_fijos_default)

# -------------------------------
# Cálculos dinámicos
# -------------------------------
def calcular_pyg():
    total_costes_fijos = sum(st.session_state.costes_fijos_detalle.values())
    costes_directos = facturacion_default * (result['costes_directos'] / result['facturacion_total'])
    margen_bruto = facturacion_default - costes_directos
    ebitda = margen_bruto - total_costes_fijos

    return {
        "costes_directos": costes_directos,
        "margen_bruto": margen_bruto,
        "costes_fijos": total_costes_fijos,
        "ebitda": ebitda,
        "costes_directos_pct": costes_directos / facturacion_default,
        "margen_bruto_pct": margen_bruto / facturacion_default,
        "costes_fijos_pct": total_costes_fijos / facturacion_default,
        "ebitda_pct": ebitda / facturacion_default
    }

# -------------------------------
# Layout KPIs principales
# -------------------------------
pyg = calcular_pyg()

st.title("💻 Simulador PyG Financiero para Empresa IT")
st.markdown("Ajusta los costes fijos y observa el impacto en tiempo real.")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Facturación Total", format_euro(facturacion_default))
with col2:
    st.metric("Costes Directos", format_euro(pyg['costes_directos']))
with col3:
    st.metric("Margen Bruto", format_euro(pyg['margen_bruto']))
with col4:
    st.metric("Costes Fijos", format_euro(pyg['costes_fijos']))
with col5:
    st.metric("EBITDA", format_euro(pyg['ebitda']))

# -------------------------------
# Gráfico cascada
# -------------------------------
fig = go.Figure(go.Waterfall(
    name="PyG",
    orientation="v",
    measure=["relative", "relative", "relative", "total"],
    x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
    textposition="outside",
    text=[format_euro(facturacion_default), format_euro(-pyg['costes_directos']),
          format_euro(-pyg['costes_fijos']), format_euro(pyg['ebitda'])],
    y=[facturacion_default, -pyg['costes_directos'], -pyg['costes_fijos'], pyg['ebitda']],
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

# -------------------------------
# Bloque Costes Fijos (tarjetas en línea con sliders integrados)
# -------------------------------
st.markdown("### 🏢 Detalle de Costes Fijos")
detalle_cols = st.columns(len(costes_fijos_default))
for idx, (categoria, valor_default) in enumerate(costes_fijos_default.items()):
    with detalle_cols[idx]:
        nuevo_valor = kpi_card_slider(
            nombre=categoria.capitalize(),
            valor=st.session_state.costes_fijos_detalle[categoria],
            facturacion=facturacion_default,
            benchmark=BENCHMARKS.get(categoria.capitalize()),
            max_valor=valor_default * 2
        )
        st.session_state.costes_fijos_detalle[categoria] = nuevo_valor
