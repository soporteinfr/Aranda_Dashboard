import streamlit as st
import pandas as pd
import os
import plotly.express as px
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import base64

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

                    fig = px.line(
                        resumen,
                        x="Año-Mes",
                        y="Cantidad",
                        markers=True,
                        title=f"Total de casos registrados por mes - Grupo: {grupo}",
                        labels={"Año-Mes": "Mes", "Cantidad": "Número de Casos"}
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

                    # Conteo de aplicaciones
                    aplicaciones = []
                    for _, row in df_grafico.iterrows():
                        segundo = str(row["Segundo Nivel"]).strip().lower()
                        primero = str(row["Primer Nivel"]).strip()
                        if segundo in ["solicitud", "falla"]:
                            app = primero
                        else:
                            app = row["Segundo Nivel"]
                        if isinstance(app, str):
                            app = app.strip()
                            if app.lower() not in ["otro", "otros", ""]:
                                aplicaciones.append(app)

                    if aplicaciones:
                        conteo_apps = pd.Series(aplicaciones).value_counts().reset_index()
                        conteo_apps.columns = ["Aplicación", "Cantidad"]
                        fig_apps = px.bar(
                            conteo_apps,
                            x="Cantidad",
                            y="Aplicación",
                            orientation="h",
                            title="Jerarquía más frecuente en los casos",
                            labels={"Cantidad": "Número de Casos", "Aplicación": "Aplicación"}
                        )
                        st.plotly_chart(fig_apps, use_container_width=True)
                    else:
                        st.info("No hay aplicaciones válidas para mostrar.")
                    
                    # Holt-Winters Forecasting
                    periodos = df_grupo["Año"].nunique()
                    if periodos >= 3:
                        resumen_full = df_grupo.groupby("Año-Mes")["Numero de caso"].count().reset_index(name="Cantidad")
                        resumen_full["Año-Mes"] = pd.to_datetime(resumen_full["Año-Mes"])
                        resumen_full = resumen_full.sort_values("Año-Mes")
                        resumen_full.set_index("Año-Mes", inplace=True)

                        try:

                            modelo = ExponentialSmoothing(
                                resumen_full["Cantidad"],
                                trend="add",
                                seasonal="add",
                                seasonal_periods=12
                            )
                            ajuste = modelo.fit()
                            proyeccion = ajuste.forecast(6)

                            df_proyeccion = proyeccion.reset_index()
                            df_proyeccion.columns = ["Mes", "Proyección"]

                            fig_forecast = px.line(
                                resumen_full.reset_index(),
                                x="Año-Mes",
                                y="Cantidad",
                                markers=True,
                                title=f"Proyección Holt-Winters - Grupo: {grupo}",
                                labels={"Año-Mes": "Mes", "Cantidad": "Número de Casos"}
                            )
                            fig_forecast.add_scatter(
                                x=df_proyeccion["Mes"],
                                y=df_proyeccion["Proyección"],
                                mode="lines+markers",
                                name="Proyección",
                                line=dict(dash="dot", color="red")
                            )
                            st.plotly_chart(fig_forecast, use_container_width=True)
                            st.subheader("📅 Tabla de Proyección")
                            df_proyeccion["Mes"] = pd.to_datetime(df_proyeccion["Mes"]).dt.strftime("%Y-%m")
                            st.dataframe(df_proyeccion)

                        except Exception as e:
                            st.warning(f"No se pudo generar la proyección: {e}")
                    else:
                        st.warning("Cantidad de periodos por debajo de los recomendados, no puede generarse una proyección estable.")