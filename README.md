# 📊 Dashboard Aranda - Gestión de Datos y Visualización

Un dashboard interactivo para el análisis y visualización de datos de gestión de casos de soporte técnico de Aranda.

## 🚀 Características

- **📈 Visualizaciones Interactivas**: Gráficos de distribución, tendencias y análisis estadísticos
- **📊 Múltiples Vistas**: Dashboard con Streamlit (rama main) y Dash (rama develop)
- **📁 Carga de Archivos**: Soporte para archivos Excel (.xlsx) con validación automática
- **🔍 Filtros Avanzados**: Filtrado por grupos de especialistas y períodos de tiempo
- **📱 Diseño Responsivo**: Interfaz adaptable a diferentes dispositivos
- **🎨 Temas Personalizables**: Tema claro (Streamlit) y tema dark (Dash)

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.8+**
- **Pandas**: Manipulación y análisis de datos
- **NumPy**: Computación numérica
- **Plotly**: Visualizaciones interactivas
- **OpenPyXL**: Lectura de archivos Excel

### Frontend
- **Streamlit** (rama main): Framework de aplicaciones web
- **Dash** (rama develop): Framework de dashboards interactivos
- **Bootstrap**: Estilos y componentes UI

### Analytics
- **Prophet**: Forecasting y predicciones
- **Statsmodels**: Análisis estadístico
- **Scikit-learn**: Machine Learning

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- 8GB RAM mínimo (recomendado 16GB)
- 2GB espacio libre en disco

## ⚙️ Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/soporteinfr/DashboardAranda.git
cd DashboardAranda
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Streamlit Version (Rama Main)
```bash
git checkout main
streamlit run Aranda_Dashboard/app.py
```
Accede a: http://localhost:8501

### Dash Version (Rama Develop)
```bash
git checkout develop
python Aranda_Dashboard/dash_app.py
```
Accede a: http://127.0.0.1:8050

## 📊 Estructura del Proyecto

```
DashboardAranda/
├── Aranda_Dashboard/
│   ├── app.py              # Aplicación Streamlit (main)
│   ├── dash_app.py         # Aplicación Dash (develop)
│   ├── assets/             # Recursos estáticos
│   │   ├── imagen.png      # Fondo de aplicación
│   │   ├── Imagen1.png     # Favicon
│   │   └── custom.css      # Estilos personalizados
│   ├── data/              # Datos procesados
│   └── data_filtered/     # Datos filtrados
├── requirements.txt       # Dependencias
├── README.md             # Documentación
├── .gitignore           # Archivos ignorados
└── README_TROUBLESHOOTING.md  # Solución de problemas
```

## 📝 Formato de Datos

El archivo Excel debe contener las siguientes columnas:

| Columna | Descripción | Tipo |
|---------|-------------|------|
| `Numero de caso` | ID único del caso | String |
| `Fecha de registro` | Fecha de creación | Date |
| `Especialista` | Nombre del analista | String |
| `Grupo de especialista` | Equipo/departamento | String |
| `Estado` | Estado actual del caso | String |
| `Asunto` | Título del caso | String |
| `Descripcion` | Detalle del problema | String |
| `Primer Nivel` | Categoría principal | String |
| `Segundo Nivel` | Subcategoría | String |
| `Fecha de en proceso` | Fecha de inicio trabajo | Date |
| `Fecha de Pendiente 1` | Fecha de pausa | Date |
| `Fecha de Cerrado` | Fecha de resolución | Date |

## 📈 Visualizaciones Disponibles

### 1. Distribución de Casos
- **Casos Cerrados por Analista**: Gráfico de dona con distribución
- **Casos Pendientes por Analista**: Análisis de carga de trabajo
- **Top Aplicaciones**: Ranking de aplicaciones con más casos

### 2. Análisis Temporal
- **Timeline de Casos**: Evolución temporal de casos registrados
- **Tendencias Mensuales**: Patrones estacionales
- **Predicciones**: Forecasting con Prophet

### 3. Métricas de Rendimiento
- **Tiempo de Resolución**: Análisis estadístico de tiempos
- **Productividad por Analista**: Métricas de eficiencia
- **Distribución por Estados**: Análisis del flujo de trabajo

## 🎨 Personalización

### Cambiar Tema
```python
# En app.py para Streamlit
st.set_page_config(
    page_title="Dashboard Aranda",
    page_icon="assets/Imagen1.png",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### Agregar Nuevas Visualizaciones
```python
# Ejemplo de nueva gráfica
def nueva_visualizacion(df):
    fig = px.scatter(df, x='columna_x', y='columna_y')
    return fig
```

## 🐛 Solución de Problemas

### Error de Carga de Archivos
```bash
# Verificar formato del archivo
pandas.read_excel("tu_archivo.xlsx")
```

### Problemas de Memoria
```python
# Optimizar tipos de datos
df = df.astype({
    'columna_string': 'category',
    'columna_numerica': 'int32'
})
```

Consulta [README_TROUBLESHOOTING.md](README_TROUBLESHOOTING.md) para más detalles.

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📜 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Equipo

- **Desarrollo**: Equipo de Soporte Infraestructura
- **Análisis de Datos**: Especialistas Aranda
- **Diseño UI/UX**: Equipo de Desarrollo

## 📞 Soporte

Para soporte técnico, contacta:
- **Email**: soporte@aranda.com
- **GitHub Issues**: [Crear Issue](https://github.com/soporteinfr/DashboardAranda/issues)

---

⭐ ¡No olvides dar una estrella al proyecto si te fue útil!