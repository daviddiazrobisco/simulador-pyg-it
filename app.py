import streamlit as st
import json
import plotly.graph_objects as go

# -------------------------------
# Cargar datos y benchmarks
# -------------------------------
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)

# -------------------------------
# Mapeo nombres presupuesto -> benchmark
# -------------------------------
nombre_benchmark = {
    "Implantacion": "consultoria",  # sin tilde
    "Licencias": "software",
    "Hot Line": "mixto"
}

# -------------------------------
# Normalizar claves líneas de negocio
# -------------------------------
lineas_negocio = {k.strip().title(): v for k, v in data['parametros']['lineas_negocio'].items()}

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

def calcular_linea(tarifa, ticket, unidades, personas, coste_persona, costes_directos_pct, jornadas_persona):
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

def bloque_linea(nombre_linea, datos_linea, benchmark_linea):
    with st.expander(f"🔽 {nombre_linea} (Haz clic para ajustar)", expanded=False):
        st.markdown(f"Ajusta los parámetros para la línea de negocio **{nombre_linea}** y observa el impacto en tiempo real.")

        # Sliders + KPIs
        tarifa = st.slider("Tarifa (€)", 500, 2000, int(datos_linea['tarifa']), step=50)
        ticket = st.slider("Ticket medio (€)", 10000, 600000, int(datos_linea['ticket_medio']), step=5000)
        unidades = st.slider("Número de proyectos", 1, 100, int(datos_linea['unidades']), step=1)
        personas = st.slider("Número de personas", 0, 100, int(datos_linea['personas']), step=1)
        coste_persona = st.slider("Coste medio persona (€)", 30000, 90000, int(datos_linea['coste_medio_persona']), step=1000)
        costes_pct = st.slider("Costes directos (%)", 0, 70, int(datos_linea['costes_directos_%']), step=1)

        # Cálculos
        resultados = calcular_linea(tarifa, ticket, unidades, personas, coste_persona, costes_pct, datos_linea['jornadas_por_persona'])

        # KPIs resumen en tarjetas
        st.markdown(f"### 📊 Resultados Línea {nombre_linea}")
        col1, col2, col3 = st.columns(3)
        with col1:
            simbolo, color = get_estado(resultados['facturacion'], benchmark_linea['precio_jornada'], 'mas_es_mejor')
            st.markdown(f"<div style='border-left:5px solid {color}; padding:10px'><b>Facturación</b><br>{format_euro(resultados['facturacion'])} {simbolo}</div>", unsafe_allow_html=True)
        with col2:
            simbolo, color = get_estado(resultados['costes_directos'], benchmark_linea['margen_bruto'], 'menos_es_mejor')
            st.markdown(f"<div style='border-left:5px solid {color}; padding:10px'><b>Costes Directos</b><br>{format_euro(resultados['costes_directos'])} {simbolo}</div>", unsafe_allow_html=True)
        with col3:
            simbolo, color = get_estado(resultados['margen_bruto'], benchmark_linea['ebitda'], 'mas_es_mejor')
            st.markdown(f"<div style='border-left:5px solid {color}; padding:10px'><b>Margen Bruto</b><br>{format_euro(resultados['margen_bruto'])} {simbolo}</div>", unsafe_allow_html=True)

        # Velocímetro Nivel Actividad
        if resultados['nivel_actividad'] is not None:
            min_sub, media_sub, max_sub = benchmark_linea['utilizacion']
            gauge_color = "#144C44" if min_sub * 100 <= resultados['nivel_actividad'] <= max_sub * 100 else "#D33F49"
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

            # Texto debajo del velocímetro
            st.markdown(f"""
            📅 **Jornadas disponibles**: {int(resultados['jornadas_totales']) if resultados['jornadas_totales'] else '—'}  
            ✅ **Jornadas utilizadas**: {int(resultados['jornadas_utilizadas']) if resultados['jornadas_utilizadas'] else '—'}  
            📊 **% Jornadas utilizadas**: {round(resultados['nivel_actividad'], 1)}%  
            🔄 **Subactividad asumible ({data['parametros']['subactividad_permitida_%']}%)**: {int(resultados['jornadas_totales'] * data['parametros']['subactividad_permitida_%']/100) if resultados['jornadas_totales'] else '—'} jornadas  
            🚨 **Exceso Subactividad**: {int(resultados['subactividad_jornadas']) if resultados['subactividad_jornadas'] > 0 else 0} jornadas  
            💸 **Coste asociado**: {format_euro(resultados['subactividad_jornadas'] * coste_persona / jornadas_persona) if resultados['subactividad_jornadas'] and jornadas_persona > 0 else '—'}
            """)

        else:
            st.markdown("ℹ️ **Sin nivel de actividad (100% uso supuesto)**")

        # Gráfico cascada
        fig_cascada = go.Figure(go.Waterfall(
            name=nombre_linea,
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
            title=f"Gráfico Cascada - {nombre_linea}",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color="#333333")
        )
        st.plotly_chart(fig_cascada, use_container_width=True)

# -------------------------------
# Crear bloques para cada línea
# -------------------------------
for linea, datos_linea in lineas_negocio.items():
    clave_benchmark = nombre_benchmark.get(linea.replace("á", "a"))
    benchmark_linea = benchmarks['lineas_negocio'][clave_benchmark]
    bloque_linea(linea, datos_linea, benchmark_linea)
