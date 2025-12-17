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

# Expose the port your app will run on
EXPOSE 8051

# Default command to run your app
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8051"]
