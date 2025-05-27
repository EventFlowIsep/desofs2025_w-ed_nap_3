# Oficial Python image as a base
FROM python:3.10-slim

# Define the Directory of the application
WORKDIR /app

# Copy dependencies file
COPY ../requirements.txt .

# Install system dependencies for Streamlit
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port for Streamlit
EXPOSE 8501

# Comand for starting the Streamlit application
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.enableCORS=false"]
