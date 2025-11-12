# Usa una imagen base con Python 3.10
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de dependencias
RUN apt-get update && apt-get install -y build-essential

# Instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir cmdstanpy
RUN python -m cmdstanpy.install_cmdstan


# Copia el resto del proyecto
COPY . .

# Comando para iniciar la app en Render
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]