import os, json, time, random, threading, uuid, datetime
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()
KAFKA_BOOTSTRAP=os.getenv("KAFKA_BOOTSTRAP")
KAFKA_USERNAME=os.getenv("KAFKA_USERNAME")
KAFKA_PASSWORD=os.getenv("KAFKA_PASSWORD")

producer=Producer({
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": KAFKA_USERNAME,
    "sasl.password": KAFKA_PASSWORD
})

topic="transactions"

def generate_valid_transaction():
    return {
        "transaction_id": f"TX-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "channel": random.choice(["CARD_PRESENT", "CARD_NOT_PRESENT", "ONLINE"]),
        "amount": round(random.uniform(10, 5000), 2),
        "currency": "USD",
        "merchant": {
            "id": f"M-{random.randint(1000,9999)}",
            "name": f"Merchant-{random.randint(1,100)}",
            "country": random.choice(["US","CH","UK","IN"])
        },
        "payer": {
            "account_id": f"U-{random.randint(1000,9999)}",
            "pan_last4": f"{random.randint(1000,9999)}",
            "ip_address": f"192.168.{random.randint(0,255)}.{random.randint(0,255)}",
            "device_id": f"DEV-{random.randint(1000,9999)}"
        }
    }

def generate_invalid_transaction():
    t=generate_valid_transaction()
    t.pop("transaction_id", None)  # remove a critical field
    return t

def send_message(valid=True):
    msg=generate_valid_transaction() if valid else generate_invalid_transaction()
    producer.produce(topic, json.dumps(msg).encode("utf-8"))
    producer.flush()
    print(f"Sent {'valid' if valid else 'invalid'} message.")

def start_production():
    for _ in range(100):
        threading.Thread(target=send_message, args=(random.random() > 0.2,)).start()
        time.sleep(0.1)

if __name__ == "__main__":
    start_production()
