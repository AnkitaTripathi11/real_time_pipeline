## Real Time Data Persistence and API Development
### 🎯 Objective
Design and implement a robust **real-time data persistence pipeline** using:
- **Kafka** → for data ingestion  
- **Azure SQL database (MSSQL)** → for data storage  
- **Python microservices (FastAPI)** → for API development and data retrieval

**Architecture Summary:** Kafka → Consumer (validation) → Azure SQL → FastAPI API → Client
____________________________________________________________________________________________________________________________________________________________________________________________________________
### 🧰 Technologies Used
- 🐍 **Python 3.10+**
- ☁️ **Confluent Kafka Cloud**
- 🗄️ **Azure SQL Database (MSSQL)**
- ⚡ **FastAPI**
- 🐳 **Docker**
- ☸️ **Kubernetes**
____________________________________________________________________________________________________________________________________________________________________________________________________________
### 📂 Folder Structure
```
real_time_pipeline/
├── sql/
│ └── schema.sql
│
├── kafka_consumer/
│ ├── consumer.py
│ ├── producer_test.py
│ ├── Dockerfile
│
├── fastapi_api/
│ ├── main.py
│ ├── Dockerfile
│
├── k8s/
│ ├── kafka_consumer_deployment.yaml
│ ├── fastapi_api_deployment.yaml
│ ├── services.yaml
│
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```
____________________________________________________________________________________________________________________________________________________________________________________________________________
### 🧩 Task 1: Designing the Database (Azure SQL)
The relational schema is designed from the incoming transaction JSON and follows normalization.
**Tables:**
1.	Transactions
2.	Merchants
3.	Payers
- Each transaction references a merchant and payer using foreign keys.

**Schema file:**
-	sql/schema.sql – contains table creation and indexing scripts.
Features:
-	Normalized relational model with primary/foreign keys
-	Indexed for optimized lookups by ```transaction_id```, ```timestamp```, and ```merchant_id```
____________________________________________________________________________________________________________________________________________________________________________________________________________
### 🧩 Task 2: Building the Real-Time Kafka Pipeline
**Components**

**1. Kafka Producer (```producer_test.py```)**
- Generates and sends both valid and invalid transaction messages concurrently.
- Publishes valid and invalid JSON messages to Kafka topic ```transactions```.

**2. Kafka Consumer (```consumer.py```)**
- Consumes JSON messages from the ```transactions``` topic.
- Validates each message using **Pydantic schema models**.
- Persists valid records into **Azure SQL**.
- Sends invalid records to a dedicated Kafka error topic ```transactions_error```.

Both scripts are containerized and can run independently.
**Flow**
```
Producer → Kafka Topic → Consumer → Azure SQL
                       ↳ Invalid → Error Topic
```
____________________________________________________________________________________________________________________________________________________________________________________________________________
### 🧩 Task 3: Building the FastAPI Layer
To make the stored data accessible, a lightweight **FastAPI** service provides two REST APIs:

**1. Fetch Transaction Details**
```
GET /transactions/{transaction_id}
```
- Returns transaction details including merchant and payer info.

**2. Top Merchants by Transaction Volume**
```
GET /merchants/top?start_date=<YYYY-MM-DD>&end_date=<YYYY-MM-DD>
```
- Returns top 5 merchants ranked by total transaction amount within a date range.
- Each endpoint connects directly to the Azure SQL database using **pyodbc**.
____________________________________________________________________________________________________________________________________________________________________________________________________________
### Environment Configuration
All credentials are managed via ```.env``` file (excluded from repo for security).
An example template is provided in : ```.env.example```:

| Variable | Description |
|-----------|-------------|
| `KAFKA_BOOTSTRAP` | Kafka broker connection string |
| `KAFKA_USERNAME` | Kafka confluent api key |
| `KAFKA_PASSWORD` | Kafka confluent api secret |
| `SQL_SERVER` | Azure SQL server name |
| `SQL_DB` | Database name |
| `SQL_USER` | Database username |
| `SQL_PASSWORD` | Database password |

- None of these values are hardcoded or committed to GitHub.
____________________________________________________________________________________________________________________________________________________________________________________________________________
### 🧪 Testing & Validation
#### Kafka Producer Test :
Run producer_test.py to generate valid and invalid transaction messages:
```
python kafka_consumer/producer_test.py
```
-	Valid messages → Sent to Kafka topic ````transactions```
-	Invalid messages → Missing critical fields (eg. transaction_id), used to test validation logic
#### Kafka Consumer Test :
Run consumer.py to process incoming Kafka messages and persist them in Azure SQL:
```
python kafka_consumer/consumer.py
```
-	Valid messages → Validated via Pydantic models and stored in Azure SQL tables 
-	Invalid messages → Captured and re-published to Kafka topic ```transactions_error```
#### API Testing :
**Start the FastAPI Server**
```
cd fastapi_api
uvicorn main:app --reload
```
Access the interactive docs at :
```http://127.0.0.1:8000/docs```
**Get Transaction details:**
```GET /transactions/TX-10001```
- Returns transaction info along with merchant and payer details

**Top 5 Merchants by transaction amount:**
```GET /merchants/top?start_date=2025-08-20&end_date=2025-08-25```
- Returns the top 5 merchants ranked by total transaction volume within the specified date range
#### Azure SQL Verification:
Checked via Azure Query Editor (Preview) verified records insertion in:
- Transaction
- Merchants
- Payers
____________________________________________________________________________________________________________________________________________________________________________________________________________
### ☸️ Containerization and Deployment
These manifests define the deployment and service configuration for both Kafka Consumer and FastAPI API pods on AKS.
**Resources :**
- **kafka_consumer_deployment.yaml** → Kafka consumer pod
- **fastapi_api_deployment.yaml** → FastAPI API pod
- **services.yaml** → Defines cluster-accessible endpoints

**Deployment steps**
1. Build Docker Images
```
docker build -t <your_docker_repo>/kafka_consumer:latest ./kafka_consumer
docker build -t <your_docker_repo>/fastapi_api:latest ./fastapi_api
```
2. Push to container registry
```
docker push <your_docker_repo>/kafka_consumer:latest
docker push <your_docker_repo>/fastapi_api:latest
```
3. Create Kubernetes secrets for credentials.
```
kubectl create secret generic mssql-secrets \
  --from-literal=server=<SQL_SERVER> \
  --from-literal=db=<SQL_DB> \
  --from-literal=user=<SQL_USER> \
  --from-literal=password=<SQL_PASSWORD>

kubectl create secret generic kafka-secrets \
  --from-literal=bootstrap=<KAFKA_BOOTSTRAP>
```
4. Deploy all resources
```
kubectl apply -f k8s/kafka_consumer_deployment.yaml
kubectl apply -f k8s/fastapi_api_deployment.yaml
kubectl apply -f k8s/services.yaml
```
____________________________________________________________________________________________________________________________________________________________________________________________________________
#### Author : 
Name: Ankita Tripathi

Email: ankitatripathivns@gmail.com

Date: January 2026

