# Use the official Python 3.9 image to match our venv
FROM python:3.9-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the local code and assets to the container
COPY . ./

# Expose port 8080 as expected by Cloud Run
EXPOSE 8080

# Command to run the Streamlit app
CMD sh -c "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0"
