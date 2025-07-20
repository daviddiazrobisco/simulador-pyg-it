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

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tipo="coste", tooltip=None):
    """Genera una tarjeta KPI con color dinámico y popup"""
    color, icono = COLOR_VERDE, "✅"
    comparativa = ""
    if benchmark:
        color, icono = get_estado(valor_pct, benchmark, tipo)
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
# IMPLANTACIÓN
# -------------------------------
st.title("🔽 IMPLANTACIÓN")
st.markdown("Ajusta los parámetros para analizar el impacto en resultados.")

linea = param['lineas_negocio']['Implantación']
benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark['Implantación'])

# Sliders sobre KPI
st.subheader("🎛️ Ajustes de Implantación")
# Ticket Medio
nuevo_ticket = st.slider("Ticket Medio (€)", 
                         min_value=int(linea['ticket_medio'] * 0.5),
                         max_value=int(linea['ticket_medio'] * 1.5),
                         value=int(linea['ticket_medio']),
                         step=1000,
                         format="%d")
kpi_card("Ticket Medio", nuevo_ticket, nuevo_ticket / facturacion_total, 
         benchmark=(benchmark_linea['precio_jornada'][0]/facturacion_total,
                    benchmark_linea['precio_jornada'][2]/facturacion_total),
         tooltip="Valor medio por proyecto")

# Unidades
nuevo_unidades = st.slider("Número de Unidades", 
                           min_value=0, max_value=int(linea['unidades']*2),
                           value=int(linea['unidades']), step=1)
kpi_card("Número de Unidades", nuevo_unidades * nuevo_ticket, 
         (nuevo_unidades * nuevo_ticket)/facturacion_total,
         tooltip="Número de proyectos o ventas")

# Personas
nuevo_personas = st.slider("Personas", 
                           min_value=0, max_value=int(linea['personas']*2),
                           value=int(linea['personas']), step=1)
kpi_card("Personas", nuevo_personas * linea['coste_medio_persona'], 
         (nuevo_personas * linea['coste_medio_persona'])/facturacion_total,
         tooltip="Coste de personal asignado")

# -------------------------------
# Cálculos resultados
# -------------------------------
facturacion_linea = nuevo_ticket * nuevo_unidades
costes_personal = nuevo_personas * linea['coste_medio_persona']
costes_directos_pct = linea['costes_directos_%']
costes_directos = facturacion_linea * (costes_directos_pct / 100) + costes_personal
margen_bruto = facturacion_linea - costes_directos

# KPIs resultados
st.subheader("📊 KPIs Resultados")
col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Facturación", facturacion_linea, facturacion_linea/facturacion_total,
             tooltip="Facturación total línea")
with col2:
    kpi_card("Costes Directos", costes_directos, costes_directos/facturacion_total,
             benchmark=(benchmark_linea['margen_bruto'][0],
                        benchmark_linea['margen_bruto'][2]),
             tipo="coste",
             tooltip="Costes directos de la línea")
with col3:
    kpi_card("Margen Bruto", margen_bruto, margen_bruto/facturacion_total,
             benchmark=(benchmark_linea['margen_bruto'][0],
                        benchmark_linea['margen_bruto'][2]),
             tipo="margen",
             tooltip="Ingresos menos costes directos")

# -------------------------------
# Nivel de actividad
# -------------------------------
st.subheader("⏱️ Nivel de Actividad")
if linea['jornadas_por_persona'] > 0 and nuevo_personas > 0:
    jornadas_disponibles = nuevo_personas * linea['jornadas_por_persona']
    jornadas_utilizadas = (facturacion_linea / linea['tarifa'])
    nivel_utilizacion = jornadas_utilizadas / jornadas_disponibles

    # Velocímetro
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=nivel_utilizacion * 100,
        title={'text': "Utilización (%)"},
        gauge={
            'axis': {'range': [0, 120]},
            'bar': {'color': COLOR_NARANJA},
            'steps': [
                {'range': [0, subactividad_permitida*100], 'color': COLOR_ESTRELLA},
                {'range': [subactividad_permitida*100, 100], 'color': COLOR_VERDE},
                {'range': [100, 120], 'color': COLOR_ROJO}
            ]
        }
    ))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Texto debajo
    st.markdown(f"""
    📅 **Jornadas disponibles:** {int(jornadas_disponibles)}  
    ✅ **Jornadas utilizadas:** {int(jornadas_utilizadas)}  
    📊 **% Jornadas utilizadas:** {nivel_utilizacion*100:.1f}%  
    🔄 **Subactividad asumible ({int(subactividad_permitida*100)}%):** {int(jornadas_disponibles*subactividad_permitida)} jornadas  
    🚨 **Exceso Subactividad:** {max(0, int(jornadas_disponibles - jornadas_utilizadas - jornadas_disponibles*subactividad_permitida))} jornadas  
    💸 **Coste asociado:** {format_euro(max(0, (jornadas_disponibles - jornadas_utilizadas - jornadas_disponibles*subactividad_permitida)*linea['coste_medio_persona']/linea['jornadas_por_persona']))}
    """)
else:
    st.markdown("⚡ Sin nivel de actividad (100% uso supuesto)")

# -------------------------------
# Gráfico cascada
# -------------------------------
st.subheader("📉 Resumen Económico - Implantación")
fig_cascada = go.Figure(go.Waterfall(
    name="Implantación",
    orientation="v",
    measure=["relative", "relative", "total"],
    x=["Facturación", "Costes Directos", "Margen Bruto"],
    textposition="outside",
    text=[format_euro(facturacion_linea), format_euro(-costes_directos), format_euro(margen_bruto)],
    y=[facturacion_linea, -costes_directos, margen_bruto],
    connector={"line": {"color": "rgb(63, 63, 63)"}}
))
fig_cascada.update_layout(
    title="Implantación - Facturación / Costes Directos / Margen Bruto",
    plot_bgcolor=COLOR_FONDO,
    paper_bgcolor=COLOR_FONDO,
    font=dict(color=COLOR_TEXTO),
    margin=dict(l=10, r=10, t=40, b=10)
)
st.plotly_chart(fig_cascada, use_container_width=True)
