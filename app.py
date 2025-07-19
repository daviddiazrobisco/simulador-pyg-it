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

# Benchmarks globales y específicos (ajusta según informe)
BENCHMARKS = {
    "Costes Directos": (0.50, 0.55),
    "Margen Bruto": (0.45, 0.50),
    "Costes Fijos": (0.15, 0.20),
    "EBITDA": (0.25, 0.30),
    # Costes fijos por categoría
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
    """Formatea número con puntos miles y €"""
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
# Inicializar variables acumuladoras
# -------------------------------
facturacion_total = 0
costes_directos_total = 0

# -------------------------------
# BLOQUES POR LÍNEA DE NEGOCIO
# -------------------------------
st.title("💻 Simulador PyG Financiero para Empresa IT")
st.markdown("Ajusta las variables clave de cada línea de negocio y analiza el impacto.")

for linea, valores in param['lineas_negocio'].items():
    with st.expander(f"📦 {linea.capitalize()}", expanded=False):
        st.markdown(f"**Configura los parámetros de {linea}**")

        tarifa = st.slider(
            f"Tarifa media {linea} (€)",
            min_value=0,
            max_value=int(valores['tarifa'] * 2),
            value=int(valores['tarifa']),
            step=100
        )

        proyectos = st.slider(
            f"Nº Proyectos {linea}",
            min_value=0,
            max_value=int(valores['proyectos'] * 2),
            value=int(valores['proyectos']),
            step=1
        )

        personas = st.slider(
            f"Nº Personas {linea}",
            min_value=0,
            max_value=int(valores['personas'] * 2),
            value=int(valores['personas']),
            step=1
        )

        actividad = st.slider(
            f"Nivel de actividad {linea} (%)",
            min_value=0,
            max_value=150,
            value=int(valores['actividad'] * 100),
            step=1
        ) / 100  # convertir a ratio

        # Cálculos
        facturacion_linea = tarifa * proyectos * actividad
        costes_directos_linea = personas * valores['coste_persona'] * actividad
        margen_bruto_linea = facturacion_linea - costes_directos_linea

        facturacion_total += facturacion_linea
        costes_directos_total += costes_directos_linea

        # KPIs línea
        linea_cols = st.columns(3)
        with linea_cols[0]:
            kpi_card("Facturación", facturacion_linea, facturacion_linea / facturacion_total,
                     tooltip="Ingresos generados por esta línea")
        with linea_cols[1]:
            kpi_card("Costes Directos", costes_directos_linea, costes_directos_linea / facturacion_linea,
                     benchmark=BENCHMARKS["Costes Directos"],
                     tooltip="Costes de personal directamente asignados")
        with linea_cols[2]:
            kpi_card("Margen Bruto", margen_bruto_linea, margen_bruto_linea / facturacion_linea,
                     benchmark=BENCHMARKS["Margen Bruto"],
                     tooltip="Ingresos menos costes directos")

# -------------------------------
# BLOQUE COSTES FIJOS
# -------------------------------
costes_fijos = 0
with st.expander("🏢 Costes Fijos", expanded=False):
    st.markdown("Ajusta las partidas de costes fijos.")

    cols_fijos = st.columns(len(param['costes_fijos']))
    for idx, (categoria, valor) in enumerate(param['costes_fijos'].items()):
        nuevo_valor = st.slider(
            f"{categoria.capitalize()} (€)",
            min_value=0,
            max_value=int(valor * 2),
            value=int(valor),
            step=1000
        )
        costes_fijos += nuevo_valor

        porcentaje = nuevo_valor / facturacion_total if facturacion_total > 0 else 0
        benchmark_categoria = BENCHMARKS.get(categoria.capitalize())
        with cols_fijos[idx]:
            kpi_card(categoria.capitalize(), nuevo_valor, porcentaje,
                     benchmark=benchmark_categoria,
                     tooltip=f"Coste fijo en {categoria}")

# -------------------------------
# KPIs TOTALES EMPRESA
# -------------------------------
margen_bruto_total = facturacion_total - costes_directos_total
ebitda_total = margen_bruto_total - costes_fijos

st.header("📊 Resumen Total Empresa")
total_cols = st.columns(5)
with total_cols[0]:
    kpi_card("Facturación Total", facturacion_total, 1.0, tooltip="Suma de todas las líneas")
with total_cols[1]:
    kpi_card("Costes Directos", costes_directos_total, costes_directos_total / facturacion_total,
             benchmark=BENCHMARKS["Costes Directos"])
with total_cols[2]:
    kpi_card("Margen Bruto", margen_bruto_total, margen_bruto_total / facturacion_total,
             benchmark=BENCHMARKS["Margen Bruto"])
with total_cols[3]:
    kpi_card("Costes Fijos", costes_fijos, costes_fijos / facturacion_total,
             benchmark=BENCHMARKS["Costes Fijos"])
with total_cols[4]:
    kpi_card("EBITDA", ebitda_total, ebitda_total / facturacion_total,
             benchmark=BENCHMARKS["EBITDA"])

# -------------------------------
# GRÁFICO CASCADA
# -------------------------------
fig = go.Figure(go.Waterfall(
    name="PyG",
    orientation="v",
    measure=["relative", "relative", "relative", "total"],
    x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
    textposition="outside",
    text=[format_euro(facturacion_total), format_euro(-costes_directos_total),
          format_euro(-costes_fijos), format_euro(ebitda_total)],
    y=[facturacion_total, -costes_directos_total, -costes_fijos, ebitda_total],
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
