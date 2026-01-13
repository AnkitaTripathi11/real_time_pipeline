# Dockerfile for Kafka Consumer microservice
FROM python:3.10
WORKDIR /app
# Copy requirements file from root and install dependencies.
COPY ../requirements.txt .
RUN pip install -r requirements.txt
# Copy consumer scripts into the container
COPY . .
#start the Kafka consumer
CMD ["python", "consumer.py"]