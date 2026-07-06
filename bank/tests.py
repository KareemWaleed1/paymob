from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase


class BankAuthorizeEndpointTests(APITestCase):
    @patch("bank.views.simulate_authorization")
    def test_bank_authorize_returns_bank_response(self, mocked_authorization):
        mocked_authorization.return_value = {
            "bank_response": "APPROVED",
            "bank_reference": "BANK-TEST",
        }

        response = self.client.post(
            "/bank/authorize/",
            {
                "transaction_id": 1,
                "merchant_id": 1,
                "terminal_id": 1,
                "amount": "500.00",
                "currency": "EGP",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bank_response"], "APPROVED")
        self.assertEqual(response.data["bank_reference"], "BANK-TEST")

    def test_bank_authorize_validates_request_body(self):
        response = self.client.post(
            "/bank/authorize/",
            {
                "transaction_id": 1,
                "merchant_id": 1,
                "terminal_id": 1,
                "amount": "-10.00",
                "currency": "EGP",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
