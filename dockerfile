FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    liblapack-dev \
    libblas-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]