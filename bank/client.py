from .services import simulate_authorization


class BankClientError(Exception):
    pass


def authorize_payment(transaction):
    return simulate_authorization()
