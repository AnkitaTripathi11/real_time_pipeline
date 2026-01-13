FROM python:3.10
WORKDIR /app
#Copy shared requirements file from root and install dependencies
COPY ../requirements.txt .
RUN pip install -r requirements.txt
#Copy FastAPI app files into container
COPY . .
#Expose FastAPI port
EXPOSE 8000
#run FastAPI using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]