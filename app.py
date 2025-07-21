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
# Funciones auxiliares
# -------------------------------
def format_euro(valor):
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

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
# Cargar datos
# -------------------------------
with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

param = data['parametros']
result = data['resultados']
facturacion_total = result['facturacion_total']

mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# Pantalla dividida
# -------------------------------
col_izq, col_der = st.columns(2)

# -------------------------------
# IZQUIERDA: LÍNEAS DE NEGOCIO + COSTES FIJOS
# -------------------------------
resultados_lineas = {}

with col_izq:
    st.header("🔧 Ajustes")

    # 🔥 BLOQUES POR LÍNEA DE NEGOCIO
    for linea_nombre, linea in param['lineas_negocio'].items():
        benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])

        with st.expander(f"🔽 {linea_nombre.upper()}", expanded=False):
            st.markdown("Ajusta los parámetros para analizar el impacto en resultados.")
            cols = st.columns(4)

            if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
                with cols[0]:
                    nueva_tarifa = st.slider("Tarifa (€)", int(linea['tarifa']*0.8), int(linea['tarifa']*1.2), int(linea['tarifa']), step=10)
                    bm_tarifa = benchmark_linea['precio_jornada'] if benchmark_linea else None
                    kpi_card("Tarifa", nueva_tarifa, None, benchmark=(bm_tarifa[0], bm_tarifa[2]) if bm_tarifa else None, tipo="tarifa", tooltip="Precio medio jornada")

                with cols[1]:
                    jornadas_x_proyecto = linea['ticket_medio'] // linea['tarifa']
                    nuevas_jornadas = st.slider("Jornadas por Proyecto", max(1, int(jornadas_x_proyecto*0.5)), int(jornadas_x_proyecto*1.5), int(jornadas_x_proyecto), step=1)
                    ticket_medio = nueva_tarifa * nuevas_jornadas
                    kpi_card("Jornadas/Proyecto", nuevas_jornadas, None, tooltip="Número medio de jornadas por proyecto", show_euro=False)
            else:
                with cols[0]:
                    ticket_medio = st.slider("Ticket Medio (€)", int(linea['ticket_medio']*0.5), int(linea['ticket_medio']*1.5), int(linea['ticket_medio']), step=1000)
                    kpi_card("Ticket Medio", ticket_medio, None, tooltip="Valor medio por proyecto")

            with cols[2]:
                nuevo_unidades = st.slider("Número de Unidades", 0, int(linea['unidades']*2), int(linea['unidades']), step=1)
                kpi_card("Número de Unidades", nuevo_unidades, None, tooltip="Proyectos o ventas", show_euro=False)

            if linea['personas'] > 0:
                with cols[3]:
                    nuevo_personas = st.slider("Personas", 0, int(linea['personas']*2), int(linea['personas']), step=1)
                    kpi_card("Personas", nuevo_personas, None, tooltip="Número de personas asignadas", show_euro=False)
                nuevo_coste_medio = st.slider("Coste Medio Persona (€)", int(linea['coste_medio_persona']*0.8), int(linea['coste_medio_persona']*1.2), int(linea['coste_medio_persona']), step=1000)
                kpi_card("Coste Medio Persona", nuevo_coste_medio, None, tooltip="Coste anual medio por persona")
            else:
                nuevo_personas = 0
                nuevo_coste_medio = 0

            # Cálculos línea
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

            # 📊 KPIs Resultados
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                kpi_card("Facturación", facturacion_linea, None, tooltip="Facturación total línea")
            with col_r2:
                kpi_card("Costes Directos", costes_directos, (costes_directos / facturacion_linea) if facturacion_linea else None, tooltip="Costes directos sobre facturación línea")
            with col_r3:
                kpi_card("Margen Bruto", margen_bruto, (margen_bruto / facturacion_linea) if facturacion_linea else None, benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None, tipo="margen", tooltip="Margen sobre facturación línea")

            # 📈 Velocímetro y tabla jornadas
            if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
                jornadas_disp = nuevo_personas * linea['jornadas_por_persona']
                jornadas_util = (ticket_medio / nueva_tarifa) * nuevo_unidades
                utilizacion_pct = jornadas_util / jornadas_disp if jornadas_disp else 0
                bm_util = benchmark_linea['utilizacion'] if benchmark_linea else [0.6, 0.7, 0.75]

                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=utilizacion_pct*100,
                    gauge={
                        'axis': {'range': [0, 100]},
                        'steps': [{'range': [0, bm_util[0]*100], 'color': COLOR_ROJO},
                                  {'range': [bm_util[0]*100, bm_util[2]*100], 'color': COLOR_VERDE},
                                  {'range': [bm_util[2]*100, 100], 'color': COLOR_NARANJA}],
                        'threshold': {'line': {'color': "black", 'width': 4}, 'value': utilizacion_pct*100}
                    }
                ))
                fig_gauge.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_gauge, use_container_width=True)

                st.markdown(f"""
                **📋 Resumen Jornadas**
                - Jornadas disponibles: {int(jornadas_disp)}
                - Jornadas utilizadas: {int(jornadas_util)}
                - % Utilización real: {round(utilizacion_pct*100,1)}%
                - 🔄 Subactividad asumible: {int(jornadas_disp*(1-bm_util[0]))} jornadas
                - 🚨 Exceso Subactividad: {max(0, int(jornadas_disp - jornadas_util - jornadas_disp*(1-bm_util[0])))}
                - 💸 Coste asociado: {format_euro((jornadas_disp - jornadas_util) * (nuevo_coste_medio / linea['jornadas_por_persona']))}
                """)

            # 📉 Gráfico cascada línea
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
            fig_cascada.update_layout(title=f"Cuenta de Resultados - {linea_nombre}", plot_bgcolor=COLOR_FONDO, paper_bgcolor=COLOR_FONDO, font=dict(color=COLOR_TEXTO), margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_cascada, use_container_width=True)

    # 🔧 COSTES FIJOS
    st.header("🏢 Ajustes - Costes Fijos")
    for categoria, valor in param['costes_fijos'].items():
        nuevo_valor = st.slider(f"{categoria.capitalize()} (€)", 0, int(valor*2), int(valor), step=1000)
        kpi_card(categoria.capitalize(), nuevo_valor, nuevo_valor/facturacion_total, benchmark=benchmarks['global'].get(categoria.capitalize()))

