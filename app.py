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
COLOR_ESTRELLA = "#FFD700"  # Dorado para ⭐
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

# -------------------------------
# Función estado de alerta
# -------------------------------
def get_estado(valor_pct, benchmark, tipo="coste"):
    if benchmark:
        min_bm, max_bm = benchmark
        if tipo == "coste":
            if valor_pct < min_bm:
                return COLOR_ESTRELLA, "⭐"
            elif min_bm <= valor_pct <= max_bm:
                return COLOR_VERDE, "✅"
            else:
                return COLOR_NARANJA, "⚠️"
        else:  # márgenes y EBITDA
            if valor_pct > max_bm:
                return COLOR_ESTRELLA, "⭐"
            elif min_bm <= valor_pct <= max_bm:
                return COLOR_VERDE, "✅"
            else:
                return COLOR_NARANJA, "⚠️"
    else:
        return COLOR_TEXTO, ""  # Sin símbolo ni color si no hay benchmark

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tipo="coste", tooltip=None):
    color, icono = get_estado(valor_pct, benchmark, tipo)
    if benchmark:
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
# Leer datos JSON
# -------------------------------
with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

param = data['parametros']
facturacion_total = data['resultados']['facturacion_total']
subactividad_permitida = param.get("subactividad_permitida_%", 15) / 100

