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
    """Formatea número en formato europeo con €"""
    try:
        formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} €"
    except:
        return str(valor)

def get_estado(valor_pct, benchmark, tipo="coste", valor_abs=None):
    """Devuelve color e icono según benchmark"""
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
    """Genera tarjeta KPI"""
    color, icono = get_estado(valor_pct, benchmark, tipo, valor_abs=valor_abs if tipo == "tarifa" else None)
    if benchmark:
        comparativa = f"<br><small>Benchmark: {int(benchmark[0]*100)}–{int(benchmark[1]*100)}%</small>" if tipo != "tarifa" else f"<br><small>Benchmark: {int(benchmark[0])}–{int(benchmark[1])} €</small>"
    else:
        comparativa = "<br><small>Sin benchmark definido</small>"

    valor_mostrado = format_euro(valor_abs) if isinstance(valor_abs, (int, float)) and show_euro else str(valor_abs)
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
# Cargar datos desde JSON
# -------------------------------
with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

param = data['parametros']
result = data['resultados']
facturacion_total = result['facturacion_total']

# -------------------------------
# Mapeo líneas de negocio → benchmarks
# -------------------------------
mapa_lineas_benchmark = {
    "Implantación": "consultoria",
    "Licencias": "software",
    "Hot line": "mixto"
}

# -------------------------------
# Pantalla dividida
# -------------------------------
col_izq, col_der = st.columns([1, 1.5])  # Columna izquierda más estrecha

