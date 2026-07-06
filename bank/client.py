import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .services import simulate_authorization


class BankClientError(Exception):
    pass


def authorize_payment(transaction):
    payload = {
        "transaction_id": transaction.id,
        "merchant_id": transaction.merchant_id,
        "terminal_id": transaction.terminal_id,
        "amount": str(transaction.amount),
        "currency": transaction.order.currency,
    }

    if settings.BANK_API_BASE_URL:
        return authorize_payment_via_http(payload)

    return simulate_authorization()


def authorize_payment_via_http(payload):
    url = settings.BANK_API_BASE_URL.rstrip("/") + "/bank/authorize/"
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.BANK_API_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise BankClientError(f"Bank API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        raise BankClientError("Could not connect to bank API.") from exc
