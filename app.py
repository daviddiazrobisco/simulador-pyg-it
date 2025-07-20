import streamlit as st
import json
import plotly.graph_objects as go

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="Simulador PyG IT - Implantación", page_icon="💻", layout="wide")

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

def get_estado(valor_pct, benchmark, tipo="normal"):
    """Devuelve color e icono según benchmark"""
    min_bm, max_bm = benchmark
    if tipo == "coste":
        if valor_pct < min_bm:
            return COLOR_VERDE, "⭐"
        elif min_bm <= valor_pct <= max_bm:
            return COLOR_VERDE, "✅"
        else:
            return COLOR_NARANJA, "⚠️"
    else:  # márgenes y EBITDA
        if valor_pct < min_bm:
            return COLOR_NARANJA, "⚠️"
        elif min_bm <= valor_pct <= max_bm:
            return COLOR_VERDE, "✅"
        else:
            return COLOR_VERDE, "⭐"

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tooltip=None, tipo="normal"):
    """Genera una tarjeta KPI con color dinámico y popup"""
    color, icono = COLOR_VERDE, "✅"
    comparativa = ""
    if benchmark:
        color, icono = get_estado(valor_pct, benchmark, tipo=tipo)
        comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[1]*100)}%</small>"
    else:
        comparativa = "<br><small>Sin benchmark definido</small>"

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
with open('data/presupuesto_it_2025.json') as f:
    presupuesto = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

# Mapeo líneas presupuesto → benchmarks
mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# Datos línea Implantación
# -------------------------------
linea_nombre = "Implantación"
datos_linea = presupuesto['parametros']['lineas_negocio'][linea_nombre]
benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])

facturacion_objetivo = presupuesto['parametros']['facturacion_objetivo']
subactividad_permitida_pct = presupuesto['parametros']['subactividad_permitida_%']

# -------------------------------
# Bloque plegable
# -------------------------------
with st.expander(f"📦 {linea_nombre} (haz clic para ajustar)", expanded=False):

    st.subheader(f"🎯 Ajustes - {linea_nombre}")

    # Sliders sobre tarjetas KPI
    cols = st.columns(2)
    with cols[0]:
        tarifa = st.slider("Tarifa (€)", min_value=int(datos_linea['tarifa']*0.5), max_value=int(datos_linea['tarifa']*1.5),
                           value=int(datos_linea['tarifa']), step=10, format="%d")
        kpi_card("Tarifa", tarifa, 0, tooltip="Precio por jornada")
    with cols[1]:
        ticket_medio = st.slider("Ticket Medio (€)", min_value=int(datos_linea['ticket_medio']*0.5),
                                 max_value=int(datos_linea['ticket_medio']*1.5),
                                 value=int(datos_linea['ticket_medio']), step=1000, format="%d")
        kpi_card("Ticket Medio", ticket_medio, 0, tooltip="Valor medio de los proyectos")

    cols = st.columns(3)
    with cols[0]:
        unidades = st.slider("Número de Proyectos", min_value=0, max_value=datos_linea['unidades']*2,
                             value=datos_linea['unidades'], step=1)
        kpi_card("Nº Proyectos", unidades, 0, tooltip="Número total de proyectos")
    with cols[1]:
        personas = st.slider("Personas", min_value=0, max_value=datos_linea['personas']*2,
                             value=datos_linea['personas'], step=1)
        kpi_card("Personas", personas, 0, tooltip="Número de personas asignadas")
    with cols[2]:
        coste_medio_persona = st.slider("Coste Medio Persona (€)", min_value=int(datos_linea['coste_medio_persona']*0.8),
                                        max_value=int(datos_linea['coste_medio_persona']*1.2),
                                        value=int(datos_linea['coste_medio_persona']), step=500, format="%d")
        kpi_card("Coste Medio Persona", coste_medio_persona, 0, tooltip="Coste medio por persona")

    # -------------------------------
    # Cálculos
    # -------------------------------
    facturacion = ticket_medio * unidades
    coste_personas = personas * coste_medio_persona
    costes_directos = coste_personas + (facturacion * datos_linea['costes_directos_%'] / 100)
    margen_bruto = facturacion - costes_directos
    margen_bruto_pct = margen_bruto / facturacion if facturacion else 0

    # -------------------------------
    # KPIs resultados
    # -------------------------------
    st.subheader("📊 Resultados")
    res_cols = st.columns(3)
    with res_cols[0]:
        kpi_card("Facturación", facturacion, facturacion / facturacion_objetivo, benchmark_linea.get("margen_bruto") if benchmark_linea else None, tipo="margen")
    with res_cols[1]:
        kpi_card("Costes Directos", costes_directos, costes_directos / facturacion if facturacion else 0,
                 benchmark_linea.get("margen_bruto") if benchmark_linea else None, tipo="coste")
    with res_cols[2]:
        kpi_card("Margen Bruto", margen_bruto, margen_bruto_pct,
                 benchmark_linea.get("margen_bruto") if benchmark_linea else None, tipo="margen")

    # -------------------------------
    # Velocímetro nivel de actividad
    # -------------------------------
    st.subheader("📈 Nivel de Actividad")
    if datos_linea['jornadas_por_persona'] > 0 and personas > 0:
        jornadas_disponibles = personas * datos_linea['jornadas_por_persona']
        jornadas_utilizadas = (ticket_medio / tarifa) * unidades
        porcentaje_utilizacion = jornadas_utilizadas / jornadas_disponibles if jornadas_disponibles else 0

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=porcentaje_utilizacion*100,
            gauge={
                'axis': {'range': [0, 120]},
                'bar': {'color': COLOR_NARANJA},
                'steps': [
                    {'range': [0, subactividad_permitida_pct], 'color': COLOR_ROJO},
                    {'range': [subactividad_permitida_pct, 100], 'color': COLOR_VERDE},
                    {'range': [100, 120], 'color': COLOR_ROJO}
                ],
            },
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Utilización (%)"}
        ))
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        📅 Jornadas disponibles: {int(jornadas_disponibles)}  
        ✅ Jornadas utilizadas: {int(jornadas_utilizadas)}  
        📊 % Jornadas utilizadas: {round(porcentaje_utilizacion*100, 1)}%  
        🔄 Subactividad asumible ({subactividad_permitida_pct}%): {int(jornadas_disponibles*subactividad_permitida_pct/100)} jornadas  
        🚨 Exceso Subactividad: {max(0, int(jornadas_disponibles - jornadas_utilizadas - (jornadas_disponibles*subactividad_permitida_pct/100)))} jornadas  
        💸 Coste asociado: {format_euro((jornadas_disponibles - jornadas_utilizadas)*coste_medio_persona) if porcentaje_utilizacion<1 else '0 €'}
        """)
    else:
        st.info("Sin nivel de actividad (100% uso supuesto)")

    # -------------------------------
    # Gráfico cascada
    # -------------------------------
    st.subheader("📊 Gráfico Cascada")
    fig_cascada = go.Figure(go.Waterfall(
        name="PyG Implantación",
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Facturación", "Costes Directos", "Margen Bruto"],
        textposition="outside",
        text=[format_euro(facturacion), format_euro(-costes_directos), format_euro(margen_bruto)],
        y=[facturacion, -costes_directos, margen_bruto],
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))
    fig_cascada.update_layout(
        title="Cuenta de Resultados - Implantación",
        plot_bgcolor=COLOR_FONDO,
        paper_bgcolor=COLOR_FONDO,
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_cascada, use_container_width=True)
