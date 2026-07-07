# Paymob-like Payment Gateway

A simplified Django REST Framework backend that accepts merchant payment requests at `POST /pay`, creates an order and transaction, simulates a bank response, and updates both records atomically.

Project layout:

```text
manage.py
paymob/              # Django project settings and root URLs
payment_gateaway/    # Payment gateway app
bank/                # Fake bank app
```

The bank app exposes:

```text
POST /bank/authorize/
```

The payment gateway calls `bank.client.authorize_payment()`, which uses the local bank simulator directly.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

By default, local development uses SQLite at `db.sqlite3`.

To use MySQL later, set `DB_ENGINE=mysql` in `.env` and create a MySQL database that matches the same file:

```sql
CREATE DATABASE payment_gateway CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run migrations and start the server:

```bash
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

The seed command creates these demo accounts:

```text
admin / admin123
merchant_one / merchant123
merchant_two / merchant123
```

## Authentication

Obtain JWT tokens:

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"merchant_user","password":"password"}'
```

Call `/pay` with the access token:

```bash
curl -X POST http://127.0.0.1:8000/pay \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"terminal_id":1,"amount":"500.00","currency":"EGP"}'
```

You can also call the fake bank API directly:

```bash
curl -X POST http://127.0.0.1:8000/bank/authorize/ \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":1,"merchant_id":1,"terminal_id":1,"amount":"500.00","currency":"EGP"}'
```

## Admin Setup

Use Django admin to create:

1. A `User`
2. A `Merchant` linked to that user
3. One or more active `Terminal` records for the merchant

## Tests

```bash
python manage.py test
```
