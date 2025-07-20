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
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

def get_estado(kpi_name, valor, benchmark):
    min_bm, max_bm = benchmark["min"], benchmark["max"]
    if "coste" in kpi_name.lower():
        if valor < min_bm:
            return COLOR_VERDE, "⭐"
        elif min_bm <= valor <= max_bm:
            return COLOR_VERDE, "✅"
        else:
            return COLOR_ROJO, "⚠️"
    else:
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
# Cargar datos
# -------------------------------
with open('presupuesto_it_2025.json') as f:
    data = json.load(f)
lineas_negocio = data['parametros']['lineas_negocio']

with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

resultados = data['resultados']
facturacion_total = resultados['facturacion_total']
costes_fijos = resultados['costes_fijos']

# -------------------------------
# Pantalla dividida
# -------------------------------
col_izq, col_der = st.columns([1, 1.5])

# -------------------------------
# Columna Izquierda: Implantación
# -------------------------------
with col_izq:
    with st.expander("🔽 Implantación (Haz clic para ajustar)", expanded=False):
        st.markdown("Ajusta las variables de la línea Implantación:")

        datos_implantacion = lineas_negocio["Implantación"]
        unidades = datos_implantacion['unidades']
        personas = datos_implantacion['personas']

        # Slider: Tarifa Media Proyecto
        tarifa = st.slider(
            "💵 Tarifa Media Proyecto (€)", 
            min_value=500, max_value=1200, value=int(datos_implantacion['tarifa']), step=50,
            format="%d"
        )
        kpi_card("Tarifa Media Proyecto", tarifa, tarifa / facturacion_total,
                 benchmark=benchmarks["Servicios"]["Precio Medio Proyecto"])

        # Slider: Coste Medio Persona
        coste_persona = st.slider(
            "👥 Coste Medio Persona (€)", 
            min_value=40000, max_value=80000, value=int(datos_implantacion['coste_medio_persona']), step=1000,
            format="%d"
        )
        kpi_card("Coste Medio Persona", coste_persona, coste_persona / facturacion_total,
                 benchmark=benchmarks["Servicios"]["Coste Medio Persona"])

        # Slider: Nivel de Actividad
        nivel_actividad = st.slider(
            "🔥 Nivel de Actividad (%)", 
            min_value=50, max_value=110, value=85, step=5,
            format="%d%%"
        )
        kpi_card("Nivel Actividad", nivel_actividad, nivel_actividad / 100,
                 benchmark=benchmarks["Servicios"]["Nivel Actividad"])

        # KPIs calculados
        actividad_real = unidades * (nivel_actividad / 100)
        implantacion_facturacion = tarifa * actividad_real
        implantacion_costes_directos = coste_persona * personas
        implantacion_margen = implantacion_facturacion - implantacion_costes_directos
        margen_pct = implantacion_margen / implantacion_facturacion if implantacion_facturacion else 0

        st.subheader("📊 KPIs Implantación")
        kpi_card("Facturación Implantación", implantacion_facturacion, implantacion_facturacion / facturacion_total)
        kpi_card("Costes Directos Implantación", implantacion_costes_directos, implantacion_costes_directos / facturacion_total)
        kpi_card("Margen Implantación", implantacion_margen, margen_pct)

        # Mini gráfico cascada
        fig_implantacion = go.Figure(go.Waterfall(
            name="Implantación",
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Ingresos", "Costes Directos", "Margen"],
            textposition="outside",
            text=[format_euro(implantacion_facturacion), format_euro(-implantacion_costes_directos),
                  format_euro(implantacion_margen)],
            y=[implantacion_facturacion, -implantacion_costes_directos, implantacion_margen],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_implantacion.update_layout(
            title="Gráfico Cascada - Implantación",
            plot_bgcolor=COLOR_FONDO,
            paper_bgcolor=COLOR_FONDO,
            font=dict(color=COLOR_TEXTO),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_implantacion, use_container_width=True)

# -------------------------------
# Recalcular EBITDA global
# -------------------------------
margen_bruto = resultados['margen_bruto']  # fijo
ebitda = margen_bruto - costes_fijos

# -------------------------------
# Columna Derecha: Resultados Globales
# -------------------------------
with col_der:
    st.header("📊 Resultados PyG Global")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        kpi_card("Facturación Total", facturacion_total, 1.0)
    with col2:
        kpi_card("Costes Directos", resultados['costes_directos'], resultados['costes_directos']/facturacion_total)
    with col3:
        kpi_card("Margen Bruto", margen_bruto, margen_bruto/facturacion_total)
    with col4:
        kpi_card("Costes Fijos", costes_fijos, costes_fijos/facturacion_total)
    with col5:
        kpi_card("EBITDA", ebitda, ebitda/facturacion_total)

    # Gráfico cascada global
    fig_global = go.Figure(go.Waterfall(
        name="PyG Global",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
        textposition="outside",
        text=[format_euro(facturacion_total), format_euro(-resultados['costes_directos']),
              format_euro(-costes_fijos), format_euro(ebitda)],
        y=[facturacion_total, -resultados['costes_directos'], -costes_fijos, ebitda],
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
