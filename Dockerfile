# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies first for caching
COPY requirements.txt /app/

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . /app

# Expose port Cloud Run expects
EXPOSE 8080

# Default command
CMD ["bash", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8080} --server.headless true"]

