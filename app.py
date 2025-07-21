import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="Simulador PyG IT", page_icon="💻", layout="wide")

# Colores corporativos
COLOR_VERDE = "#144C44"
COLOR_NARANJA = "#fb9200"
COLOR_ESTRELLA = "#FFD700"
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
def get_estado(valor_pct, benchmark, tipo="coste", valor_abs=None):
    if benchmark:
        min_bm, max_bm = benchmark
        if tipo == "tarifa" and valor_abs is not None:
            if valor_abs < min_bm:
                return COLOR_NARANJA, "⚠️"
            elif min_bm <= valor_abs <= max_bm:
                return COLOR_VERDE, "✅"
            else:
                return COLOR_ESTRELLA, "⭐"
        elif valor_pct is not None:
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
    return COLOR_TEXTO, ""

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tipo="coste", tooltip=None, show_euro=True):
    color, icono = get_estado(valor_pct, benchmark, tipo, valor_abs=valor_abs if tipo == "tarifa" else None)
    if benchmark:
        comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[1]*100)}%</small>" if tipo != "tarifa" else f"<br><small>Benchmark: {int(benchmark[0])}–{int(benchmark[1])} €</small>"
    else:
        comparativa = "<br><small>Sin benchmark definido</small>"

    valor_mostrado = format_euro(valor_abs) if show_euro else f"{int(valor_abs)}"
    porcentaje = f"{round(valor_pct*100,1)}%" if valor_pct is not None else "—"

    html = f"""
    <div class="kpi-card" style="background-color:{COLOR_GRIS}; 
                                  border-left:5px solid {color};
                                  padding:10px; border-radius:8px;
                                  transition: transform 0.2s; position:relative;"
         onmouseover="this.style.transform='scale(1.02)'"
         onmouseout="this.style.transform='scale(1)'"
         title="{tooltip or nombre}">
        <div style="font-size:18px; color:{COLOR_TEXTO};">{nombre} {icono}</div>
        <div style="font-size:26px; font-weight:bold; color:{color};">{valor_mostrado}</div>
        <div style="font-size:14px; color:{COLOR_TEXTO};">{porcentaje} sobre ventas{comparativa}</div>
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
resultados_lineas = {}

mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# BLOQUES LÍNEAS DE NEGOCIO
# -------------------------------
for linea_nombre, linea in param['lineas_negocio'].items():
    benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])

    with st.expander(f"🔽 {linea_nombre.upper()}", expanded=False):
        st.markdown("Ajusta los parámetros para analizar el impacto en resultados.")

        # Sliders + KPIs en dos filas
        cols1 = st.columns(4)
        cols2 = st.columns(2)

        # Tarifa o Ticket Medio
        if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
            with cols1[0]:
                nueva_tarifa = st.slider("Tarifa (€)", int(linea['tarifa']*0.8), int(linea['tarifa']*1.2), int(linea['tarifa']), 10)
                bm_tarifa = benchmark_linea['precio_jornada'] if benchmark_linea else None
                kpi_card("Tarifa", nueva_tarifa, None,
                         benchmark=(bm_tarifa[0], bm_tarifa[2]) if bm_tarifa else None,
                         tipo="tarifa", tooltip="Precio medio jornada")
            with cols1[1]:
                jornadas_x_proyecto = linea['ticket_medio'] // linea['tarifa']
                nuevas_jornadas = st.slider("Jornadas por Proyecto", max(1, int(jornadas_x_proyecto*0.5)), int(jornadas_x_proyecto*1.5), int(jornadas_x_proyecto), 1)
                ticket_medio = nueva_tarifa * nuevas_jornadas
                kpi_card("Jornadas/Proyecto", nuevas_jornadas, None,
                         tooltip="Número medio de jornadas por proyecto", show_euro=False)
        else:
            with cols1[0]:
                ticket_medio = st.slider("Ticket Medio (€)", int(linea['ticket_medio']*0.5), int(linea['ticket_medio']*1.5), int(linea['ticket_medio']), 1000)
                kpi_card("Ticket Medio", ticket_medio, None,
                         tooltip="Valor medio por proyecto")

        # Unidades
        with cols1[2]:
            nuevo_unidades = st.slider("Número de Unidades", 0, int(linea['unidades']*2), int(linea['unidades']), 1)
            kpi_card("Número de Unidades", nuevo_unidades, None,
                     tooltip="Proyectos o ventas", show_euro=False)

        # Personas y Coste Medio Persona (si aplica)
        if linea['personas'] > 0:
            with cols2[0]:
                nuevo_personas = st.slider("Personas", 0, int(linea['personas']*2), int(linea['personas']), 1)
                kpi_card("Personas", nuevo_personas, None,
                         tooltip="Número de personas asignadas", show_euro=False)
            with cols2[1]:
                nuevo_coste_medio = st.slider("Coste Medio Persona (€)", int(linea['coste_medio_persona']*0.8), int(linea['coste_medio_persona']*1.2), int(linea['coste_medio_persona']), 1000)
                kpi_card("Coste Medio Persona", nuevo_coste_medio, None,
                         tooltip="Coste anual medio por persona")
        else:
            nuevo_personas = 0
            nuevo_coste_medio = 0

        # Cálculos y resultados
        facturacion_linea = ticket_medio * nuevo_unidades
        costes_personal = nuevo_personas * nuevo_coste_medio
        costes_directos_pct = linea['costes_directos_%']
        costes_directos = facturacion_linea * (costes_directos_pct / 100) + costes_personal
        margen_bruto = facturacion_linea - costes_directos

        resultados_lineas[linea_nombre] = {
            "facturacion": facturacion_linea,
            "costes_directos": costes_directos,
            "margen_bruto": margen_bruto
        }

        # KPIs resultados
        st.subheader("📊 KPIs Resultados")
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_card("Facturación", facturacion_linea, None)
        with col2:
            kpi_card("Costes Directos", costes_directos, (costes_directos / facturacion_linea) if facturacion_linea else None)
        with col3:
            kpi_card("Margen Bruto", margen_bruto, (margen_bruto / facturacion_linea) if facturacion_linea else None,
                     benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None,
                     tipo="margen")

        # Velocímetro y tabla jornadas (si aplica)
        if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
            jornadas_disponibles = nuevo_personas * linea['jornadas_por_persona']
            jornadas_utilizadas = (ticket_medio / nueva_tarifa) * nuevo_unidades
            utilizacion_real_pct = jornadas_utilizadas / jornadas_disponibles if jornadas_disponibles else 0
            bm_util = benchmark_linea['utilizacion'] if benchmark_linea else [0.6, 0.7, 0.75]

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=utilizacion_real_pct*100,
                gauge={
                    'axis': {'range': [0, 100]},
                    'steps': [
                        {'range': [0, bm_util[0]*100], 'color': COLOR_ROJO},
                        {'range': [bm_util[0]*100, bm_util[2]*100], 'color': COLOR_VERDE},
                        {'range': [bm_util[2]*100, 100], 'color': COLOR_NARANJA},
                    ]
                }
            ))
            fig_gauge.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown(f"""
            **📋 Resumen Jornadas**
            - Jornadas disponibles: {int(jornadas_disponibles)}
            - Jornadas utilizadas: {int(jornadas_utilizadas)}
            - % Utilización real: {round(utilizacion_real_pct*100,1)}%
            - 🔄 Subactividad asumible ({int(bm_util[0]*100)}%): {int(jornadas_disponibles*(1-bm_util[0]))} jornadas
            - 🚨 Exceso Subactividad: {max(0, int(jornadas_disponibles - jornadas_utilizadas - jornadas_disponibles*(1-bm_util[0])))}
            - 💸 Coste asociado: {format_euro((jornadas_disponibles - jornadas_utilizadas) * (nuevo_coste_medio / linea['jornadas_por_persona']))}
            """)

        # Gráfico cascada
        fig_cascada = go.Figure(go.Waterfall(
            name=linea_nombre,
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Facturación", "Costes Directos", "Margen Bruto"],
            textposition="outside",
            text=[format_euro(facturacion_linea), format_euro(-costes_directos), format_euro(margen_bruto)],
            y=[facturacion_linea, -costes_directos, margen_bruto],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_cascada.update_layout(
            title=f"Cuenta de Resultados - {linea_nombre}",
            plot_bgcolor=COLOR_FONDO,
            paper_bgcolor=COLOR_FONDO,
            font=dict(color=COLOR_TEXTO),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_cascada, use_container_width=True)

# -------------------------------
# BLOQUE COSTES FIJOS
# -------------------------------
st.header("🏢 Costes Fijos")
with st.expander("🔽 Ajuste Detallado de Costes Fijos", expanded=False):
    costes_fijos_detalle = {}
    for categoria, valor in param['costes_fijos'].items():
        nuevo_valor = st.slider(f"{categoria.capitalize()} (€)", 0, int(valor*2), int(valor), 1000)
        costes_fijos_detalle[categoria] = nuevo_valor
        porcentaje = nuevo_valor / facturacion_total
        benchmark_categoria = benchmarks['global'].get(categoria.lower())
        kpi_card(categoria.capitalize(), nuevo_valor, porcentaje,
                 benchmark=benchmark_categoria,
                 tooltip=f"Coste fijo en {categoria}")

total_costes_fijos = sum(costes_fijos_detalle.values())

# -------------------------------
# RESULTADOS GLOBALES
# -------------------------------
st.header("📊 Resultados Globales")
costes_directos_global = sum(v["costes_directos"] for v in resultados_lineas.values())
margen_bruto_global = sum(v["margen_bruto"] for v in resultados_lineas.values())
ebitda_global = margen_bruto_global - total_costes_fijos

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    kpi_card("Facturación Total", facturacion_total, 1.0)
with col2:
    kpi_card("Costes Directos", costes_directos_global, costes_directos_global/facturacion_total,
             benchmark=benchmarks['global']['costes_directos'])
with col3:
    kpi_card("Margen Bruto", margen_bruto_global, margen_bruto_global/facturacion_total,
             benchmark=benchmarks['global']['margen_bruto'], tipo="margen")
with col4:
    kpi_card("Costes Fijos", total_costes_fijos, total_costes_fijos/facturacion_total,
             benchmark=benchmarks['global']['costes_fijos'])
with col5:
    kpi_card("EBITDA", ebitda_global, ebitda_global/facturacion_total,
             benchmark=benchmarks['global']['ebitda'], tipo="margen")

# Gráfico cascada global
fig_global = go.Figure(go.Waterfall(
    name="Global",
    orientation="v",
    measure=["relative", "relative", "relative", "total"],
    x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
    textposition="outside",
    text=[format_euro(facturacion_total), format_euro(-costes_directos_global),
          format_euro(-total_costes_fijos), format_euro(ebitda_global)],
    y=[facturacion_total, -costes_directos_global, -total_costes_fijos, ebitda_global],
    connector={"line": {"color": "rgb(63, 63, 63)"}}
))
fig_global.update_layout(
    title="Cuenta de Resultados Global",
    plot_bgcolor=COLOR_FONDO,
    paper_bgcolor=COLOR_FONDO,
    font=dict(color=COLOR_TEXTO),
    margin=dict(l=10, r=10, t=40, b=10)
)
st.plotly_chart(fig_global, use_container_width=True)

# Resumen por línea
st.subheader("📦 Resumen por Línea de Negocio")
resumen_df = pd.DataFrame([
    {
        "Línea": k,
        "Facturación": format_euro(v["facturacion"]),
        "Costes Directos": f"{format_euro(v['costes_directos'])} ({v['costes_directos']/v['facturacion']*100:.1f}%)" if v['facturacion'] else "—",
        "Margen Bruto": f"{format_euro(v['margen_bruto'])} ({v['margen_bruto']/v['facturacion']*100:.1f}%)" if v['facturacion'] else "—"
    }
    for k, v in resultados_lineas.items()
])
st.table(resumen_df)

# -------------------------------
# COMENTARIOS ESTRATÉGICOS
# -------------------------------
st.header("💬 Comentarios Estratégicos")

comentarios = []

for linea, datos in resultados_lineas.items():
    bm_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea])
    margen_pct = datos['margen_bruto']/datos['facturacion'] if datos['facturacion'] else 0
    if margen_pct > bm_linea['margen_bruto'][2]:
        comentarios.append(f"⭐ {linea}: margen bruto superior a la media.")
    elif margen_pct < bm_linea['margen_bruto'][0]:
        comentarios.append(f"⚠️ {linea}: margen bruto bajo respecto a la media.")

    if linea in param['lineas_negocio']:
        l = param['lineas_negocio'][linea]
        if l['personas'] > 0 and l['jornadas_por_persona'] > 0:
            jornadas_disponibles = nuevo_personas * l['jornadas_por_persona']
            jornadas_utilizadas = (ticket_medio / nueva_tarifa) * nuevo_unidades
            utilizacion_pct = jornadas_utilizadas / jornadas_disponibles if jornadas_disponibles else 0
            if utilizacion_pct < bm_linea['utilizacion'][0]:
                comentarios.append(f"⚠️ {linea}: subactividad superior a lo deseable.")
            elif utilizacion_pct > 1:
                comentarios.append(f"🚨 {linea}: sobreactividad, posible saturación de recursos.")

ebitda_pct = ebitda_global / facturacion_total
if ebitda_pct > benchmarks['global']['ebitda'][1]:
    comentarios.append("⭐ EBITDA global excelente.")
elif ebitda_pct < benchmarks['global']['ebitda'][0]:
    comentarios.append("🚨 EBITDA global por debajo del benchmark.")

if not comentarios:
    comentarios.append("✅ Todos los indicadores están dentro de los rangos deseados.")

for c in comentarios:
    st.markdown(f"- {c}")
