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

# -------------------------------
# Cargar datos
# -------------------------------
with open('presupuesto_it_2025.json') as f:
    data = json.load(f)
linea = data['parametros']['lineas_negocio']["Implantación"]

# -------------------------------
# Ajustes implantación
# -------------------------------
st.header("🔽 Implantación (Tipo A - Solo personal con subactividad)")

# Sliders
importe_proyecto = st.slider("💶 Importe Medio Proyecto (€)", 100000, 500000, 200000, step=5000, format="%d")
tarifa_jornada = st.slider("💵 Tarifa Media Jornada (€)", 500, 1500, int(linea['tarifa']), step=50, format="%d")
num_proyectos = st.slider("📦 Nº Proyectos", 5, 30, int(linea['unidades']), step=1)
num_personas = st.slider("👥 Nº Personas", 10, 60, int(linea['personas']), step=1)
coste_medio_persona = st.slider("👔 Coste Medio Persona (€)", 40000, 80000, int(linea['coste_medio_persona']), step=1000, format="%d")

# Cálculos
jornadas_proyecto = importe_proyecto / tarifa_jornada
jornadas_facturadas = num_proyectos * jornadas_proyecto
facturacion_implantacion = jornadas_facturadas * tarifa_jornada

costes_directos_implantacion = num_personas * coste_medio_persona
margen_implantacion = facturacion_implantacion - costes_directos_implantacion
margen_pct = (margen_implantacion / facturacion_implantacion) * 100 if facturacion_implantacion else 0

# Nivel de Actividad
jornadas_disponibles = num_personas * 220
nivel_actividad = (jornadas_facturadas / jornadas_disponibles) * 100 if jornadas_disponibles else 0

# Subactividad
subactividad_asumible = jornadas_disponibles * 0.15
exceso_subactividad = max(jornadas_disponibles - jornadas_facturadas - subactividad_asumible, 0)
coste_jornada_persona = coste_medio_persona / 220
coste_subactividad = exceso_subactividad * coste_jornada_persona

# -------------------------------
# Mostrar resultados
# -------------------------------
st.subheader("📊 KPIs Implantación")
col1, col2, col3 = st.columns(3)
col1.metric("💶 Facturación", format_euro(facturacion_implantacion))
col2.metric("💸 Costes Directos", format_euro(costes_directos_implantacion))
col3.metric("📊 Margen Bruto", f"{format_euro(margen_implantacion)} ({round(margen_pct,1)}%)")

# Barra horizontal nivel de actividad
color_act = COLOR_VERDE if 70 <= nivel_actividad <= 100 else (COLOR_NARANJA if nivel_actividad > 100 else COLOR_ROJO)
estado_act = "✅ Óptimo" if 70 <= nivel_actividad <= 100 else ("⚠️ Sobreactividad" if nivel_actividad > 100 else "⭐ Subactividad")

fig_barra = go.Figure(go.Bar(
    x=[nivel_actividad],
    y=["Nivel de Actividad"],
    orientation='h',
    marker=dict(color=color_act),
    text=f"{round(nivel_actividad,1)}%",
    textposition="outside"
))
fig_barra.update_layout(
    xaxis=dict(range=[0, 120], title="%", showgrid=False),
    yaxis=dict(showgrid=False),
    title=f"🔥 Nivel de Actividad: {estado_act}",
    plot_bgcolor=COLOR_FONDO,
    paper_bgcolor=COLOR_FONDO,
    font=dict(color=COLOR_TEXTO)
)
st.plotly_chart(fig_barra, use_container_width=True)

# Subactividad informativa
st.markdown(f"**🔄 Subactividad asumible (15%)**: {int(subactividad_asumible)} jornadas")
st.markdown(f"**🚨 Exceso Subactividad**: {int(exceso_subactividad)} jornadas")
st.markdown(f"**💸 Coste asociado**: {format_euro(coste_subactividad)}")

# Mini gráfico cascada Implantación
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
    font=dict(color=COLOR_TEXTO)
)
st.plotly_chart(fig_implantacion, use_container_width=True)
