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

        # -------------------------------
        # Cálculos
        # -------------------------------
        resultados = calcular_linea(
            tarifa, ticket, unidades,
            personas, coste_persona,
            costes_pct, datos_linea['jornadas_por_persona']
        )

        # -------------------------------
        # KPIs Resumen
        # -------------------------------
        st.markdown(f"### 📊 Resultados Línea {nombre_linea}")
        col1, col2, col3 = st.columns(3)
        with col1:
            simbolo, color = get_estado(resultados['facturacion'], benchmark_linea['precio_jornada'], 'mas_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Facturación</b><br>{format_euro(resultados['facturacion'])} {simbolo}
            </div>
            """, unsafe_allow_html=True)
        with col2:
            simbolo, color = get_estado(resultados['costes_directos'], benchmark_linea['margen_bruto'], 'menos_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Costes Directos</b><br>{format_euro(resultados['costes_directos'])} {simbolo}
            </div>
            """, unsafe_allow_html=True)
        with col3:
            simbolo, color = get_estado(resultados['margen_bruto'], benchmark_linea['ebitda'], 'mas_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:{COLOR_GRIS}'>
                <b>Margen Bruto</b><br>{format_euro(resultados['margen_bruto'])} {simbolo}
            </div>
            """, unsafe_allow_html=True)

        # -------------------------------
        # Velocímetro Nivel Actividad
        # -------------------------------
        if resultados['nivel_actividad'] is not None:
            min_sub, media_sub, max_sub = benchmark_linea['utilizacion']
            gauge_color = COLOR_VERDE if min_sub * 100 <= resultados['nivel_actividad'] <= max_sub * 100 else COLOR_ROJO
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=resultados['nivel_actividad'],
                title={'text': "Nivel de Actividad (%)"},
                gauge={
                    'axis': {'range': [0, 120]},
                    'bar': {'color': gauge_color},
                    'steps': [
                        {'range': [0, min_sub * 100], 'color': COLOR_NARANJA},
                        {'range': [min_sub * 100, max_sub * 100], 'color': COLOR_VERDE},
                        {'range': [max_sub * 100, 100], 'color': COLOR_NARANJA},
                        {'range': [100, 120], 'color': COLOR_ROJO}
                    ]
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

        else:
            st.markdown("ℹ️ **Sin nivel de actividad (100% uso supuesto)**")

        # -------------------------------
        # Gráfico cascada
        # -------------------------------
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
        st.plotly_chart(fig_cascada, use_container_width=True)
