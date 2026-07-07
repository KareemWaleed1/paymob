import socket

from django.conf import settings

from .protocol import BankProtocolError, decode_message, encode_message
from .services import simulate_authorization


class BankClientError(Exception):
    pass


def authorize_payment(transaction):
    if settings.BANK_TRANSPORT == "tcp":
        return authorize_payment_via_tcp(transaction)

    return simulate_authorization()


def authorize_payment_via_tcp(transaction):
    payload = {
        "transaction_id": transaction.id,
        "merchant_id": transaction.merchant_id,
        "terminal_id": transaction.terminal_id,
        "amount": str(transaction.amount),
        "currency": transaction.order.currency,
    }

    try:
        with socket.create_connection(
            (settings.BANK_TCP_HOST, settings.BANK_TCP_PORT),
            timeout=settings.BANK_TCP_TIMEOUT_SECONDS,
        ) as sock:
            file = sock.makefile("rwb")
            file.write(encode_message(payload).encode("utf-8"))
            file.flush()

            response_line = file.readline()
            if not response_line:
                raise BankClientError("Bank TCP server closed the connection.")

            response = decode_message(response_line.decode("utf-8"))
    except socket.timeout as exc:
        raise BankClientError("Bank TCP request timed out.") from exc
    except OSError as exc:
        raise BankClientError("Could not connect to bank TCP server.") from exc
    except (BankProtocolError, UnicodeDecodeError) as exc:
        raise BankClientError("Bank TCP server returned an invalid message.") from exc

    if response.get("ok") != "true":
        raise BankClientError(response.get("error", "Bank TCP request failed."))

    return {
        "bank_response": response["bank_response"],
        "bank_reference": response["bank_reference"],
    }
