# Use a slim version of Python 3.11/3.12
FROM python:3.11-slim

# Set environment variables for better Python performance in Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for PDF processing (Poppler/Tesseract)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure
# This includes app.py, core/, config/, and rag_source/
COPY . .

# Streamlit uses port 8501 by default
EXPOSE 8501

# The command now points to app.py
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]