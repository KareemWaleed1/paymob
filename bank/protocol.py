from urllib.parse import parse_qsl, urlencode


MESSAGE_TERMINATOR = "\n"


class BankProtocolError(Exception):
    pass


def encode_message(values):
    return urlencode(values) + MESSAGE_TERMINATOR


def decode_message(message):
    message = message.strip()
    if not message:
        raise BankProtocolError("Empty bank message.")

    return dict(parse_qsl(message, keep_blank_values=True))
