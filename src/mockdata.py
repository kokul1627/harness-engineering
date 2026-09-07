"""
Mock Data for Retail Banking Agent.
Contains demo accounts, beneficiaries, and transaction history in Indian Rupees (₹).
"""

DEFAULT_USER_ACCOUNT = "ACC1001"
DEFAULT_DAILY_LIMIT = 50000.00

# Demo Customer Accounts
ACCOUNTS = {
    "ACC1001": {
        "account_id": "ACC1001",
        "owner_name": "Priya Sharma",
        "balance": 75000.00,
        "daily_limit": 50000.00,
        "currency": "INR",
        "currency_symbol": "₹",
        "bank_name": "HDFC Bank",
        "ifsc_code": "HDFC0001234",
        "status": "ACTIVE",
    },
    "ACC1002": {
        "account_id": "ACC1002",
        "owner_name": "Kavita Nair",
        "balance": 18500.50,
        "daily_limit": 50000.00,
        "currency": "INR",
        "currency_symbol": "₹",
        "bank_name": "HDFC Bank",
        "ifsc_code": "HDFC0001234",
        "status": "ACTIVE",
    },
    "ACC2001": {
        "account_id": "ACC2001",
        "owner_name": "Rahul Verma",
        "balance": 42000.00,
        "daily_limit": 50000.00,
        "currency": "INR",
        "currency_symbol": "₹",
        "bank_name": "ICICI Bank",
        "ifsc_code": "ICIC0004321",
        "status": "ACTIVE",
    },
    "ACC2002": {
        "account_id": "ACC2002",
        "owner_name": "Sneha Rao",
        "balance": 15000.00,
        "daily_limit": 50000.00,
        "currency": "INR",
        "currency_symbol": "₹",
        "bank_name": "State Bank of India",
        "ifsc_code": "SBIN0008765",
        "status": "ACTIVE",
    },
    "ACC2003": {
        "account_id": "ACC2003",
        "owner_name": "Amit Patel",
        "balance": 63000.00,
        "daily_limit": 50000.00,
        "currency": "INR",
        "currency_symbol": "₹",
        "bank_name": "Axis Bank",
        "ifsc_code": "UTIB0001122",
        "status": "ACTIVE",
    },
    "ACC2004": {
        "account_id": "ACC2004",
        "owner_name": "Rahul Sharma",
        "balance": 28000.00,
        "daily_limit": 50000.00,
        "currency": "INR",
        "currency_symbol": "₹",
        "bank_name": "HDFC Bank",
        "ifsc_code": "HDFC0005678",
        "status": "ACTIVE",
    },
    "ACC9001": {
        "account_id": "ACC9001",
        "owner_name": "Priya Sharma (Dormant)",
        "balance": 10000.00,
        "daily_limit": 50000.00,
        "currency": "INR",
        "currency_symbol": "₹",
        "bank_name": "HDFC Bank",
        "ifsc_code": "HDFC0001234",
        "status": "FROZEN",
    },
}

# Registered Beneficiaries for Accounts
# Notice ACC1001 has two beneficiaries with the name / nickname 'Rahul' to test ambiguous matching!
BENEFICIARIES = {
    "ACC1001": [
        {
            "beneficiary_id": "BENEF001",
            "name": "Rahul Verma",
            "nickname": "Rahul",
            "account_id": "ACC2001",
            "bank_name": "ICICI Bank",
            "ifsc_code": "ICIC0004321",
        },
        {
            "beneficiary_id": "BENEF002",
            "name": "Sneha Rao",
            "nickname": "Sneha",
            "account_id": "ACC2002",
            "bank_name": "State Bank of India",
            "ifsc_code": "SBIN0008765",
        },
        {
            "beneficiary_id": "BENEF003",
            "name": "Amit Patel",
            "nickname": "Amit",
            "account_id": "ACC2003",
            "bank_name": "Axis Bank",
            "ifsc_code": "UTIB0001122",
        },
        {
            "beneficiary_id": "BENEF004",
            "name": "Rahul Sharma",
            "nickname": "Rahul",
            "account_id": "ACC2004",
            "bank_name": "HDFC Bank",
            "ifsc_code": "HDFC0005678",
        },
    ]
}

# Past Transaction History
TRANSACTIONS = {
    "TXN1001": {
        "transaction_id": "TXN1001",
        "source_account_id": "ACC1001",
        "destination_account_id": "ACC2001",
        "recipient_name": "Rahul Verma",
        "amount": 2500.00,
        "currency": "INR",
        "status": "COMPLETED",
        "remarks": "Dinner split",
        "timestamp": "2026-09-05 20:15:00",
    },
    "TXN1002": {
        "transaction_id": "TXN1002",
        "source_account_id": "ACC1001",
        "destination_account_id": "ACC2002",
        "recipient_name": "Sneha Rao",
        "amount": 1200.00,
        "currency": "INR",
        "status": "COMPLETED",
        "remarks": "Electricity bill",
        "timestamp": "2026-09-06 11:30:00",
    },
    "TXN1003": {
        "transaction_id": "TXN1003",
        "source_account_id": "ACC1001",
        "destination_account_id": "ACC2003",
        "recipient_name": "Amit Patel",
        "amount": 15000.00,
        "currency": "INR",
        "status": "PENDING",
        "remarks": "Apartment rent share",
        "timestamp": "2026-09-07 06:45:00",
    },
}
