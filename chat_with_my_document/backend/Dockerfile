# Use an official Python runtime as a parent image
FROM python:3.12

WORKDIR /app
#COPY . /app
# Copy requirements.txt and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code.
COPY . .

# Expose port 5000.
EXPOSE 5000

# Set the environment variable for Flask.
ENV FLASK_APP=app.py

# Run the application.
CMD ["python", "app.py"]
