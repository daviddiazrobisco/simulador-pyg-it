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

# Mapeo líneas de negocio → benchmarks
mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# BLOQUES LÍNEAS DE NEGOCIO
# -------------------------------
resultados_lineas = {}

for linea_nombre, linea in param['lineas_negocio'].items():
    benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])

    with st.expander(f"🔽 {linea_nombre.upper()}", expanded=False):
        st.markdown("Ajusta los parámetros para analizar el impacto en resultados.")

        # Sliders + KPIs
        cols = st.columns(5)

        # Tarifa + Jornadas (si hay nivel de actividad) o Ticket Medio
        if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
            # Tarifa
            with cols[0]:
                nueva_tarifa = st.slider("Tarifa (€)", 
                                         min_value=int(linea['tarifa'] * 0.8),
                                         max_value=int(linea['tarifa'] * 1.2),
                                         value=int(linea['tarifa']),
                                         step=10,
                                         format="%d")
                bm_tarifa = benchmark_linea['precio_jornada'] if benchmark_linea else None
                kpi_card("Tarifa", nueva_tarifa, None,
                         benchmark=(bm_tarifa[0], bm_tarifa[2]) if bm_tarifa else None,
                         tipo="tarifa", tooltip="Precio medio jornada")
            # Jornadas por proyecto
            with cols[1]:
                jornadas_x_proyecto = linea['ticket_medio'] // linea['tarifa']
                nuevas_jornadas = st.slider("Jornadas por Proyecto", 
                                            min_value=max(1, int(jornadas_x_proyecto * 0.5)),
                                            max_value=int(jornadas_x_proyecto * 1.5),
                                            value=int(jornadas_x_proyecto),
                                            step=1)
                ticket_medio = nueva_tarifa * nuevas_jornadas
                kpi_card("Jornadas/Proyecto", nuevas_jornadas, None,
                         tooltip="Número medio de jornadas por proyecto", show_euro=False)
        else:
            # Ticket Medio
            with cols[0]:
                ticket_medio = st.slider("Ticket Medio (€)", 
                                         min_value=int(linea['ticket_medio'] * 0.5),
                                         max_value=int(linea['ticket_medio'] * 1.5),
                                         value=int(linea['ticket_medio']),
                                         step=1000,
                                         format="%d")
                kpi_card("Ticket Medio", ticket_medio, None,
                         tooltip="Valor medio por proyecto")

        # Unidades
        with cols[2]:
            nuevo_unidades = st.slider("Número de Unidades", 
                                       min_value=0, max_value=int(linea['unidades']*2),
                                       value=int(linea['unidades']), step=1)
            kpi_card("Número de Unidades", nuevo_unidades, None,
                     tooltip="Proyectos o ventas", show_euro=False)

        # Personas y Coste Medio Persona (si aplica)
        if linea['personas'] > 0:
            with cols[3]:
                nuevo_personas = st.slider("Personas", 
                                           min_value=0, max_value=int(linea['personas']*2),
                                           value=int(linea['personas']), step=1)
                kpi_card("Personas", nuevo_personas, None,
                         tooltip="Número de personas asignadas", show_euro=False)
            with cols[4]:
                nuevo_coste_medio = st.slider("Coste Medio Persona (€)", 
                                              min_value=int(linea['coste_medio_persona'] * 0.8),
                                              max_value=int(linea['coste_medio_persona'] * 1.2),
                                              value=int(linea['coste_medio_persona']),
                                              step=1000,
                                              format="%d")
                kpi_card("Coste Medio Persona", nuevo_coste_medio, None,
                         tooltip="Coste anual medio por persona")
        else:
            nuevo_personas = 0
            nuevo_coste_medio = 0

        # Cálculos
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

        # 📊 KPIs resultados
        st.subheader("📊 KPIs Resultados")
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_card("Facturación", facturacion_linea, None,
                     tooltip="Facturación total línea")
        with col2:
            kpi_card("Costes Directos", costes_directos, (costes_directos / facturacion_linea) if facturacion_linea else None,
                     tooltip="Costes directos sobre facturación línea")
        with col3:
            kpi_card("Margen Bruto", margen_bruto, (margen_bruto / facturacion_linea) if facturacion_linea else None,
                     benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None,
                     tipo="margen", tooltip="Margen sobre facturación línea")

        # 📈 Velocímetro y tabla jornadas (si aplica)
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
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': utilizacion_real_pct*100
                    }
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

        # 📉 Gráfico cascada
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
# Resumen total
# -------------------------------
st.header("📦 Resumen Total por Línea de Negocio")

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
