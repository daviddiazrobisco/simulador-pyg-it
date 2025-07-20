def bloque_linea(nombre_linea, datos_linea, benchmark_linea):
    st.markdown(f"### 🔽 {nombre_linea.upper()}")
    with st.expander(f"📂 Ajustes y Resultados - {nombre_linea}", expanded=False):

        # Sliders sobre KPI en una sola fila
        cols = st.columns(3)
        # Ticket Medio
        with cols[0]:
            nuevo_ticket = st.slider("Ticket Medio (€)", 
                                     min_value=int(datos_linea['ticket_medio'] * 0.5),
                                     max_value=int(datos_linea['ticket_medio'] * 1.5),
                                     value=int(datos_linea['ticket_medio']),
                                     step=1000,
                                     format="%d")
            kpi_card("Ticket Medio", nuevo_ticket, nuevo_ticket / facturacion_total,
                     tooltip="Valor medio por proyecto")

        # Unidades
        with cols[1]:
            nuevo_unidades = st.slider("Número de Unidades", 
                                       min_value=0, max_value=int(datos_linea['unidades']*2),
                                       value=int(datos_linea['unidades']), step=1)
            kpi_card("Número de Unidades", nuevo_unidades, nuevo_unidades / facturacion_total,
                     tooltip="Proyectos o ventas")

        # Personas (solo si aplica)
        if datos_linea['personas'] > 0 and datos_linea['coste_medio_persona'] > 0:
            with cols[2]:
                nuevo_personas = st.slider("Personas", 
                                           min_value=0, max_value=int(max(1, datos_linea['personas']*2)),
                                           value=int(datos_linea['personas']), step=1)
                kpi_card("Personas", nuevo_personas, nuevo_personas / facturacion_total,
                         tooltip="Número de personas asignadas")

            # Coste Medio Persona
            nuevo_coste_medio = st.slider("Coste Medio Persona (€)", 
                                          min_value=int(datos_linea['coste_medio_persona'] * 0.8),
                                          max_value=int(datos_linea['coste_medio_persona'] * 1.2),
                                          value=int(datos_linea['coste_medio_persona']),
                                          step=1000,
                                          format="%d")
            kpi_card("Coste Medio Persona", nuevo_coste_medio, 
                     (nuevo_coste_medio*nuevo_personas)/facturacion_total,
                     tooltip="Coste anual medio por persona")
        else:
            nuevo_personas = 0
            nuevo_coste_medio = 0
            st.markdown("⚡ **Sin personas asignadas. No aplica ajuste de coste medio ni nivel de actividad.**")

        # Cálculos resultados
        facturacion = nuevo_ticket * nuevo_unidades
        costes_personal = nuevo_personas * nuevo_coste_medio
        costes_directos_pct = datos_linea['costes_directos_%']
        costes_directos = facturacion * (costes_directos_pct / 100) + costes_personal
        margen_bruto = facturacion - costes_directos

        # KPIs resultados
        st.subheader("📊 KPIs Resultados")
        col1, col2, col3 = st.columns(3)
        with col1:
            kpi_card("Facturación", facturacion, facturacion/facturacion_total,
                     tooltip="Facturación total línea")
        with col2:
            kpi_card("Costes Directos", costes_directos, costes_directos/facturacion_total,
                     benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None,
                     tipo="coste",
                     tooltip="Costes directos de la línea")
        with col3:
            kpi_card("Margen Bruto", margen_bruto, margen_bruto/facturacion_total,
                     benchmark=(benchmark_linea['margen_bruto'][0], benchmark_linea['margen_bruto'][2]) if benchmark_linea else None,
                     tipo="margen",
                     tooltip="Ingresos menos costes directos")

        # Nivel de actividad (solo si aplica)
        if datos_linea['personas'] > 0 and datos_linea['jornadas_por_persona'] > 0:
            st.subheader("⏱️ Nivel de Actividad")
            jornadas_disponibles = nuevo_personas * datos_linea['jornadas_por_persona']
            jornadas_utilizadas = (facturacion / datos_linea['tarifa'])
            nivel_utilizacion = jornadas_utilizadas / jornadas_disponibles * 100
            benchmark_util = benchmark_linea['utilizacion'] if benchmark_linea else [0.6, 0.75]

            # Velocímetro
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=nivel_utilizacion,
                title={'text': "Utilización (%)"},
                gauge={
                    'axis': {'range': [0, 120]},
                    'bar': {'color': COLOR_NARANJA},
                    'steps': [
                        {'range': [0, benchmark_util[0]*100], 'color': COLOR_ESTRELLA},
                        {'range': [benchmark_util[0]*100, benchmark_util[1]*100], 'color': COLOR_VERDE},
                        {'range': [benchmark_util[1]*100, 120], 'color': COLOR_ROJO}
                    ]
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown(f"""
            📅 **Jornadas disponibles:** {int(jornadas_disponibles)}  
            ✅ **Jornadas utilizadas:** {int(jornadas_utilizadas)}  
            📊 **% Jornadas utilizadas:** {nivel_utilizacion:.1f}%  
            🔄 **Subactividad asumible ({int(subactividad_permitida*100)}%):** {int(jornadas_disponibles*subactividad_permitida)} jornadas  
            🚨 **Exceso Subactividad:** {max(0, int(jornadas_disponibles - jornadas_utilizadas - jornadas_disponibles*subactividad_permitida))} jornadas  
            💸 **Coste asociado:** {format_euro(max(0, (jornadas_disponibles - jornadas_utilizadas - jornadas_disponibles*subactividad_permitida)*nuevo_coste_medio/datos_linea['jornadas_por_persona']))}
            """)
        else:
            st.markdown("⚡ **Nivel de actividad no aplica. Uso 100% supuesto.**")

        # Gráfico cascada
        st.subheader(f"📉 Resumen Económico - {nombre_linea}")
        fig_cascada = go.Figure(go.Waterfall(
            name=nombre_linea,
            orientation="v",
            measure=["relative", "relative", "total"],
            x=["Facturación", "Costes Directos", "Margen Bruto"],
            textposition="outside",
            text=[format_euro(facturacion), format_euro(-costes_directos), format_euro(margen_bruto)],
            y=[facturacion, -costes_directos, margen_bruto],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_cascada.update_layout(
            title=f"{nombre_linea} - Facturación / Costes Directos / Margen Bruto",
            plot_bgcolor=COLOR_FONDO,
            paper_bgcolor=COLOR_FONDO,
            font=dict(color=COLOR_TEXTO),
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig_cascada, use_container_width=True)

        return facturacion, costes_directos, margen_bruto
