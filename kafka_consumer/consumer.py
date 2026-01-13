import os, json, logging, pyodbc
from confluent_kafka import Consumer, Producer
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Environment variables
load_dotenv()
KAFKA_BOOTSTRAP=os.getenv("KAFKA_BOOTSTRAP")
KAFKA_USERNAME=os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD=os.getenv("KAFKA_PASSWORD")

SQL_SERVER=os.getenv("SQL_SERVER")
SQL_DB=os.getenv("SQL_DB")
SQL_USER=os.getenv("SQL_USER")
SQL_PASSWORD=os.getenv("SQL_PASSWORD")

# Connect to Azure SQL
try:
    conn=pyodbc.connect(
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={SQL_SERVER};Database={SQL_DB};UID={SQL_USER};PWD={SQL_PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    cursor=conn.cursor()
    logging.info("Connected to Azure SQL Database.")
except Exception as e:
    logging.error(f"Database connection failed: {e}")
    raise

# Kafka configuration
consumer_config={
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": KAFKA_USERNAME,
    "sasl.password": KAFKA_PASSWORD,
    "group.id": "transactions_group",
    "auto.offset.reset": "earliest"
}
consumer=Consumer(consumer_config)
consumer.subscribe(["transactions"])

producer=Producer({
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": KAFKA_USERNAME,
    "sasl.password": KAFKA_PASSWORD
})
error_topic="transactions_error"

# Schema Models (Pydantic)
class Merchant(BaseModel):
    id: str
    name: str
    country: str

class Payer(BaseModel):
    account_id: str
    pan_last4: str
    ip_address: str
    device_id: str

class Transaction(BaseModel):
    transaction_id: str
    timestamp: str
    channel: str
    amount: float
    currency: str
    merchant: Merchant
    payer: Payer

# Save to SQL
def persist_transaction(tx: Transaction):
    try:
        # Convert timestamp to SQL-compatible format (YYYY-MM-DD HH:MM:SS)
        try:
            formatted_ts = datetime.fromisoformat(tx.timestamp.replace("Z", "")).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            formatted_ts = tx.timestamp.replace("T", " ").replace("Z", "")

        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Merchants WHERE merchant_id=?)
            INSERT INTO Merchants (merchant_id, name, country) VALUES (?, ?, ?)
        """, tx.merchant.id, tx.merchant.id, tx.merchant.name, tx.merchant.country)

        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Payers WHERE account_id=?)
            INSERT INTO Payers (account_id, pan_last4, ip_address, device_id)
            VALUES (?, ?, ?, ?)
        """, tx.payer.account_id, tx.payer.account_id, tx.payer.pan_last4, tx.payer.ip_address, tx.payer.device_id)

        cursor.execute("""
            INSERT INTO Transactions (transaction_id, timestamp, channel, amount, currency, merchant_id, account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tx.transaction_id, formatted_ts, tx.channel, tx.amount, tx.currency, tx.merchant.id, tx.payer.account_id)

        conn.commit()
        logging.info(f"Transaction {tx.transaction_id} persisted successfully.")
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to persist {tx.transaction_id}: {e}")

# Consume and Process
try:
    while True:
        msg=consumer.poll(1.0)
        if msg is None:
            continue
        try:
            data=json.loads(msg.value())
            tx=Transaction(**data)
            persist_transaction(tx)
        except (json.JSONDecodeError, ValidationError) as e:
            logging.warning(f"Invalid message: {e}")
            producer.produce(error_topic, msg.value())
            producer.flush()
except KeyboardInterrupt:
    logging.info("Consumer stopped manually.")
finally:
    consumer.close()
    cursor.close()
    conn.close()
