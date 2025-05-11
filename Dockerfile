# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip install uv && uv --version

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install dependencies with uv
RUN uv sync --frozen

# Expose the application port
EXPOSE 8000

# Start the application with Uvicorn
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]