import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import base64
import re

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

os.makedirs("data", exist_ok=True)
os.makedirs("data_filtered", exist_ok=True)

st.title("Sube tu archivo Excel")

archivo = st.file_uploader("Sube el archivo Excel", type=["xlsx"])

archivo_guardado = False
ruta_guardado = ""

if archivo:
    ruta_guardado = os.path.join("data", archivo.name)
    if os.path.exists(ruta_guardado):
        st.warning(f"El archivo '{archivo.name}' ya ha sido subido previamente.\n\n"
                   f"Puedes cambiar el nombre del archivo para realizar una nueva operación o continuar con el archivo existente.")
        archivo_guardado = True
    else:
        with open(ruta_guardado, "wb") as f:
            f.write(archivo.getbuffer())
        st.success(f"Archivo guardado en: {ruta_guardado}")
        archivo_guardado = True

if archivo_guardado:
    col_used = [
        "Numero de caso", "Fecha de registro", "Especialista", "Grupo de especialista", "Estado",
        "Asunto", "Descripcion", "Primer Nivel", "Segundo Nivel",
        "Fecha de en proceso", "Fecha de Pendiente 1", "Fecha de Cerrado"
    ]

    @st.cache_data
    def cargar_datos(ruta, columnas):
        df = pd.read_excel(ruta, usecols=columnas, engine="openpyxl")
        columnas_fecha = ["Fecha de registro", "Fecha de en proceso", "Fecha de Pendiente 1", "Fecha de Cerrado"]
        for col in columnas_fecha:
            if df[col].dtype != 'datetime64[ns]':
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    try:
        bl = cargar_datos(ruta_guardado, col_used)
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

                            df_actual = df_grafico[df_grafico["Año"] == año_seleccionado]
                            df_anterior = df_grafico[df_grafico["Año"] == año_anterior]

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
                                        ticktext=["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]),
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

                    # Gráficas de pastel por grupo "Especialista"
                    col_pie1, col_pie2 = st.columns(2)

                    # Tabla de casos cerrados.
                    df_cerrados = df_grafico[df_grafico["Estado"].str.lower().isin(["cerrado", "solucionado"])]
                    if not df_cerrados.empty:
                        cerrados_por_analista = df_cerrados["Especialista"].value_counts().reset_index()
                        cerrados_por_analista.columns = ["Especialista", "Cantidad"]
                        fig_cerrados = px.pie(
                            cerrados_por_analista,
                            names="Especialista",
                            values="Cantidad",
                            title="Distribución de casos cerrados por analista"
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
                            title="Distribución de casos pendientes por analista"
                        )
                        col_pie2.plotly_chart(fig_pendientes, use_container_width=True)

                        col_tabla1, col_tabla2 = st.columns(2)

                        with col_tabla1:
                            if not df_cerrados.empty:
                                tabla_cerrados = df_cerrados["Especialista"].value_counts().reset_index()
                                tabla_cerrados.columns = ["Especialista", "Cantidad de Casos Cerrados"]
                                st.dataframe(tabla_cerrados)
                            else:
                                st.info("No hay datos de casos cerrados para mostrar.")

                        with col_tabla2:
                            if not df_pendientes.empty:
                                tabla_pendientes = df_pendientes["Especialista"].value_counts().reset_index()
                                tabla_pendientes.columns = ["Especialista", "Cantidad de Casos Pendientes"]
                                st.dataframe(tabla_pendientes)
                            else:
                                st.info("No hay datos de casos pendientes para mostrar.")

                    else:
                        col_pie2.info("No hay casos pendientes para mostrar.")

                    # Mapeo de palabras clave para clasificación
                    trigger_map = {
                        'Matriculas_Constitucion': ['Asociar', 'MT', 'SC', 'capital suscrito', 'corregir ceros'],
                        'SVI - Servicio Virtual de Inscripcion': ['SI'],
                        'Renovacion Nacional': ['RN', 'renovacion'],
                        'Proponentes': ['PW', 'proponentes'],
                        'Actualización de datos': ['AC'],
                        'Certificado Electrónico': ['certificado'],
                        'Otras aplicaciones de registro': ['procesar pago']
                    }

                    # Función para limpiar nombres (quitar números y espacios, capitalizar)
                    def clean_name(name):
                        name = str(name).strip()  # quitar espacios
                        name = re.sub(r'^\d+\s*', '', name)  # quitar números al inicio
                        return name.capitalize()

                    # Función para categorizar cada fila
                    def categorize_row(row):
                        segundo = str(row['Segundo Nivel']).strip()
                        primero = str(row['Primer Nivel']).strip()
                        asunto = str(row['Asunto']).strip()
                        descripcion = str(row['Descripcion']).strip()

                        # Considerar Solicitud, Falla y Fallo
                        if segundo in ['Solicitud', 'Falla', 'Fallo', 'Aplicaciones']:
                            if 'otros' in primero.lower():
                                return 'Otras aplicaciones de registro'
                            elif primero == 'Aplicaciones':
                                # Buscar en Asunto
                                for categoria, keywords in trigger_map.items():
                                    if any(kw.lower() in asunto.lower() for kw in keywords):
                                        return categoria
                                # Buscar en Descripcion
                                for categoria, keywords in trigger_map.items():
                                    if any(kw.lower() in descripcion.lower() for kw in keywords):
                                        return categoria
                                return 'Otras aplicaciones de registro'
                            else:
                                return clean_name(primero)
                        else:
                            if 'otros' in segundo.lower():
                                return 'Otras aplicaciones de registro'
                            return clean_name(segundo)

                    # Aplicar categorización
                    df_grafico['Categoria'] = df_grafico.apply(categorize_row, axis=1)

                    # Contar frecuencias y dejar solo el TOP 10
                    conteo_categorias = df_grafico['Categoria'].value_counts().reset_index()
                    conteo_categorias.columns = ['Aplicación', 'Cantidad']
                    conteo_top10 = conteo_categorias.head(10)

                    # Crear gráfica de barras horizontal ordenada
                    fig_apps = px.bar(
                        conteo_top10.sort_values('Cantidad', ascending=True),
                        x='Cantidad', y='Aplicación', orientation='h',
                        title='Top 10 Categorías de Aplicaciones',
                        labels={'Cantidad': 'Número de Casos', 'Aplicación': 'Aplicación'},
                        color='Cantidad', color_continuous_scale='Blues'
                    )

                    st.plotly_chart(fig_apps, use_container_width=True)
                    
                    # Holt-Winters Forecasting con filtro por estado
                    df_estado = df_grupo.copy()
                    if estado_seleccionado == "Pendientes":
                        df_estado = df_estado[df_estado["Estado"].str.lower() == "pendiente"]
                    elif estado_seleccionado == "Cerrados":
                        df_estado = df_estado[df_estado["Estado"].str.lower().isin(["cerrado", "solucionado"])]

                    # Agrupar por Año-Mes
                    resumen_full = df_estado.groupby("Año-Mes")["Numero de caso"].count().reset_index(name="Cantidad")
                    resumen_full["Año-Mes"] = pd.to_datetime(resumen_full["Año-Mes"], format="%Y-%m")
                    resumen_full = resumen_full.sort_values("Año-Mes")
                    resumen_full.set_index("Año-Mes", inplace=True)

                    # Reindexar para completar meses faltantes con 0
                    full_range = pd.date_range(start=resumen_full.index.min(), end=resumen_full.index.max(), freq="MS")
                    resumen_full = resumen_full.reindex(full_range, fill_value=0)
                    resumen_full.index.freq = "MS"

                    # Detectar baja variación para ajustar estacionalidad
                    seasonal_component = "add" if resumen_full["Cantidad"].std() >= 2 else None

                    if len(resumen_full) >= 24:
                        try:
                            modelo = ExponentialSmoothing(
                                resumen_full["Cantidad"],
                                trend="add",
                                seasonal=seasonal_component,
                                seasonal_periods=12 if seasonal_component else None
                            )
                            ajuste = modelo.fit()
                            proyeccion = ajuste.forecast(6)

                            df_proyeccion = proyeccion.reset_index()
                            df_proyeccion.columns = ["Mes", "Proyección"]

                            fig_forecast = px.line(
                                resumen_full.reset_index(),
                                x="index", y="Cantidad", markers=True,  # Cambiado a 'index'
                                title=f"Proyección Holt-Winters - Estado: {estado_seleccionado}",
                                labels={"index": "Mes", "Cantidad": "Número de Casos"}
                            )
                            fig_forecast.add_scatter(
                                x=df_proyeccion["Mes"], y=df_proyeccion["Proyección"],
                                mode="lines+markers", name="Proyección",
                                line=dict(dash="dot", color="red")
                            )

                            st.plotly_chart(fig_forecast, use_container_width=True)
                            st.subheader("📅 Tabla de Proyección")
                            df_proyeccion["Mes"] = pd.to_datetime(df_proyeccion["Mes"]).dt.strftime("%Y-%m")
                            st.dataframe(df_proyeccion)

                        except Exception as e:
                            st.warning(f"No se pudo generar la proyección: {e}")
                    else:
                        st.warning("No hay suficientes datos mensuales para generar una proyección confiable (mínimo 24 meses).")