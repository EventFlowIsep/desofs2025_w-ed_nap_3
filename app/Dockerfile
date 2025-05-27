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
EXPOSE 8000

# Comand for starting uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
