# -------------------------------
# RESUMEN POR LÍNEA DE NEGOCIO
# -------------------------------
st.subheader("📦 Resumen Total por Línea de Negocio")

# Encabezado tabla
st.markdown("""
| Línea de Negocio | Facturación | Costes Directos | Margen Bruto |
|------------------|-------------|-----------------|--------------|
""")

total_facturacion = 0
total_costes_directos = 0
total_margen_bruto = 0

for linea_nombre, valores in resultados_lineas.items():
    facturacion = valores['facturacion']
    costes_directos = valores['costes_directos']
    margen_bruto = valores['margen_bruto']

    facturacion_txt = format_euro(facturacion)
    costes_directos_pct = (costes_directos / facturacion) if facturacion else None
    margen_bruto_pct = (margen_bruto / facturacion) if facturacion else None

    costes_directos_txt = f"{format_euro(costes_directos)} ({round(costes_directos_pct*100,1)}%)" if costes_directos_pct is not None else "—"
    margen_bruto_txt = f"{format_euro(margen_bruto)} ({round(margen_bruto_pct*100,1)}%)" if margen_bruto_pct is not None else "—"

    # Estado Margen Bruto
    bm_linea = benchmarks['lineas_negocio'].get(mapa_lineas_benchmark[linea_nombre])
    bm_margen = bm_linea['margen_bruto'] if bm_linea else None
    color, icono = get_estado(margen_bruto_pct, (bm_margen[0], bm_margen[2]) if bm_margen else None, tipo="margen")

    # Fila tabla
    st.markdown(f"""
| {linea_nombre} | {facturacion_txt} | {costes_directos_txt} | <span style='color:{color}; font-weight:bold'>{margen_bruto_txt} {icono}</span> |
""", unsafe_allow_html=True)

    total_facturacion += facturacion
    total_costes_directos += costes_directos
    total_margen_bruto += margen_bruto

# Total empresa
total_costes_pct = (total_costes_directos / total_facturacion) if total_facturacion else None
total_margen_pct = (total_margen_bruto / total_facturacion) if total_facturacion else None
bm_global_margen = benchmarks['global']['margen_bruto']

total_costes_txt = f"{format_euro(total_costes_directos)} ({round(total_costes_pct*100,1)}%)" if total_costes_pct is not None else "—"
total_margen_txt = f"{format_euro(total_margen_bruto)} ({round(total_margen_pct*100,1)}%)" if total_margen_pct is not None else "—"

# Estado margen total
color_total, icono_total = get_estado(total_margen_pct, (bm_global_margen[0], bm_global_margen[1]), tipo="margen")

st.markdown(f"""
| **TOTAL** | **{format_euro(total_facturacion)}** | **{total_costes_txt}** | <span style='color:{color_total}; font-weight:bold'>**{total_margen_txt} {icono_total}**</span> |
""", unsafe_allow_html=True)
