FROM python:3.11-slim

WORKDIR /app

# Hugging Face Spaces expects the container to expose and listen on port 7860
EXPOSE 7860

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Run Streamlit on port 7860
ENTRYPOINT ["streamlit", "run", "dashboard/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
