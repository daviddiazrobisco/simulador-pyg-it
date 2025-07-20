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

# -------------------------------
# Función formateo números europeos
# -------------------------------
def format_euro(valor):
    """Formatea número con puntos miles, sin decimales y €"""
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

def get_estado(kpi_name, valor, benchmark):
    """Devuelve color e icono según tipo de KPI"""
    min_bm, max_bm = benchmark["min"], benchmark["max"]
    if "coste" in kpi_name.lower():
        # En Costes menos es mejor
        if valor < min_bm:
            return COLOR_VERDE, "⭐"
        elif min_bm <= valor <= max_bm:
            return COLOR_VERDE, "✅"
        else:
            return COLOR_ROJO, "⚠️"
    else:
        # En Márgenes, Precios más es mejor
        if valor < min_bm:
            return COLOR_ROJO, "⚠️"
        elif min_bm <= valor <= max_bm:
            return COLOR_VERDE, "✅"
        else:
            return COLOR_NARANJA, "⭐"

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tooltip=None):
    """Genera una tarjeta KPI con color dinámico y popup"""
    color, icono = COLOR_VERDE, "✅"
    comparativa = ""
    if benchmark:
        color, icono = get_estado(nombre, valor_abs, benchmark)
        comparativa = f"<br><small>Benchmark: {format_euro(benchmark['min'])} – {format_euro(benchmark['max'])}</small>"

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

# Normalizar claves a minúsculas
param_lower = {k.lower(): v for k, v in param.items()}

with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

# -------------------------------
# Ajustes iniciales
# -------------------------------
facturacion = int(result['facturacion_total'])
costes_fijos = sum(param['costes_fijos'].values())

# -------------------------------
# Pantalla dividida
# -------------------------------
col_izq, col_der = st.columns([1, 1.5])  # Columna izquierda más estrecha

# -------------------------------
# Columna Izquierda: Línea Servicios
# -------------------------------
with col_izq:
    with st.expander("🔽 Servicios (Haz clic para ajustar)", expanded=False):
        st.markdown("Ajusta las variables de la línea Servicios:")

        # Sliders
        precio_medio = st.slider(
            "💵 Precio Medio Proyecto (€)", 
            min_value=500, max_value=1000, value=750, step=50,
            format="%d"
        )
        coste_persona = st.slider(
            "👥 Coste Medio Persona (€)", 
            min_value=40000, max_value=60000, value=50000, step=1000,
            format="%d"
        )
        nivel_actividad = st.slider(
            "🔥 Nivel de Actividad (%)", 
            min_value=50, max_value=110, value=85, step=5,
            format="%d%%"
        )

        # Datos de Servicios desde JSON (insensible a mayúsculas)
        servicios_data = param_lower.get('servicios', {})
        num_proyectos = servicios_data.get('num_proyectos', 0)
        num_personas = servicios_data.get('num_personas', 0)

        # KPIs calculados
        servicios_facturacion = precio_medio * num_proyectos
        servicios_costes_directos = coste_persona * num_personas
        servicios_margen = servicios_facturacion - servicios_costes_directos
        margen_pct = servicios_margen / servicios_facturacion if servicios_facturacion else 0

        st.subheader("📊 KPIs Servicios")
        kpi_card("Facturación Servicios", servicios_facturacion, servicios_facturacion / facturacion)
        kpi_card("Costes Directos Servicios", servicios_costes_directos, servicios_costes_directos / facturacion,
                 benchmark=benchmarks["Servicios"]["Coste Medio Persona"])
        kpi_card("Margen Servicios", servicios_margen, margen_pct,
                 benchmark=benchmarks["Servicios"]["Precio Medio Proyecto"])

        # Mini gráfico cascada
        fig_servicios = go.Figure(go.Waterfall(
            name="Servicios",
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Ingresos", "Costes Directos", "Margen"],
            textposition="outside",
            text=[format_euro(servicios_facturacion), format_euro(-servicios_costes_directos),
                  format_euro(servicios_margen)],
            y=[servicios_facturacion, -servicios_costes_directos, servicios_margen],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_servicios.update_layout(
            title="Gráfico Cascada - Servicios",
            plot_bgcolor=COLOR_FONDO,
            paper_bgcolor=COLOR_FONDO,
            font=dict(color=COLOR_TEXTO),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_servicios, use_container_width=True)

# -------------------------------
# Recalcular resultados globales
# -------------------------------
margen_bruto = facturacion - result['costes_directos']
ebitda = margen_bruto - costes_fijos

# -------------------------------
# Columna Derecha: Resultados Globales
# -------------------------------
with col_der:
    st.header("📊 Resultados PyG Global")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        kpi_card("Facturación Total", facturacion, 1.0)
    with col2:
        kpi_card("Costes Directos", result['costes_directos'], result['costes_directos']/facturacion)
    with col3:
        kpi_card("Margen Bruto", margen_bruto, margen_bruto/facturacion)
    with col4:
        kpi_card("Costes Fijos", costes_fijos, costes_fijos/facturacion)
    with col5:
        kpi_card("EBITDA", ebitda, ebitda/facturacion)

    # Gráfico cascada global
    fig_global = go.Figure(go.Waterfall(
        name="PyG Global",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
        textposition="outside",
        text=[format_euro(facturacion), format_euro(-result['costes_directos']),
              format_euro(-costes_fijos), format_euro(ebitda)],
        y=[facturacion, -result['costes_directos'], -costes_fijos, ebitda],
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))
    fig_global.update_layout(
        title="Cuenta de Resultados - Global",
        plot_bgcolor=COLOR_FONDO,
        paper_bgcolor=COLOR_FONDO,
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_global, use_container_width=True)
