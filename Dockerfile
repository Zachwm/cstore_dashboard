# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your app code and requirements
COPY requirements.txt /app/
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose the port Cloud Run expects
EXPOSE 8080

# Use the PORT environment variable
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.enableCORS=false"]

