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

The payment gateway calls `bank.client.authorize_payment()`. By default it uses the
local bank simulator directly, but it can also talk to a separate bank process over
normal TCP sockets.

## Bank TCP Socket Flow

This project supports a lower-level bank transport that sends plain character
streams over TCP. The data format is the same shape as URL query parameters:

```text
transaction_id=1&merchant_id=1&terminal_id=1&amount=500.00&currency=EGP
```

Each TCP message ends with a newline character. That final `\n` is important:
TCP is a stream of bytes, not a request/response protocol, so the newline is how
both sides know where one message ends.

The gateway sends:

```text
transaction_id=1&merchant_id=1&terminal_id=1&amount=500.00&currency=EGP\n
```

The bank TCP server responds:

```text
ok=true&bank_response=APPROVED&bank_reference=BANK-ABC123\n
```

To use TCP, start the bank socket server in one terminal:

```bash
python manage.py run_bank_tcp_server
```

Then set the gateway transport in `.env`:

```env
BANK_TRANSPORT=tcp
BANK_TCP_HOST=127.0.0.1
BANK_TCP_PORT=9000
BANK_TCP_TIMEOUT_SECONDS=5
```

Start Django in another terminal:

```bash
python manage.py runserver
```

The full flow is:

1. A merchant calls `POST /pay`.
2. Django creates the order and transaction.
3. `bank.client.authorize_payment()` converts the transaction fields into a query-parameter string.
4. The client opens a TCP connection to `BANK_TCP_HOST:BANK_TCP_PORT`.
5. The client sends the encoded string plus `\n`.
6. The bank TCP server reads until `\n`, parses the parameters, validates them, and runs the simulator.
7. The bank TCP server sends back another query-parameter string plus `\n`.
8. The payment gateway parses the response and stores `bank_response` and `bank_reference` on the transaction.

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
