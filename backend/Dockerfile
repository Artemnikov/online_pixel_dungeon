FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set python path to allow imports from backend.app
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "app/main.py"]
