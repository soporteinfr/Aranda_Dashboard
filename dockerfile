# Imagen base con Python 3.10
FROM python:3.10-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema necesarias para pandas, plotly, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la app
WORKDIR /app

# Copiar archivos de la app
COPY . /app

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto para Streamlit
EXPOSE 8501

# Comando para ejecutar la app en Render
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]