# -------------------------------
# Columna Izquierda: Líneas de negocio
# -------------------------------
resultados_lineas = {}
with col_izq:
    st.header("🛠️ Ajustes por Línea de Negocio")

    for linea_nombre, linea in param['lineas_negocio'].items():
        benchmark_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])

        with st.expander(f"🔽 {linea_nombre.upper()}", expanded=False):
            st.markdown("Ajusta los parámetros para analizar el impacto en resultados.")
            cols = st.columns(5)

            if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
                # Tarifa
                with cols[0]:
                    nueva_tarifa = st.slider("Tarifa (€)",
                                             min_value=int(linea['tarifa'] * 0.8),
                                             max_value=int(linea['tarifa'] * 1.2),
                                             value=int(linea['tarifa']),
                                             step=10, format="%d")
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
                                                value=int(jornadas_x_proyecto), step=1)
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
                                             step=1000, format="%d")
                    kpi_card("Ticket Medio", ticket_medio, None,
                             tooltip="Valor medio por proyecto")

            # Número de unidades
            with cols[2]:
                nuevo_unidades = st.slider("Número de Unidades",
                                           min_value=0, max_value=int(linea['unidades'] * 2),
                                           value=int(linea['unidades']), step=1)
                kpi_card("Número de Unidades", nuevo_unidades, None,
                         tooltip="Proyectos o ventas", show_euro=False)

            # Personas y coste medio por persona
            if linea['personas'] > 0:
                with cols[3]:
                    nuevo_personas = st.slider("Personas",
                                               min_value=0, max_value=int(linea['personas'] * 2),
                                               value=int(linea['personas']), step=1)
                    kpi_card("Personas", nuevo_personas, None,
                             tooltip="Número de personas asignadas", show_euro=False)
                with cols[4]:
                    nuevo_coste_medio = st.slider("Coste Medio Persona (€)",
                                                  min_value=int(linea['coste_medio_persona'] * 0.8),
                                                  max_value=int(linea['coste_medio_persona'] * 1.2),
                                                  value=int(linea['coste_medio_persona']),
                                                  step=1000, format="%d")
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

            # 📈 Velocímetro y tabla (si aplica)
            if linea['personas'] > 0 and linea['jornadas_por_persona'] > 0:
                jornadas_disponibles = nuevo_personas * linea['jornadas_por_persona']
                jornadas_utilizadas = (ticket_medio / nueva_tarifa) * nuevo_unidades
                utilizacion_real_pct = jornadas_utilizadas / jornadas_disponibles if jornadas_disponibles else 0

                bm_util = benchmark_linea['utilizacion'] if benchmark_linea else [0.6, 0.7, 0.75]
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=utilizacion_real_pct * 100,
                    gauge={
                        'axis': {'range': [0, 100]},
                        'steps': [
                            {'range': [0, bm_util[0] * 100], 'color': COLOR_ROJO},
                            {'range': [bm_util[0] * 100, bm_util[2] * 100], 'color': COLOR_VERDE},
                            {'range': [bm_util[2] * 100, 100], 'color': COLOR_NARANJA},
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': utilizacion_real_pct * 100
                        }
                    }
                ))
                fig_gauge.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_gauge, use_container_width=True)

                st.markdown(f"""
                **📋 Resumen Jornadas**
                - Jornadas disponibles: {int(jornadas_disponibles)}
                - Jornadas utilizadas: {int(jornadas_utilizadas)}
                - % Utilización real: {round(utilizacion_real_pct * 100, 1)}%
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
# Columna Izquierda: Costes Fijos
# -------------------------------
st.header("🏢 Ajustes - Costes Fijos")
costes_fijos_detalle = {}
for categoria, valor in param['costes_fijos'].items():
    costes_fijos_detalle[categoria] = valor

cols_fijos = st.columns(2)
for idx, (categoria, valor) in enumerate(costes_fijos_detalle.items()):
    with cols_fijos[idx % 2]:
        nuevo_valor = st.slider(
            f"{categoria.capitalize()} (€)",
            min_value=0,
            max_value=int(valor * 2),
            value=int(valor),
            step=1000, format="%d"
        )
        costes_fijos_detalle[categoria] = nuevo_valor
        porcentaje = nuevo_valor / facturacion_total
        benchmark_categoria = None  # No hay benchmark detallado
        kpi_card(categoria.capitalize(), nuevo_valor, porcentaje,
                 benchmark=benchmark_categoria, tooltip=f"Coste fijo en {categoria}")

# -------------------------------
# Columna Derecha: KPIs Globales y Gráfico
# -------------------------------
with col_der:
    st.header("📊 Resultados Globales")

    facturacion_global = sum(v["facturacion"] for v in resultados_lineas.values())
    costes_directos_global = sum(v["costes_directos"] for v in resultados_lineas.values())
    margen_bruto_global = sum(v["margen_bruto"] for v in resultados_lineas.values())
    costes_fijos_global = sum(costes_fijos_detalle.values())
    ebitda_global = margen_bruto_global - costes_fijos_global

    kpis_globales = [
        ("Facturación Total", facturacion_global, 1.0, None),
        ("Costes Directos", costes_directos_global, costes_directos_global / facturacion_global, benchmarks["global"]["costes_directos"]),
        ("Margen Bruto", margen_bruto_global, margen_bruto_global / facturacion_global, benchmarks["global"]["margen_bruto"]),
        ("Costes Fijos", costes_fijos_global, costes_fijos_global / facturacion_global, benchmarks["global"]["costes_fijos"]),
        ("EBITDA", ebitda_global, ebitda_global / facturacion_global, benchmarks["global"]["ebitda"])
    ]

    cols_globales1, cols_globales2 = st.columns(3), st.columns(2)
    for i, (nombre, valor, pct, bm) in enumerate(kpis_globales):
        with (cols_globales1 if i < 3 else cols_globales2)[i % 3]:
            kpi_card(nombre, valor, pct, benchmark=bm, tipo="margen" if nombre == "Margen Bruto" else "coste")

    # 📊 Gráfico cascada global
    fig_global = go.Figure(go.Waterfall(
        name="Global",
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Facturación", "Costes Directos", "Costes Fijos", "EBITDA"],
        textposition="outside",
        text=[format_euro(facturacion_global), format_euro(-costes_directos_global),
              format_euro(-costes_fijos_global), format_euro(ebitda_global)],
        y=[facturacion_global, -costes_directos_global, -costes_fijos_global, ebitda_global],
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

    # 📋 Informe Resumen
    st.subheader("📝 Informe Resumen")
    st.markdown(f"""
    - 🔝 Línea más rentable: **{max(resultados_lineas.items(), key=lambda x: x[1]['margen_bruto'])[0]}**
    - 💵 Facturación Global: **{format_euro(facturacion_global)}**
    - 📉 Costes Directos: **{format_euro(costes_directos_global)}**
    - 📊 Margen Bruto: **{format_euro(margen_bruto_global)}**
    - 🏢 Costes Fijos: **{format_euro(costes_fijos_global)}**
    - 📈 EBITDA: **{format_euro(ebitda_global)}**
    """)
