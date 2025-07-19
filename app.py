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

def comentario_estrategico(kpi, valor_pct, benchmark):
    """Genera comentario según estado del KPI"""
    min_bm, max_bm = benchmark
    if valor_pct < min_bm:
        return f"🔴 {kpi} bajo: considera subir tarifas o reducir costes directos."
    elif valor_pct > max_bm:
        return f"🟠 {kpi} alto: revisa posibles ineficiencias operativas."
    else:
        return f"✅ {kpi} en rango óptimo."

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
    with st.expander(f"📦 {linea}", expanded=False):
        st.markdown(f"**Configura los parámetros de {linea}**")

        tarifa = st.slider(
            f"Tarifa media {linea} (€)",
            min_value=0,
            max_value=int(valores.get('tarifa', 1000) * 2),
            value=int(valores.get('tarifa', 1000)),
            step=100
        )

        unidades = st.slider(
            f"Unidades/Proyectos {linea}",
            min_value=0,
            max_value=int(valores.get('unidades', 10) * 2),
            value=int(valores.get('unidades', 10)),
            step=1
        )

        actividad = st.slider(
            f"Nivel de actividad {linea} (%)",
            min_value=0,
            max_value=150,
            value=100,
            step=1
        ) / 100  # convertir a ratio

        # Cálculos
        facturacion_linea = tarifa * unidades * actividad

        # Costes directos: Si hay personas, calcular; si no, usar %
        if valores.get('personas', 0) > 0:
            costes_directos_linea = valores['personas'] * valores['coste_medio_persona'] * actividad
        else:
            costes_directos_linea = facturacion_linea * (valores['costes_directos_%'] / 100)

        margen_bruto_linea = facturacion_linea - costes_directos_linea

        facturacion_total += facturacion_linea
        costes_directos_total += costes_directos_linea

        # KPIs línea
        linea_cols = st.columns(3)
        with linea_cols[0]:
            kpi_card("Facturación", facturacion_linea, facturacion_linea / facturacion_total if facturacion_total else 0,
                     tooltip="Ingresos generados por esta línea")
        with linea_cols[1]:
            mb_pct = margen_bruto_linea / facturacion_linea if facturacion_linea else 0
            kpi_card("Margen Bruto", margen_bruto_linea, mb_pct,
                     benchmark=BENCHMARKS["Margen Bruto"],
                     tooltip="Ingresos menos costes directos")
        with linea_cols[2]:
            cd_pct = costes_directos_linea / facturacion_linea if facturacion_linea else 0
            kpi_card("Costes Directos", costes_directos_linea, cd_pct,
                     benchmark=BENCHMARKS["Costes Directos"],
                     tooltip="Costes de esta línea")

        # Comentario estratégico
        comentario = comentario_estrategico("Margen Bruto", mb_pct, BENCHMARKS["Margen Bruto"])
        st.markdown(f"💬 **{comentario}**")

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
ebitda_pct = ebitda_total / facturacion_total if facturacion_total else 0

st.header("📊 Resumen Total Empresa")
total_cols = st.columns(5)
with total_cols[0]:
    kpi_card("Facturación Total", facturacion_total, 1.0, tooltip="Suma de todas las líneas")
with total_cols[1]:
    kpi_card("Costes Directos", costes_directos_total, costes_directos_total / facturacion_total if facturacion_total else 0,
             benchmark=BENCHMARKS["Costes Directos"])
with total_cols[2]:
    kpi_card("Margen Bruto", margen_bruto_total, margen_bruto_total / facturacion_total if facturacion_total else 0,
             benchmark=BENCHMARKS["Margen Bruto"])
with total_cols[3]:
    kpi_card("Costes Fijos", costes_fijos, costes_fijos / facturacion_total if facturacion_total else 0,
             benchmark=BENCHMARKS["Costes Fijos"])
with total_cols[4]:
    kpi_card("EBITDA", ebitda_total, ebitda_pct,
             benchmark=BENCHMARKS["EBITDA"])

# Comentario estratégico global
comentario_total = comentario_estrategico("EBITDA", ebitda_pct, BENCHMARKS["EBITDA"])
st.markdown(f"💬 **{comentario_total}**")

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
