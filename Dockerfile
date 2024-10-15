# Use a lightweight Python image
FROM python:3.9-slim

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the app code
COPY . /app

# Set the working directory
WORKDIR /app

# Command to run the app
CMD ["streamlit", "run", "app.py"]