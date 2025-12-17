FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["streamlit", "run", "--server.address=0.0.0.0", "--server.port=8080", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "app.py"]
