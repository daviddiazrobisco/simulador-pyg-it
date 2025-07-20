def bloque_linea(nombre_linea, datos_linea, benchmark_linea):
    with st.expander(f"🔽 {nombre_linea} (Haz clic para ajustar)", expanded=False):
        st.markdown(f"Ajusta los parámetros para la línea de negocio **{nombre_linea}** y observa el impacto en tiempo real.")

        # -------------------------------
        # Sliders + Tarjetas KPI
        # -------------------------------
        st.markdown("### 🎛️ Ajustes de parámetros")

        col1, col2, col3 = st.columns(3)
        with col1:
            tarifa = st.slider("Tarifa (€)", 500, 2000, int(datos_linea['tarifa']), step=50)
            simbolo, color = get_estado(tarifa, benchmark_linea['precio_jornada'], 'mas_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Tarifa</b><br>{format_euro(tarifa)} {simbolo}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            ticket = st.slider("Ticket medio (€)", 10000, 600000, int(datos_linea['ticket_medio']), step=5000)
            st.markdown(f"""
            <div style='border-left:5px solid #144C44; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Ticket Medio</b><br>{format_euro(ticket)}
            </div>
            """, unsafe_allow_html=True)

        with col3:
            unidades = st.slider("Número de proyectos", 1, 100, int(datos_linea['unidades']), step=1)
            st.markdown(f"""
            <div style='border-left:5px solid #144C44; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Proyectos</b><br>{unidades}
            </div>
            """, unsafe_allow_html=True)

        col4, col5 = st.columns(2)
        with col4:
            personas = st.slider("Número de personas", 0, 100, int(datos_linea['personas']), step=1)
            st.markdown(f"""
            <div style='border-left:5px solid #144C44; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Personas</b><br>{personas}
            </div>
            """, unsafe_allow_html=True)

        with col5:
            coste_persona = st.slider("Coste medio persona (€)", 30000, 90000, int(datos_linea['coste_medio_persona']), step=1000)
            st.markdown(f"""
            <div style='border-left:5px solid #144C44; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Coste Persona</b><br>{format_euro(coste_persona)}
            </div>
            """, unsafe_allow_html=True)

        # Costes directos (%)
        costes_pct = st.slider("Costes directos (%)", 0, 70, int(datos_linea['costes_directos_%']), step=1)
        st.markdown(f"""
        <div style='border-left:5px solid #144C44; padding:10px; border-radius:8px; background-color:#F2F2F2'>
            <b>Costes Directos (%)</b><br>{costes_pct}%
        </div>
        """, unsafe_allow_html=True)

        # -------------------------------
        # Cálculos
        # -------------------------------
        resultados = calcular_linea(tarifa, ticket, unidades, personas, coste_persona, costes_pct, datos_linea['jornadas_por_persona'])

        # -------------------------------
        # KPIs Resumen
        # -------------------------------
        st.markdown(f"### 📊 Resultados Línea {nombre_linea}")
        col1, col2, col3 = st.columns(3)
        with col1:
            simbolo, color = get_estado(resultados['facturacion'], benchmark_linea['precio_jornada'], 'mas_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Facturación</b><br>{format_euro(resultados['facturacion'])} {simbolo}
            </div>
            """, unsafe_allow_html=True)
        with col2:
            simbolo, color = get_estado(resultados['costes_directos'], benchmark_linea['margen_bruto'], 'menos_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Costes Directos</b><br>{format_euro(resultados['costes_directos'])} {simbolo}
            </div>
            """, unsafe_allow_html=True)
        with col3:
            simbolo, color = get_estado(resultados['margen_bruto'], benchmark_linea['ebitda'], 'mas_es_mejor')
            st.markdown(f"""
            <div style='border-left:5px solid {color}; padding:10px; border-radius:8px; background-color:#F2F2F2'>
                <b>Margen Bruto</b><br>{format_euro(resultados['margen_bruto'])} {simbolo}
            </div>
            """, unsafe_allow_html=True)

        # -------------------------------
        # Velocímetro Nivel Actividad
        # -------------------------------
        if resultados['nivel_actividad'] is not None:
            min_sub, media_sub, max_sub = benchmark_linea['utilizacion']
            gauge_color = "#144C44" if min_sub * 100 <= resultados['nivel_actividad'] <= max_sub * 100 else "#D33F49"
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=resultados['nivel_actividad'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Nivel de Actividad (%)"},
                gauge={
                    'axis': {'range': [0, 120]},
                    'bar': {'color': gauge_color},
                    'steps': [
                        {'range': [0, min_sub * 100], 'color': "#fb9200"},
                        {'range': [min_sub * 100, max_sub * 100], 'color': "#144C44"},
                        {'range': [max_sub * 100, 100], 'color': "#fb9200"},
                        {'range': [100, 120], 'color': "#D33F49"}
                    ]
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Texto debajo del velocímetro
            jornadas_por_persona = datos_linea['jornadas_por_persona']
            coste_asociado = (
                resultados['subactividad_jornadas'] * coste_persona / jornadas_por_persona
                if resultados['subactividad_jornadas'] and jornadas_por_persona > 0 else 0
            )
            st.markdown(f"""
            📅 **Jornadas disponibles**: {int(resultados['jornadas_totales']) if resultados['jornadas_totales'] else '—'}  
            ✅ **Jornadas utilizadas**: {int(resultados['jornadas_utilizadas']) if resultados['jornadas_utilizadas'] else '—'}  
            📊 **% Jornadas utilizadas**: {round(resultados['nivel_actividad'], 1)}%  
            🔄 **Subactividad asumible ({data['parametros']['subactividad_permitida_%']}%)**: {int(resultados['jornadas_totales'] * data['parametros']['subactividad_permitida_%']/100) if resultados['jornadas_totales'] else '—'} jornadas  
            🚨 **Exceso Subactividad**: {int(resultados['subactividad_jornadas']) if resultados['subactividad_jornadas'] > 0 else 0} jornadas  
            💸 **Coste asociado**: {format_euro(coste_asociado) if coste_asociado else '—'}
            """)

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
        fig_cascada.update_layout(
            title=f"Gráfico Cascada - {nombre_linea}",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color="#333333")
        )
        st.plotly_chart(fig_cascada, use_container_width=True)
