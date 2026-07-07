from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .protocol import BankProtocolError, decode_message, encode_message
from .tcp import handle_bank_message


class BankProtocolTests(SimpleTestCase):
    def test_encode_message_uses_query_parameter_format(self):
        message = encode_message(
            {
                "transaction_id": 1,
                "amount": "500.00",
                "currency": "EGP",
            }
        )

        self.assertEqual(
            message,
            "transaction_id=1&amount=500.00&currency=EGP\n",
        )

    def test_decode_message_returns_parameters(self):
        data = decode_message("bank_response=APPROVED&bank_reference=BANK-TEST\n")

        self.assertEqual(data["bank_response"], "APPROVED")
        self.assertEqual(data["bank_reference"], "BANK-TEST")

    def test_decode_message_rejects_empty_messages(self):
        with self.assertRaises(BankProtocolError):
            decode_message("\n")


class BankTcpHandlerTests(SimpleTestCase):
    @patch("bank.tcp.simulate_authorization")
    def test_handle_bank_message_returns_authorization_as_query_parameters(
        self,
        mocked_authorization,
    ):
        mocked_authorization.return_value = {
            "bank_response": "APPROVED",
            "bank_reference": "BANK-TEST",
        }

        response = handle_bank_message(
            "transaction_id=1&merchant_id=1&terminal_id=1&amount=500.00&currency=EGP\n"
        )

        self.assertEqual(
            response,
            "ok=true&bank_response=APPROVED&bank_reference=BANK-TEST\n",
        )

    def test_handle_bank_message_returns_error_for_invalid_request(self):
        response = handle_bank_message(
            "transaction_id=1&merchant_id=1&terminal_id=1&amount=-10.00&currency=EGP\n"
        )

        self.assertEqual(response, "ok=false&error=invalid_request\n")


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