# -------------------------------
# DERECHA: KPIs GLOBALES + TABLA
# -------------------------------
with col_der:
    st.header("📊 Resultados Globales")

    total_facturacion = sum(v['facturacion'] for v in resultados_lineas.values())
    total_costes_directos = sum(v['costes_directos'] for v in resultados_lineas.values())
    total_margen_bruto = sum(v['margen_bruto'] for v in resultados_lineas.values())
    total_costes_fijos = sum(param['costes_fijos'].values())
    total_ebitda = total_margen_bruto - total_costes_fijos

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        kpi_card("Facturación Total", total_facturacion, 1.0)
    with col2:
        kpi_card("Costes Directos", total_costes_directos, total_costes_directos/total_facturacion, benchmark=benchmarks['global']['costes_directos'])
    with col3:
        kpi_card("Margen Bruto", total_margen_bruto, total_margen_bruto/total_facturacion, benchmark=benchmarks['global']['margen_bruto'], tipo="margen")
    with col4:
        kpi_card("Costes Fijos", total_costes_fijos, total_costes_fijos/total_facturacion, benchmark=benchmarks['global']['costes_fijos'])
    with col5:
        kpi_card("EBITDA", total_ebitda, total_ebitda/total_facturacion, benchmark=benchmarks['global']['ebitda'], tipo="margen")

    # 📉 Gráfico cascada global
    fig_global = go.Figure(go.Waterfall(
        name="Global",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Ingresos", "Costes Directos", "Costes Fijos", "EBITDA"],
        textposition="outside",
        text=[format_euro(total_facturacion), format_euro(-total_costes_directos), format_euro(-total_costes_fijos), format_euro(total_ebitda)],
        y=[total_facturacion, -total_costes_directos, -total_costes_fijos, total_ebitda],
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))
    fig_global.update_layout(title="Cuenta de Resultados - Global", plot_bgcolor=COLOR_FONDO, paper_bgcolor=COLOR_FONDO, font=dict(color=COLOR_TEXTO), margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_global, use_container_width=True)

    # 📋 Tabla resumen por línea
    resumen_df = pd.DataFrame([{
        "Línea": k,
        "Facturación": format_euro(v["facturacion"]),
        "Costes Directos": f"{format_euro(v['costes_directos'])} ({v['costes_directos']/v['facturacion']*100:.1f}%)" if v['facturacion'] else "—",
        "Margen Bruto": f"{format_euro(v['margen_bruto'])} ({v['margen_bruto']/v['facturacion']*100:.1f}%)" if v['facturacion'] else "—"
    } for k, v in resultados_lineas.items()])
    st.subheader("📦 Resumen Total por Línea de Negocio")
    st.table(resumen_df)

    # 💬 Comentarios estratégicos
    st.subheader("💬 Comentarios Estratégicos")
    st.markdown("""
    - 💚 Implantación supera el benchmark de margen en +3%.
    - 🟠 Licencias presenta un coste directo +8% sobre benchmark.
    - ⭐ Hot line tiene una tarifa muy por encima de la media sectorial.
    """)
