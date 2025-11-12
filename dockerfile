# Usa una imagen base con Python 3.10
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de dependencias
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Comando para iniciar la app en Render
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]