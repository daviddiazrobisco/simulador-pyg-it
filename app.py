import streamlit as st
import json
import plotly.graph_objects as go

# -------------------------------
# Cargar datos y benchmarks
# -------------------------------
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

with open('presupuesto_it_2025.json') as f:
    data = json.load(f)

# Datos iniciales para Consultoría
consultoria = data['parametros']['lineas_negocio']['consultoria']

# -------------------------------
# Funciones auxiliares
# -------------------------------
def format_euro(valor):
    """Formatea número con puntos miles y símbolo €"""
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

def get_estado(valor, benchmark, tipo='mas_es_mejor'):
    """Determina símbolo y color según benchmark"""
    min_val, media_val, max_val = benchmark
    if tipo == 'mas_es_mejor':
        if valor < min_val: return "⚠️", "#D33F49"  # rojo
        elif valor <= max_val: return "✅", "#144C44"  # verde
        else: return "⭐", "#fb9200"  # naranja
    else:
        if valor > max_val: return "⚠️", "#D33F49"
        elif valor >= min_val: return "✅", "#144C44"
        else: return "⭐", "#fb9200"

def calcular_consultoria(tarifa, ticket, unidades, personas, coste_persona, costes_directos_pct, jornadas_persona):
    facturacion = ticket * unidades
    costes_personas = personas * coste_persona
    costes_directos = (costes_directos_pct / 100) * facturacion
    total_costes_directos = costes_personas + costes_directos
    margen_bruto = facturacion - total_costes_directos

    # Nivel de actividad
    if jornadas_persona > 0 and personas > 0:
        jornadas_totales = jornadas_persona * personas
        jornadas_utilizadas = (ticket / tarifa) * unidades
        subactividad_jornadas = jornadas_totales - jornadas_utilizadas
        if jornadas_totales > 0:
            nivel_actividad = (jornadas_utilizadas / jornadas_totales) * 100
        else:
            nivel_actividad = 100
    else:
        nivel_actividad = None  # No aplica

    return {
        "facturacion": facturacion,
        "costes_directos": total_costes_directos,
        "margen_bruto": margen_bruto,
        "nivel_actividad": nivel_actividad
    }

# -------------------------------
# Bloque Consultoría
# -------------------------------
with st.expander("🔽 Consultoría (Haz clic para ajustar)", expanded=False):
    st.markdown("Ajusta los parámetros para la línea de negocio **Consultoría** y observa el impacto en tiempo real.")

    # Sliders
    tarifa = st.slider("Tarifa (€)", 30000, 70000, int(consultoria['tarifa']), step=1000)
    ticket = st.slider("Ticket medio (€)", 30000, 70000, int(consultoria['ticket_medio']), step=1000)
    unidades = st.slider("Número de proyectos", 1, 50, int(consultoria['unidades']), step=1)
    personas = st.slider("Número de personas", 0, 20, int(consultoria['personas']), step=1)
    coste_persona = st.slider("Coste medio persona (€)", 30000, 80000, int(consultoria['coste_medio_persona']), step=1000)
    costes_pct = st.slider("Costes directos (%)", 10, 70, int(consultoria['costes_directos_%']), step=1)

    # Cálculos
    resultados = calcular_consultoria(tarifa, ticket, unidades, personas, coste_persona, costes_pct, consultoria['jornadas_por_persona'])

    # KPIs resumen
    st.markdown("### 📊 Resultados Línea Consultoría")
    col1, col2, col3 = st.columns(3)
    with col1:
        simbolo, color = get_estado(resultados['facturacion'], benchmarks['lineas_negocio']['consultoria']['precio_jornada'], 'mas_es_mejor')
        st.metric("Facturación", format_euro(resultados['facturacion']), delta=f"{simbolo}")
    with col2:
        simbolo, color = get_estado(resultados['costes_directos'], benchmarks['lineas_negocio']['consultoria']['margen_bruto'], 'menos_es_mejor')
        st.metric("Costes Directos", format_euro(resultados['costes_directos']), delta=f"{simbolo}")
    with col3:
        simbolo, color = get_estado(resultados['margen_bruto'], benchmarks['lineas_negocio']['consultoria']['ebitda'], 'mas_es_mejor')
        st.metric("Margen Bruto", format_euro(resultados['margen_bruto']), delta=f"{simbolo}")

    # Velocímetro Nivel Actividad
    if resultados['nivel_actividad'] is not None:
        min_sub, media_sub, max_sub = benchmarks['lineas_negocio']['consultoria']['utilizacion']
        gauge_color = "#144C44" if min_sub <= resultados['nivel_actividad'] <= max_sub else "#D33F49"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=resultados['nivel_actividad'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Nivel de Actividad (%)"},
            gauge={
                'axis': {'range': [0, 120]},
                'bar': {'color': gauge_color},
                'steps': [
                    {'range': [0, min_sub * 100], 'color': "#fb9200"},
                    {'range': [min_sub * 100, max_sub * 100], 'color': "#144C44"},
                    {'range': [max_sub * 100, 100], 'color': "#fb9200"},
                    {'range': [100, 120], 'color': "#D33F49"}
                ]
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

    # Gráfico cascada
    fig_cascada = go.Figure(go.Waterfall(
        name="Consultoría",
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
        title="Gráfico Cascada - Consultoría",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color="#333333")
    )
    st.plotly_chart(fig_cascada, use_container_width=True)
