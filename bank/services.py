import uuid


class BankResponse:
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


def simulate_authorization():
    import random

    approved = random.choice([True, False])
    bank_response = BankResponse.APPROVED if approved else BankResponse.DECLINED

    return {
        "bank_response": bank_response,
        "bank_reference": f"BANK-{uuid.uuid4().hex[:12].upper()}",
    }
