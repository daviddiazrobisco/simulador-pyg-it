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

def get_estado(valor, benchmark, tipo='mas_es_mejor'):
    """Devuelve color e icono según benchmark"""
    if not benchmark:
        return COLOR_GRIS, "🔗"
    min_bm, med_bm, max_bm = benchmark
    if tipo == 'mas_es_mejor':
        if valor < min_bm: return COLOR_ROJO, "⚠️"
        elif valor <= max_bm: return COLOR_VERDE, "✅"
        else: return COLOR_NARANJA, "⭐"
    else:
        if valor > max_bm: return COLOR_ROJO, "⚠️"
        elif valor >= min_bm: return COLOR_VERDE, "✅"
        else: return COLOR_NARANJA, "⭐"

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tooltip=None):
    """Genera una tarjeta KPI con color dinámico y popup"""
    color, icono = COLOR_VERDE, "✅"
    comparativa = ""
    if benchmark:
        color, icono = get_estado(valor_pct, benchmark)
        comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[2]*100)}%</small>"
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
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

lineas_negocio = data['parametros']['lineas_negocio']
implantacion = lineas_negocio['Implantación']

# Mapeo líneas → benchmarks
mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}
nombre_benchmark = mapa_lineas_benchmark.get("Implantación")
benchmark_linea = benchmarks['lineas_negocio'].get(nombre_benchmark, {})

# -------------------------------
# Cálculos Implantación
# -------------------------------
def calcular_implantacion(tarifa, ticket, unidades, personas, coste_persona, costes_pct, jornadas_persona):
    facturacion = ticket * unidades
    costes_personas = personas * coste_persona
    costes_directos = (costes_pct / 100) * facturacion
    total_costes_directos = costes_personas + costes_directos
    margen_bruto = facturacion - total_costes_directos

    if jornadas_persona > 0 and personas > 0:
        jornadas_totales = jornadas_persona * personas
        jornadas_utilizadas = (ticket / tarifa) * unidades
        subactividad_jornadas = jornadas_totales - jornadas_utilizadas
        nivel_actividad = (jornadas_utilizadas / jornadas_totales) * 100
    else:
        jornadas_totales = jornadas_utilizadas = subactividad_jornadas = nivel_actividad = None

    return {
        "facturacion": facturacion,
        "costes_directos": total_costes_directos,
        "margen_bruto": margen_bruto,
        "jornadas_totales": jornadas_totales,
        "jornadas_utilizadas": jornadas_utilizadas,
        "subactividad_jornadas": subactividad_jornadas,
        "nivel_actividad": nivel_actividad
    }

# -------------------------------
# UI Bloque Implantación
# -------------------------------
with st.expander("🔽 IMPLANTACIÓN (haz clic para ajustar)", expanded=False):
    st.markdown("Ajusta los parámetros para la línea de negocio **Implantación** y observa el impacto en tiempo real.")

    # Sliders + KPI
    tarifa = st.slider("Tarifa (€)", 500, 1500, int(implantacion['tarifa']), step=50)
    kpi_card("Tarifa", tarifa, 0, benchmark_linea.get('precio_jornada'))

    ticket = st.slider("Ticket Medio (€)", 100000, 500000, int(implantacion['ticket_medio']), step=10000)
    kpi_card("Ticket Medio", ticket, 0)

    unidades = st.slider("Número de Unidades", 1, 30, int(implantacion['unidades']), step=1)
    kpi_card("Unidades", unidades, 0)

    personas = st.slider("Número de Personas", 0, 60, int(implantacion['personas']), step=1)
    kpi_card("Personas", personas, 0)

    coste_persona = st.slider("Coste Medio Persona (€)", 40000, 80000, int(implantacion['coste_medio_persona']), step=1000)
    kpi_card("Coste Medio Persona", coste_persona, 0)

    costes_pct = st.slider("Costes Directos (%)", 0, 70, int(implantacion['costes_directos_%']), step=1)
    kpi_card("Costes Directos (%)", costes_pct, 0, benchmark_linea.get('margen_bruto'), tooltip="Costes directos como % sobre facturación")

    # Cálculos
    resultados = calcular_implantacion(tarifa, ticket, unidades, personas, coste_persona, costes_pct, implantacion['jornadas_por_persona'])

    # KPIs resumen
    st.markdown("### 📊 Resultados Línea Implantación")
    col1, col2, col3 = st.columns(3)
    with col1:
        kpi_card("Facturación", resultados['facturacion'], resultados['facturacion'] / data['resultados']['facturacion_total'])
    with col2:
        kpi_card("Costes Directos", resultados['costes_directos'], resultados['costes_directos'] / resultados['facturacion'], benchmark_linea.get('margen_bruto'))
    with col3:
        kpi_card("Margen Bruto", resultados['margen_bruto'], resultados['margen_bruto'] / resultados['facturacion'], benchmark_linea.get('ebitda'))

    # Velocímetro actividad
    if resultados['nivel_actividad'] is not None:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=resultados['nivel_actividad'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Nivel de Actividad (%)"},
            gauge={
                'axis': {'range': [0, 120]},
                'bar': {'color': COLOR_VERDE},
                'steps': [
                    {'range': [0, 70], 'color': COLOR_NARANJA},
                    {'range': [70, 100], 'color': COLOR_VERDE},
                    {'range': [100, 120], 'color': COLOR_ROJO}
                ]
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Texto adicional
        st.markdown(f"""
        📅 Jornadas disponibles: {int(resultados['jornadas_totales'])}  
        ✅ Jornadas utilizadas: {int(resultados['jornadas_utilizadas'])}  
        📊 % Jornadas utilizadas: {round(resultados['nivel_actividad'],1)}%  
        🔄 Subactividad asumible (15%): {int(resultados['jornadas_totales']*0.15)} jornadas  
        🚨 Exceso Subactividad: {max(0, int(resultados['subactividad_jornadas'] - resultados['jornadas_totales']*0.15))} jornadas  
        💸 Coste asociado: {format_euro((resultados['subactividad_jornadas'] - resultados['jornadas_totales']*0.15)*coste_persona/214) if resultados['nivel_actividad'] < 100 else '0 €'}
        """)
    else:
        st.markdown("⏱️ Sin nivel de actividad (100% uso supuesto)")

    # Gráfico cascada
    fig_cascada = go.Figure(go.Waterfall(
        name="Implantación",
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Facturación", "Costes Directos", "Margen Bruto"],
        textposition="outside",
        text=[format_euro(resultados['facturacion']),
              format_euro(-resultados['costes_directos']),
              format_euro(resultados['margen_bruto'])],
        y=[resultados['facturacion'], -resultados['costes_directos'], resultados['margen_bruto']],
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))
    fig_cascada.update_layout(
        title="Gráfico Cascada - Implantación",
        plot_bgcolor=COLOR_FONDO,
        paper_bgcolor=COLOR_FONDO,
        font=dict(color=COLOR_TEXTO)
    )
    st.plotly_chart(fig_cascada, use_container_width=True)
