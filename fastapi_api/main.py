from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import os, pyodbc
from dotenv import load_dotenv
from pydantic import BaseModel

#Load environment variables
load_dotenv()
SQL_SERVER   = os.getenv("SQL_SERVER")
SQL_DB       = os.getenv("SQL_DB")
SQL_USER     = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

#FastAPI app setup
app = FastAPI(
    title="Real-Time Transactions API",
    description="APIs to fetch transaction data and top merchants",
    version="1.0"
)

# Database connection function
def get_connection():
    try:
        conn = pyodbc.connect(
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server={SQL_SERVER};Database={SQL_DB};UID={SQL_USER};PWD={SQL_PASSWORD};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# Pydantic models (Response structures)
class Merchant(BaseModel):
    id: str
    name: str
    country: str

class Payer(BaseModel):
    account_id: str
    pan_last4: str
    ip_address: str
    device_id: str

class TransactionResponse(BaseModel):
    transaction_id: str
    timestamp: str
    channel: str
    amount: float
    currency: str
    merchant: Merchant
    payer: Payer

class TopMerchantResponse(BaseModel):
    merchant_id: str
    name: str
    country: str
    total_amount: float

# Endpoint 1: Get transaction by ID
@app.get("/transactions/{transaction_id}",response_model=TransactionResponse)
def get_transaction(transaction_id: str):
    try:
        print(f"Fetching transaction_id: {transaction_id}")
        conn=get_connection()
        cursor=conn.cursor()

        query= """
            SELECT 
                t.transaction_id, t.timestamp, t.channel, t.amount, t.currency,
                m.merchant_id, m.name, m.country,
                p.account_id, p.pan_last4, p.ip_address, p.device_id
            FROM Transactions t
            JOIN Merchants m ON t.merchant_id = m.merchant_id
            JOIN Payers p ON t.account_id = p.account_id
            WHERE t.transaction_id = ?
        """

        cursor.execute(query, transaction_id)
        row=cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")
        print("Query executed successfully") 

        response=TransactionResponse(
            transaction_id=row.transaction_id,
            timestamp=str(row.timestamp),
            channel=row.channel,
            amount=row.amount,
            currency=row.currency,
            merchant=Merchant(id=row.merchant_id, name=row.name, country=row.country),
            payer=Payer(
                account_id=row.account_id,
                pan_last4=row.pan_last4,
                ip_address=row.ip_address,
                device_id=row.device_id
            )
        )

        cursor.close()
        conn.close()
        return response
    except Exception as e:
        print(f"Error in get_transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 2: Get top merchants by total transaction volume
@app.get("/merchants/top", response_model=List[TopMerchantResponse])
def get_top_merchants(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format")
):
    conn = get_connection()
    cursor=conn.cursor()

    query = """
        SELECT TOP 5
            m.merchant_id, m.name, m.country,
            SUM(t.amount) AS total_amount
        FROM Transactions t
        JOIN Merchants m ON t.merchant_id = m.merchant_id
        WHERE CONVERT(date, t.timestamp) BETWEEN ? AND ?
        GROUP BY m.merchant_id, m.name, m.country
        ORDER BY total_amount DESC
    """

    cursor.execute(query, start_date, end_date)
    rows = cursor.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No transactions found in this range")

    results=[
        TopMerchantResponse(
            merchant_id=row.merchant_id,
            name=row.name,
            country=row.country,
            total_amount=row.total_amount
        )
        for row in rows
    ]

    cursor.close()
    conn.close()
    return results
