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
linea = data['parametros']['lineas_negocio']["Implantación"]
resultados = data['resultados']
facturacion_total = resultados['facturacion_total']
costes_fijos = resultados['costes_fijos']

# -------------------------------
# Benchmarks (simplificado aquí)
benchmarks = {
    "Implantación": {
        "Importe Medio Proyecto": {"min": 180000, "max": 220000},
        "Tarifa Media Jornada": {"min": 700, "max": 900},
        "Coste Medio Persona": {"min": 45000, "max": 55000},
        "Nivel Actividad": {"min": 70, "max": 100},
        "Margen Bruto (%)": {"min": 25, "max": 30}
    }
}

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

        # Sliders
        importe_proyecto = st.slider("💶 Importe Medio Proyecto (€)", 100000, 300000, 200000, step=5000, format="%d")
        kpi_card("Importe Medio Proyecto", importe_proyecto, importe_proyecto / facturacion_total,
                 benchmark=benchmarks["Implantación"]["Importe Medio Proyecto"])

        tarifa_jornada = st.slider("💵 Tarifa Media Jornada (€)", 500, 1200, int(linea['tarifa']), step=50, format="%d")
        kpi_card("Tarifa Media Jornada", tarifa_jornada, tarifa_jornada / facturacion_total,
                 benchmark=benchmarks["Implantación"]["Tarifa Media Jornada"])

        num_proyectos = st.slider("📦 Nº Proyectos", 5, 30, int(linea['unidades']), step=1)
        kpi_card("Nº Proyectos", num_proyectos, num_proyectos / 100)

        num_personas = st.slider("👥 Nº Personas", 3, 15, int(linea['personas']), step=1)
        kpi_card("Nº Personas", num_personas, num_personas / 100)

        coste_medio_persona = st.slider("👔 Coste Medio Persona (€)", 40000, 80000, int(linea['coste_medio_persona']), step=1000, format="%d")
        kpi_card("Coste Medio Persona", coste_medio_persona, coste_medio_persona / facturacion_total,
                 benchmark=benchmarks["Implantación"]["Coste Medio Persona"])

        # Cálculos
        jornadas_proyecto = importe_proyecto / tarifa_jornada
        jornadas_facturadas = num_proyectos * jornadas_proyecto
        facturacion_implantacion = jornadas_facturadas * tarifa_jornada

        coste_personal = num_personas * coste_medio_persona
        otros_costes = facturacion_implantacion * linea['costes_directos_%']
        costes_directos_implantacion = coste_personal + otros_costes
        margen_implantacion = facturacion_implantacion - costes_directos_implantacion
        margen_pct = (margen_implantacion / facturacion_implantacion) * 100 if facturacion_implantacion else 0

        # Nivel de Actividad
        jornadas_disponibles = num_personas * 220
        nivel_actividad = (jornadas_facturadas / jornadas_disponibles) * 100 if jornadas_disponibles else 0

        if nivel_actividad < 70:
            estado_actividad = "⭐ Subactividad"
            color_act = COLOR_ROJO
        elif nivel_actividad > 100:
            estado_actividad = "⚠️ Sobreactividad"
            color_act = COLOR_NARANJA
        else:
            estado_actividad = "✅ Óptimo"
            color_act = COLOR_VERDE

        # Gráfico barra horizontal nivel actividad
        fig_barra = go.Figure(go.Bar(
            x=[nivel_actividad],
            y=["Nivel de Actividad"],
            orientation='h',
            marker=dict(
                color=[color_act],
                line=dict(color=COLOR_TEXTO, width=1)
            ),
            text=f"{round(nivel_actividad, 1)}%",
            textposition="outside"
        ))
        fig_barra.update_layout(
            xaxis=dict(range=[0, 120], title="%", showgrid=False),
            yaxis=dict(showgrid=False),
            title=f"🔥 Nivel de Actividad {estado_actividad}",
            plot_bgcolor=COLOR_FONDO,
            paper_bgcolor=COLOR_FONDO,
            font=dict(color=COLOR_TEXTO),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_barra, use_container_width=True)

        # Subactividad informativa
        subactividad_asumible = jornadas_disponibles * 0.15
        exceso_subactividad = max(jornadas_disponibles - jornadas_facturadas - subactividad_asumible, 0)
        coste_subactividad = exceso_subactividad * (coste_medio_persona / 220)

        st.markdown(f"**🔄 Subactividad asumible (15%)**: {int(subactividad_asumible)} jornadas")
        st.markdown(f"**🚨 Exceso Subactividad**: {int(exceso_subactividad)} jornadas")
        st.markdown(f"**💸 Coste asociado**: {format_euro(coste_subactividad)}")

        # KPIs resumen línea
        st.subheader("📊 KPIs Implantación")
        kpi_card("Facturación Implantación", facturacion_implantacion, facturacion_implantacion / facturacion_total)
        kpi_card("Costes Directos Implantación", costes_directos_implantacion, costes_directos_implantacion / facturacion_total)
        kpi_card("Margen Implantación", margen_implantacion, margen_pct / 100,
                 benchmark=benchmarks["Implantación"]["Margen Bruto (%)"])

        # Mini gráfico cascada
        fig_implantacion = go.Figure(go.Waterfall(
            name="Implantación",
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Ingresos", "Costes Directos", "Margen"],
            textposition="outside",
            text=[format_euro(facturacion_implantacion), format_euro(-costes_directos_implantacion),
                  format_euro(margen_implantacion)],
            y=[facturacion_implantacion, -costes_directos_implantacion, margen_implantacion],
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
        kpi_card("Margen Bruto", resultados['margen_bruto'], resultados['margen_bruto']/facturacion_total)
    with col4:
        kpi_card("Costes Fijos", costes_fijos, costes_fijos/facturacion_total)
    with col5:
        ebitda = resultados['margen_bruto'] - costes_fijos
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