# Mapeo líneas de negocio → benchmarks
mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# Función para cada bloque línea negocio
# -------------------------------
def bloque_linea(nombre_linea, datos_linea, benchmark_linea):
    st.markdown(f"### 🔽 {nombre_linea.upper()}")
    with st.expander(f"📂 Ajustes y Resultados - {nombre_linea}", expanded=False):

        # Sliders sobre KPI en una sola fila
        cols = st.columns(4)
        # Ticket Medio
        with cols[0]:
            nuevo_ticket = st.slider("Ticket Medio (€)", 
                                     min_value=int(datos_linea['ticket_medio'] * 0.5),
                                     max_value=int(datos_linea['ticket_medio'] * 1.5),
                                     value=int(datos_linea['ticket_medio']),
                                     step=1000,
                                     format="%d")
            kpi_card("Ticket Medio", nuevo_ticket, nuevo_ticket / facturacion_total,
                     tooltip="Valor medio por proyecto")

        # Unidades
        with cols[1]:
            nuevo_unidades = st.slider("Número de Unidades", 
                                       min_value=0, max_value=int(datos_linea['unidades']*2),
                                       value=int(datos_linea['unidades']), step=1)
            kpi_card("Número de Unidades", nuevo_unidades, nuevo_unidades / facturacion_total,
                     tooltip="Proyectos o ventas")

        # Personas
        with cols[2]:
            nuevo_personas = st.slider("Personas", 
                                       min_value=0, max_value=int(max(1, datos_linea['personas']*2)),
                                       value=int(datos_linea['personas']), step=1)
            kpi_card("Personas", nuevo_personas, nuevo_personas / facturacion_total,
                     tooltip="Número de personas asignadas")

        # Coste Medio por Persona
        with cols[3]:
            nuevo_coste_medio = st.slider("Coste Medio Persona (€)", 
                                          min_value=int(max(1000, datos_linea['coste_medio_persona'] * 0.8)),
                                          max_value=int(datos_linea['coste_medio_persona'] * 1.2),
                                          value=int(datos_linea['coste_medio_persona']),
                                          step=1000,
                                          format="%d")
            kpi_card("Coste Medio Persona", nuevo_coste_medio, 
                     (nuevo_coste_medio*nuevo_personas)/facturacion_total,
                     tooltip="Coste anual medio por persona")

        # Cálculos resultados
        facturacion = nuevo_ticket * nuevo_unidades
        costes_personal = nuevo_personas * nuevo_coste_medio
        costes_directos_pct = datos_linea['costes_directos_%']
        costes_directos = facturacion * (costes_directos_pct / 100) + costes_personal
        margen_bruto = facturacion - costes_directos

        # KPIs resultados
        st.subheader("📊 KPIs Resultados")
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_card("Facturación", facturacion, facturacion/facturacion_total,
                     tooltip="Facturación total línea")
        with col2:
            kpi_card("Costes Directos", costes_directos, costes_directos/facturacion_total,
                     benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None,
                     tipo="coste",
                     tooltip="Costes directos de la línea")
        with col3:
            kpi_card("Margen Bruto", margen_bruto, margen_bruto/facturacion_total,
                     benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None,
                     tipo="margen",
                     tooltip="Ingresos menos costes directos")

        # Nivel de actividad
        if datos_linea['jornadas_por_persona'] > 0 and nuevo_personas > 0:
            st.subheader("⏱️ Nivel de Actividad")
            jornadas_disponibles = nuevo_personas * datos_linea['jornadas_por_persona']
            jornadas_utilizadas = (facturacion / datos_linea['tarifa'])
            nivel_utilizacion = jornadas_utilizadas / jornadas_disponibles * 100
            benchmark_util = benchmark_linea['utilizacion'] if benchmark_linea else [0.6, 0.75]

            # Velocímetro
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=nivel_utilizacion,
                title={'text': "Utilización (%)"},
                gauge={
                    'axis': {'range': [0, 120]},
                    'bar': {'color': COLOR_NARANJA},
                    'steps': [
                        {'range': [0, benchmark_util[0]*100], 'color': COLOR_ESTRELLA},
                        {'range': [benchmark_util[0]*100, benchmark_util[1]*100], 'color': COLOR_VERDE},
                        {'range': [benchmark_util[1]*100, 120], 'color': COLOR_ROJO}
                    ]
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown(f"""
            📅 **Jornadas disponibles:** {int(jornadas_disponibles)}  
            ✅ **Jornadas utilizadas:** {int(jornadas_utilizadas)}  
            📊 **% Jornadas utilizadas:** {nivel_utilizacion:.1f}%  
            🔄 **Subactividad asumible ({int(subactividad_permitida*100)}%):** {int(jornadas_disponibles*subactividad_permitida)} jornadas  
            🚨 **Exceso Subactividad:** {max(0, int(jornadas_disponibles - jornadas_utilizadas - jornadas_disponibles*subactividad_permitida))} jornadas  
            💸 **Coste asociado:** {format_euro(max(0, (jornadas_disponibles - jornadas_utilizadas - jornadas_disponibles*subactividad_permitida)*nuevo_coste_medio/datos_linea['jornadas_por_persona']))}
            """)
        else:
            st.markdown("⚡ Sin nivel de actividad (100% uso supuesto)")

        # Gráfico cascada
        st.subheader(f"📉 Resumen Económico - {nombre_linea}")
        fig_cascada = go.Figure(go.Waterfall(
            name=nombre_linea,
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Facturación", "Costes Directos", "Margen Bruto"],
            textposition="outside",
            text=[format_euro(facturacion), format_euro(-costes_directos), format_euro(margen_bruto)],
            y=[facturacion, -costes_directos, margen_bruto],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_cascada.update_layout(
            title=f"{nombre_linea} - Facturación / Costes Directos / Margen Bruto",
            plot_bgcolor=COLOR_FONDO,
            paper_bgcolor=COLOR_FONDO,
            font=dict(color=COLOR_TEXTO),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_cascada, use_container_width=True)

        return facturacion, costes_directos, margen_bruto

# -------------------------------
# Bloques por línea de negocio
# -------------------------------
total_fact, total_costes, total_margen = 0, 0, 0
for nombre, datos in param['lineas_negocio'].items():
    benchmark_ln = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[nombre])
    f, c, m = bloque_linea(nombre, datos, benchmark_ln)
    total_fact += f
    total_costes += c
    total_margen += m

# -------------------------------
# Resumen Global líneas de negocio
# -------------------------------
with st.expander("📦 Resumen Global Líneas de Negocio", expanded=False):
    st.subheader("📊 KPIs Totales")
    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Facturación Total Líneas", total_fact, total_fact/facturacion_total)
    with col2:
        kpi_card("Costes Directos Totales", total_costes, total_costes/facturacion_total)
    with col3:
        kpi_card("Margen Bruto Total", total_margen, total_margen/facturacion_total)

    # Gráfico cascada global
    st.subheader("📉 Resumen Económico Total")
    fig_global = go.Figure(go.Waterfall(
        name="Total Líneas",
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Facturación Total", "Costes Directos Totales", "Margen Bruto Total"],
        textposition="outside",
        text=[format_euro(total_fact), format_euro(-total_costes), format_euro(total_margen)],
        y=[total_fact, -total_costes, total_margen],
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))
    fig_global.update_layout(
        title="Total Líneas de Negocio - Facturación / Costes Directos / Margen Bruto",
        plot_bgcolor=COLOR_FONDO,
        paper_bgcolor=COLOR_FONDO,
        font=dict(color=COLOR_TEXTO),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig_global, use_container_width=True)
