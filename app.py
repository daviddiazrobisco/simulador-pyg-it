import streamlit as st
import json
import plotly.graph_objects as go
import unicodedata

# -------------------------------
# Configuración general
# -------------------------------
st.set_page_config(page_title="Simulador PyG IT", page_icon="💻", layout="wide")

COLOR_VERDE = "#144C44"
COLOR_NARANJA = "#fb9200"
COLOR_ROJO = "#D33F49"
COLOR_GRIS = "#F2F2F2"
COLOR_TEXTO = "#333333"
COLOR_FONDO = "#FFFFFF"

# -------------------------------
# Funciones auxiliares
# -------------------------------
def normalizar(texto):
    """Quitar tildes, espacios y capitalizar"""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto.strip().title()

def format_euro(valor):
    formatted = f"{int(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"

def get_estado(valor, benchmark, tipo='mas_es_mejor'):
    min_val, media_val, max_val = benchmark
    if tipo == 'mas_es_mejor':
        if valor < min_val: return "⚠️", COLOR_ROJO
        elif valor <= max_val: return "✅", COLOR_VERDE
        else: return "⭐", COLOR_NARANJA
    else:
        if valor > max_val: return "⚠️", COLOR_ROJO
        elif valor >= min_val: return "✅", COLOR_VERDE
        else: return "⭐", COLOR_NARANJA

def calcular_linea(tarifa, ticket, unidades, personas, coste_persona, costes_directos_pct, jornadas_persona):
    facturacion = ticket * unidades
    costes_personas = personas * coste_persona
    costes_directos = (costes_directos_pct / 100) * facturacion
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
# Cargar datos
# -------------------------------
with open('data/benchmarks_it.json') as f:
    benchmarks = json.load(f)

with open('data/presupuesto_it_2025.json') as f:
    data = json.load(f)

nombre_benchmark = {
    "Implantacion": "consultoria",
    "Licencias": "software",
    "Hot Line": "mixto"
}

lineas_negocio = {normalizar(k): v for k, v in data['parametros']['lineas_negocio'].items()}
costes_fijos_detalle = {normalizar(k): v for k, v in data['parametros']['costes_fijos'].items()}
subactividad_permitida = data['parametros']['subactividad_permitida_%']

# -------------------------------
# Componente KPI reutilizable
# -------------------------------
def kpi_card(nombre, valor_abs, valor_pct, benchmark=None, tooltip=None):
    color, icono = COLOR_VERDE, "✅"
    if benchmark:
        color, icono = get_estado(valor_pct, benchmark, 'menos_es_mejor' if 'Coste' in nombre else 'mas_es_mejor')
    comparativa = f"<br><small>{round(valor_pct*100,1)}% sobre ventas</small>"

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
        <div style="font-size:14px; color:{COLOR_TEXTO};">{comparativa}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# -------------------------------
# Bloque Línea de Negocio
# -------------------------------
def bloque_linea(nombre_linea, datos_linea, benchmark_linea):
    with st.expander(f"🔽 {nombre_linea} (Haz clic para ajustar)", expanded=False):
        st.markdown(f"Ajusta los parámetros para la línea de negocio **{nombre_linea}** y observa el impacto en tiempo real.")

        # Sliders + KPIs
        col1, col2, col3 = st.columns(3)
        with col1:
            tarifa = st.slider(
                f"{nombre_linea} - Tarifa (€)", 500, 2000,
                int(datos_linea['tarifa']),
                step=50,
                key=f"{nombre_linea}_tarifa"
            )
            simbolo, color = get_estado(tarifa, benchmark_linea['precio_jornada'], 'mas_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Tarifa</b><br>{format_euro(tarifa)} {simbolo}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            ticket = st.slider(
                f"{nombre_linea} - Ticket medio (€)", 10000, 600000,
                int(datos_linea['ticket_medio']),
                step=5000,
                key=f"{nombre_linea}_ticket"
            )
            st.markdown(f"""
            <div style='border-left:5px solid {COLOR_VERDE}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Ticket Medio</b><br>{format_euro(ticket)}
            </div>
            """, unsafe_allow_html=True)

        with col3:
            unidades = st.slider(
                f"{nombre_linea} - Número de proyectos", 1, 100,
                int(datos_linea['unidades']),
                step=1,
                key=f"{nombre_linea}_unidades"
            )
            st.markdown(f"""
            <div style='border-left:5px solid {COLOR_VERDE}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Proyectos</b><br>{unidades}
            </div>
            """, unsafe_allow_html=True)

        col4, col5 = st.columns(2)
        with col4:
            personas = st.slider(
                f"{nombre_linea} - Número de personas", 0, 100,
                int(datos_linea['personas']),
                step=1,
                key=f"{nombre_linea}_personas"
            )
            st.markdown(f"""
            <div style='border-left:5px solid {COLOR_VERDE}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Personas</b><br>{personas}
            </div>
            """, unsafe_allow_html=True)

        with col5:
            coste_persona = st.slider(
                f"{nombre_linea} - Coste medio persona (€)", 30000, 90000,
                int(datos_linea['coste_medio_persona']),
                step=1000,
                key=f"{nombre_linea}_coste_persona"
            )
            st.markdown(f"""
            <div style='border-left:5px solid {COLOR_VERDE}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Coste Persona</b><br>{format_euro(coste_persona)}
            </div>
            """, unsafe_allow_html=True)

        costes_pct = st.slider(
            f"{nombre_linea} - Costes directos (%)", 0, 70,
            int(datos_linea['costes_directos_%']),
            step=1,
            key=f"{nombre_linea}_costes_pct"
        )
        st.markdown(f"""
        <div style='border-left:5px solid {COLOR_VERDE}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
            <b>Costes Directos (%)</b><br>{costes_pct}%
        </div>
        """, unsafe_allow_html=True)

        # Cálculos
        resultados = calcular_linea(
            tarifa, ticket, unidades,
            personas, coste_persona,
            costes_pct, datos_linea['jornadas_por_persona']
        )
