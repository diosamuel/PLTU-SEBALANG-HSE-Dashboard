FROM python:3.7-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Upgrade pip and build tools
RUN pip install --default-timeout=1000 --no-cache-dir --upgrade pip setuptools wheel --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Install Python dependencies
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Copy the rest of the application
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "Homepage.py", "--server.port=8501", "--server.address=0.0.0.0"]
