import socket
import threading

from .protocol import BankProtocolError, decode_message, encode_message
from .serializers import BankAuthorizeRequestSerializer, BankAuthorizeResponseSerializer
from .services import simulate_authorization


def handle_bank_message(message):
    request_data = decode_message(message)
    request_serializer = BankAuthorizeRequestSerializer(data=request_data)

    if not request_serializer.is_valid():
        return encode_message(
            {
                "ok": "false",
                "error": "invalid_request",
            }
        )

    bank_result = simulate_authorization()
    response_serializer = BankAuthorizeResponseSerializer(bank_result)
    return encode_message(
        {
            "ok": "true",
            **response_serializer.data,
        }
    )


def handle_connection(connection):
    with connection:
        file = connection.makefile("rwb")
        line = file.readline()
        if not line:
            return

        try:
            response = handle_bank_message(line.decode("utf-8"))
        except (BankProtocolError, UnicodeDecodeError):
            response = encode_message(
                {
                    "ok": "false",
                    "error": "invalid_message",
                }
            )

        file.write(response.encode("utf-8"))
        file.flush()


def serve(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()

        while True:
            connection, _address = server.accept()
            thread = threading.Thread(
                target=handle_connection,
                args=(connection,),
                daemon=True,
            )
            thread.start()
