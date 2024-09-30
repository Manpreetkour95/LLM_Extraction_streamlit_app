# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory.
WORKDIR /app

# Copy requirements.txt and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code.
COPY . .

# Expose port 8501.
EXPOSE 8501

# Run the application.
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
