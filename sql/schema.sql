--Merchants Table
CREATE TABLE Merchants (
merchant_id VARCHAR(20) PRIMARY KEY,
name VARCHAR(100) NOT NULL,
country CHAR(2) NOT NULL);

--Payers Table
CREATE TABLE Payers (
account_id VARCHAR(20) PRIMARY KEY,
pan_last4 CHAR(4) NOT NULL,
ip_address VARCHAR(15),
device_id VARCHAR(20));

-- Transactions Table
CREATE TABLE Transactions (
transaction_id VARCHAR(20) PRIMARY KEY,
timestamp DATETIME NOT NULL,
channel VARCHAR(50),
amount DECIMAL(18,2) NOT NULL,
currency CHAR(3) NOT NULL,
merchant_id VARCHAR(20) NOT NULL,
account_id VARCHAR(20) NOT NULL,
FOREIGN KEY (merchant_id) REFERENCES Merchants(merchant_id),
FOREIGN KEY (account_id) REFERENCES Payers(account_id)
 );

CREATE INDEX idx_transaction_timestamp ON Transactions(timestamp);
CREATE INDEX idx_transaction_merchant ON Transactions(merchant_id);