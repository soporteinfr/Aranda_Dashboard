import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet
import base64
import re
from collections import defaultdict

st.set_page_config(page_title='Gestión de Datos y Visualización', page_icon='assets/Imagen1.png', layout='wide')

def set_background(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded_image = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("assets/imagen.png")

st.title("Sube tu archivo Excel")

archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

if archivo is not None:
    try:
        col_used = [
            "Numero de caso", "Tipo de caso", "Fecha de registro", "Departamento",
            "Especialista", "Grupo de especialista", "Estado", "Asunto", "Descripcion",
            "Primer Nivel", "Segundo Nivel", "Fecha de en proceso", "Fecha de Pendiente 1",
            "Fecha de Cerrado", "Tiempo Total Solucion"
        ]

        @st.cache_data
        def cargar_datos(file, columnas):
            df = pd.read_excel(file, usecols=columnas, engine="openpyxl")
            columnas_fecha = ["Fecha de registro", "Fecha de en proceso", "Fecha de Pendiente 1", "Fecha de Cerrado"]
            for col in columnas_fecha:
                if df[col].dtype != 'datetime64[ns]':
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            return df

        bl = cargar_datos(archivo, col_used)
    except ValueError as e:
        st.error(f"Error al leer el archivo: {e}\n\nAsegúrate de que el archivo contiene todas las columnas requeridas:\n{', '.join(col_used)}")
        st.stop()


    grupos_disponibles = bl["Grupo de especialista"].dropna().unique()
    grupos_seleccionados = st.multiselect(
        "Selecciona uno o más grupos de especialista para visualizar",
        options=grupos_disponibles
    )

    # Visualización de datos por "Grupo de especialista"
    if grupos_seleccionados:
        for grupo in grupos_seleccionados:
            with st.expander(f"📁 Grupo: {grupo}", expanded=False):
                df_grupo = bl[bl["Grupo de especialista"] == grupo].copy()

                if "Fecha de registro" in df_grupo.columns and "Numero de caso" in df_grupo.columns:
                    df_grupo["Fecha de registro"] = pd.to_datetime(df_grupo["Fecha de registro"], errors="coerce")
                    df_grupo = df_grupo.dropna(subset=["Fecha de registro", "Numero de caso"])

                    df_grupo["Año"] = df_grupo["Fecha de registro"].dt.year
                    df_grupo["Año-Mes"] = df_grupo["Fecha de registro"].dt.to_period("M").astype(str)

                    años_disponibles = sorted(df_grupo["Año"].dropna().unique())
                    opcion = st.selectbox(f"Visualización para grupo '{grupo}'", ["Histórico"] + [str(a) for a in años_disponibles], key=grupo)

                    df_grafico = df_grupo.copy()
                    if opcion != "Histórico":
                        df_grafico = df_grupo[df_grupo["Año"] == int(opcion)]

                    resumen = df_grafico.groupby("Año-Mes")["Numero de caso"].count().reset_index(name="Cantidad")
                    resumen["Año-Mes"] = pd.to_datetime(resumen["Año-Mes"])
                    resumen = resumen.sort_values("Año-Mes")
                    resumen["Año-Mes"] = resumen["Año-Mes"].dt.strftime("%Y-%m")

                    # --- Selector para tipo de casos ---
                    opciones_estado = ["General", "Pendientes", "Cerrados"]
                    estado_seleccionado = st.selectbox("Filtrar por estado", opciones_estado, key=f"estado_{grupo}")

                    # Filtrar según selección
                    df_filtrado = df_grafico.copy()
                    if estado_seleccionado == "Pendientes":
                        df_filtrado = df_filtrado[df_filtrado["Estado"].str.lower() == "pendiente"]
                    elif estado_seleccionado == "Cerrados":
                        df_filtrado = df_filtrado[df_filtrado["Estado"].str.lower().isin(["cerrado", "solucionado"])]

                    # Validar si hay datos después del filtro
                    if df_filtrado.empty:
                        st.warning(f"No hay datos para la opción seleccionada: {estado_seleccionado}")
                    else:
                        if opcion == "Histórico":
                            df_filtrado = df_grafico.copy()
                            if estado_seleccionado == "Pendientes":
                                df_filtrado = df_filtrado[df_filtrado["Estado"].str.lower() == "pendiente"]
                            elif estado_seleccionado == "Cerrados":
                                df_filtrado = df_filtrado[df_filtrado["Estado"].str.lower().isin(["cerrado", "solucionado"])]

                            resumen = df_filtrado.groupby("Año-Mes")["Numero de caso"].count().reset_index(name="Cantidad")
                            resumen["Año-Mes"] = pd.to_datetime(resumen["Año-Mes"])
                            resumen = resumen.sort_values("Año-Mes")
                            resumen["Año-Mes"] = resumen["Año-Mes"].dt.strftime("%Y-%m")

                            fig = px.line(
                                resumen, x="Año-Mes", y="Cantidad", markers=True,
                                title=f"Total de casos registrados por mes - {estado_seleccionado}",
                                labels={"Año-Mes": "Mes", "Cantidad": "Número de Casos"}
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        else:
                            año_seleccionado = int(opcion)
                            año_anterior = año_seleccionado - 1

                            df_actual = df_grupo[df_grupo["Año"] == año_seleccionado].copy()
                            df_anterior = df_grupo[df_grupo["Año"] == año_anterior].copy()

                            # Aplicar filtro de estado
                            if estado_seleccionado == "Pendientes":
                                df_actual = df_actual[df_actual["Estado"].str.lower() == "pendiente"]
                                df_anterior = df_anterior[df_anterior["Estado"].str.lower() == "pendiente"]
                            elif estado_seleccionado == "Cerrados":
                                df_actual = df_actual[df_actual["Estado"].str.lower().isin(["cerrado", "solucionado"])]
                                df_anterior = df_anterior[df_anterior["Estado"].str.lower().isin(["cerrado", "solucionado"])]

                            resumen_actual = df_actual.groupby(df_actual["Fecha de registro"].dt.month)["Numero de caso"].count().reset_index(name="Cantidad")
                            resumen_actual.columns = ["Mes", "Cantidad"]

                            resumen_anterior = df_anterior.groupby(df_anterior["Fecha de registro"].dt.month)["Numero de caso"].count().reset_index(name="Cantidad")
                            resumen_anterior.columns = ["Mes", "Cantidad"]

                            fig = go.Figure()

                            fig.add_trace(go.Scatter(
                                x=resumen_actual["Mes"], y=resumen_actual["Cantidad"],
                                mode="lines+markers", name=f"Año {año_seleccionado}",
                                line=dict(dash="solid", color="#1f77b4")
                            ))

                            if not resumen_anterior.empty:
                                fig.add_trace(go.Scatter(
                                    x=resumen_anterior["Mes"], y=resumen_anterior["Cantidad"],
                                    mode="lines+markers", name=f"Año {año_anterior}",
                                    line=dict(dash="dot", color="#ff7f0e")
                                ))

                            fig.update_layout(
                                title=f"Comparación de casos registrados - {estado_seleccionado}",
                                xaxis=dict(title="Mes", tickmode="array", tickvals=list(range(1, 13)),
                                        ticktext=["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]),
                                yaxis_title="Número de Casos"
                            )

                            st.plotly_chart(fig, use_container_width=True)

                    total_casos = len(df_grafico)
                    estados = df_grafico["Estado"].dropna().str.lower()
                    total_cerrados = estados.isin(["cerrado", "solucionado"]).sum()
                    total_pendientes = estados.isin(["pendiente"]).sum()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total de casos", total_casos)
                    col2.metric("Total cerrados", total_cerrados)
                    col3.metric("Total pendientes", total_pendientes)

                    with st.container():
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        col4, col5, col6 = st.columns(3)

                        # Indicador 1: Promedio Solución
                        tiempos_validos = df_grafico["Tiempo Total Solucion"].dropna()
                        tiempos_validos = tiempos_validos[tiempos_validos.apply(lambda x: isinstance(x, (int, float)))]
                        if not tiempos_validos.empty:
                            promedio_minutos = tiempos_validos.mean()
                            horas = int(promedio_minutos // 60)
                            minutos = int(promedio_minutos % 60)
                            tiempo_formateado = f"{horas}h {minutos}min" if horas > 0 else f"{minutos}min"
                        else:
                            tiempo_formateado = "No disponible"

                        # Indicador 2: Mayor Tipo Caso
                        tipos = df_grafico["Tipo de caso"].dropna().astype(str).str.strip().replace("Rquerimiento", "Requerimiento")
                        tipo_mas_comun = tipos.value_counts().idxmax() if not tipos.empty else "No disponible"

                        # Mostrar indicadores
                        with col4:
                            st.metric("Promedio Solución", tiempo_formateado)

                        with col5:
                            st.metric("Mayor Tipo Caso", tipo_mas_comun)

                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    
                    # Gráfica de participación Pendientes vs Cerrados + Tabla de estados
                    col_estado_pie, col_estado_tabla = st.columns(2)

                    with col_estado_pie:
                        estados = df_grafico["Estado"].dropna().str.strip()
                        estados_lower = estados.str.lower()
                        total_pendientes = estados_lower.isin(["pendiente"]).sum()
                        total_cerrados = estados_lower.isin(["cerrado", "solucionado"]).sum()
                        total_otros = len(df_grafico) - (total_pendientes + total_cerrados)

                        participacion = pd.DataFrame({
                            "Estado": ["Pendientes", "Cerrados", "Otros"],
                            "Cantidad": [total_pendientes, total_cerrados, total_otros]
                        })

                        fig_estado = px.pie(
                            participacion,
                            names="Estado",
                            values="Cantidad",
                            title="Participación de casos por estado (Pendientes vs Cerrados)",
                            color="Estado",
                            color_discrete_map={"Pendientes": "#ECAB33", "Cerrados": "#1A6FDF", "Otros": "#525252"},
                            hole=0.3
                        )
                        fig_estado.update_traces(textinfo="percent")
                        st.plotly_chart(fig_estado, use_container_width=True)

                    with col_estado_tabla:
                        # Tabla con todos los estados desagregados
                        conteo_estados = estados.value_counts().reset_index()
                        conteo_estados.columns = ["Estados", "Casos"]
                        conteo_estados.index = conteo_estados.index + 1
                        st.markdown("### Distribución por Estado")
                        st.dataframe(conteo_estados)

                    # Gráficas de pastel por grupo "Especialista"
                    col_pie1, col_pie2 = st.columns(2)

                    # Tabla de casos cerrados.
                    df_cerrados = df_grafico[df_grafico["Estado"].str.lower().isin(["cerrado", "solucionado"])]
                    if not df_cerrados.empty:
                        cerrados_por_analista = df_cerrados["Especialista"].value_counts().reset_index()
                        cerrados_por_analista.columns = ["Especialista", "Cantidad"]
                        cerrados_por_analista.index = cerrados_por_analista.index + 1
                        fig_cerrados = px.pie(
                            cerrados_por_analista,
                            names="Especialista",
                            values="Cantidad",
                            title="Distribución de casos cerrados por analista",
                            hole=0.3
                        )
                        col_pie1.plotly_chart(fig_cerrados, use_container_width=True)
                    else:
                        col_pie1.info("No hay casos cerrados para mostrar.")

                    # Tabla de casos pendientes.
                    df_pendientes = df_grafico[df_grafico["Estado"].str.lower() == "pendiente"]
                    if not df_pendientes.empty:
                        pendientes_por_analista = df_pendientes["Especialista"].value_counts().reset_index()
                        pendientes_por_analista.columns = ["Especialista", "Cantidad"]
                        fig_pendientes = px.pie(
                            pendientes_por_analista,
                            names="Especialista",
                            values="Cantidad",
                            title="Distribución de casos pendientes por analista",
                            hole=0.3
                        )
                        col_pie2.plotly_chart(fig_pendientes, use_container_width=True)

                        col_tabla1, col_tabla2 = st.columns(2)

                        with col_tabla1:
                            if not df_cerrados.empty:
                                tabla_cerrados = df_cerrados["Especialista"].value_counts().reset_index()
                                tabla_cerrados.columns = ["Especialista", "Cantidad de Casos Cerrados"]
                                tabla_cerrados.index = tabla_cerrados.index + 1
                                st.dataframe(tabla_cerrados)
                            else:
                                st.info("No hay datos de casos cerrados para mostrar.")

                        with col_tabla2:
                            if not df_pendientes.empty:
                                tabla_pendientes = df_pendientes["Especialista"].value_counts().reset_index()
                                tabla_pendientes.columns = ["Especialista", "Cantidad de Casos Pendientes"]
                                tabla_pendientes.index = tabla_pendientes.index + 1
                                st.dataframe(tabla_pendientes)
                            else:
                                st.info("No hay datos de casos pendientes para mostrar.")

                    else:
                        col_pie2.info("No hay casos pendientes para mostrar.")
                        
                    trigger_map = {}
                    try:
                        with open("Triggers.txt", "r", encoding="utf-8") as f:
                            for line in f:
                                if ":" in line:
                                    category, keywords = line.strip().split(":", 1)
                                    trigger_map[category.strip()] = [kw.strip().lower() for kw in keywords.split(",") if kw.strip()]
                    except FileNotFoundError:
                        st.error("No se encontró el archivo Triggers.txt. Asegúrate de subirlo o colocarlo en la misma carpeta que app.py.")
                        
                    # Prioridad en caso de empate
                    prioridad = ["Matricula", "Renovación", "CajasWeb"]

                    def categorize_row(row):
                        asunto = str(row["Asunto"]).lower()
                        descripcion = str(row["Descripcion"]).lower()
                        counts = defaultdict(float)
                        tiene_actualizacion = False

                        # Buscar en Asunto y Descripción
                        for category, keywords in trigger_map.items():
                            for kw in keywords:
                                if kw in asunto or kw in descripcion:
                                    if "actualización" in category.lower():
                                        tiene_actualizacion = True
                                        counts[category] += 0.2  # Penalización ligera
                                    elif "sirp" in category.lower():
                                        counts[category] += 0.3  # Penalización SIRP
                                    else:
                                        counts[category] += 1.0

                        if counts:
                            # Si hay más de una categoría y una es Actualización, ignorarla si hay otra con más peso
                            if tiene_actualizacion and len(counts) > 1:
                                # Eliminar Actualización si hay otra categoría con mayor peso
                                actualizacion_key = [k for k in counts.keys() if "actualización" in k.lower()]
                                for key in actualizacion_key:
                                    del counts[key]

                            # Si después de eliminar sigue vacío, devolver Actualización
                            if not counts and tiene_actualizacion:
                                return "Actualización de datos"

                            # Elegir la categoría con mayor peso
                            max_count = max(counts.values())
                            candidatas = [cat for cat, val in counts.items() if val == max_count]

                            # Si hay empate, aplicar prioridad
                            for p in prioridad:
                                if p.lower() in [c.lower() for c in candidatas]:
                                    return p

                            return candidatas[0]
                        else:
                            # Si no hay coincidencias, pero había Actualización
                            if tiene_actualizacion:
                                return "Actualización de datos"
                            return "Otras aplicaciones de registro"

                    # Aplicar categorización
                    df_grafico["Categoria Detectada"] = df_grafico.apply(categorize_row, axis=1)

                    # Top 10 categorías
                    top_categories = df_grafico["Categoria Detectada"].value_counts().nlargest(10).reset_index()
                    top_categories.columns = ["Aplicación", "Cantidad"]

                    # Gráfica horizontal con etiquetas dentro
                    fig_apps = px.bar(
                        top_categories.sort_values("Cantidad", ascending=True),
                        x="Cantidad",
                        y="Aplicación",
                        orientation="h",
                        title="Top 10 Categorías de Aplicaciones",
                        labels={"Cantidad": "Número de Casos", "Aplicación": "Aplicación"},
                        color="Cantidad",
                        color_continuous_scale="Blues",
                        text="Cantidad"
                    )

                    fig_apps.update_traces(textposition="inside")
                    st.plotly_chart(fig_apps, use_container_width=True)

                    # Filtrar por estado
                    df_estado = df_grupo.copy()
                    if estado_seleccionado == "Pendientes":
                        df_estado = df_estado[df_estado["Estado"].str.lower() == "pendiente"]
                    elif estado_seleccionado == "Cerrados":
                        df_estado = df_estado[df_estado["Estado"].str.lower().isin(["cerrado", "solucionado"])]

                    # Agrupar por Año-Mes
                    df_estado["Año-Mes"] = df_estado["Fecha de registro"].dt.to_period("M").astype(str)
                    resumen_full = df_estado.groupby("Año-Mes")["Numero de caso"].count().reset_index(name="Cantidad")
                    resumen_full["Año-Mes"] = pd.to_datetime(resumen_full["Año-Mes"], format="%Y-%m")
                    resumen_full = resumen_full.sort_values("Año-Mes")

                    # Reindexar para completar meses faltantes con 0
                    full_range = pd.date_range(start=resumen_full["Año-Mes"].min(), end=resumen_full["Año-Mes"].max(), freq="MS")
                    resumen_full = resumen_full.set_index("Año-Mes").reindex(full_range, fill_value=0).rename_axis("Año-Mes").reset_index()

                    # Preparar datos para Prophet
                    df_prophet = resumen_full.rename(columns={"Año-Mes": "ds", "Cantidad": "y"})

                    if len(df_prophet) >= 24:
                        try:
                            modelo = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
                            modelo.fit(df_prophet)

                            # Crear fechas futuras
                            future = modelo.make_future_dataframe(periods=6, freq="MS")
                            forecast = modelo.predict(future)

                            # Extraer proyección
                            df_proyeccion = forecast[["ds", "yhat"]].tail(6).rename(columns={"ds": "Mes", "yhat": "Proyección"})

                            # Gráfico
                            fig_forecast = px.line(
                                df_prophet,
                                x="ds", y="y", markers=True,
                                title=f"Proyección Prophet - Estado: {estado_seleccionado}",
                                labels={"ds": "Mes", "y": "Número de Casos"}
                            )
                            fig_forecast.add_scatter(
                                x=df_proyeccion["Mes"], y=df_proyeccion["Proyección"],
                                mode="lines+markers", name="Proyección",
                                line=dict(dash="dot", color="red")
                            )

                            st.plotly_chart(fig_forecast, use_container_width=True)
                            st.subheader("📅 Tabla de Proyección")
                            df_proyeccion["Mes"] = df_proyeccion["Mes"].dt.strftime("%Y-%m")
                            df_proyeccion.index = df_proyeccion.index + 1
                            st.dataframe(df_proyeccion)

                        except Exception as e:
                            st.warning(f"No se pudo generar la proyección con Prophet: {e}")
                    else:
                        st.warning("No hay suficientes datos mensuales para generar una proyección confiable (mínimo 24 meses).")