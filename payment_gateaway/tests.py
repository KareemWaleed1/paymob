from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Merchant, Order, Terminal, Transaction


class PayEndpointTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="merchant_one",
            email="merchant1@example.com",
            password="password123",
        )
        self.other_user = user_model.objects.create_user(
            username="merchant_two",
            email="merchant2@example.com",
            password="password123",
        )
        self.merchant = Merchant.objects.create(
            name="Merchant One",
            email="merchant1@example.com",
            user=self.user,
        )
        self.other_merchant = Merchant.objects.create(
            name="Merchant Two",
            email="merchant2@example.com",
            user=self.other_user,
        )
        self.terminal = Terminal.objects.create(
            merchant=self.merchant,
            terminal_code="TERM-001",
            location="Cairo",
        )
        self.other_terminal = Terminal.objects.create(
            merchant=self.other_merchant,
            terminal_code="TERM-002",
            location="Alexandria",
        )

    def pay_payload(self, terminal_id=None):
        return {
            "terminal_id": terminal_id or self.terminal.id,
            "amount": "500.00",
            "currency": "EGP",
        }

    def test_unauthenticated_user_cannot_pay(self):
        response = self.client.post("/pay", self.pay_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_merchant_cannot_use_another_merchants_terminal(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/pay",
            self.pay_payload(terminal_id=self.other_terminal.id),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    @patch("payment_gateaway.views.authorize_payment")
    def test_successful_payment_updates_order_and_transaction(self, mocked_bank):
        mocked_bank.return_value = {
            "bank_response": "APPROVED",
            "bank_reference": "BANK-APPROVED",
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.post("/pay", self.pay_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "SUCCESS")
        self.assertEqual(response.data["bank_response"], "APPROVED")
        self.assertEqual(response.data["message"], "Payment approved")

        order = Order.objects.get()
        payment_transaction = Transaction.objects.get()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.amount, Decimal("500.00"))
        self.assertEqual(payment_transaction.status, Transaction.Status.SUCCESS)
        self.assertEqual(payment_transaction.bank_response, Transaction.BankResponse.APPROVED)
        self.assertEqual(payment_transaction.bank_reference, "BANK-APPROVED")

    @patch("payment_gateaway.views.authorize_payment")
    def test_failed_payment_updates_order_and_transaction(self, mocked_bank):
        mocked_bank.return_value = {
            "bank_response": "DECLINED",
            "bank_reference": "BANK-DECLINED",
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.post("/pay", self.pay_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "FAILED")
        self.assertEqual(response.data["bank_response"], "DECLINED")
        self.assertEqual(response.data["message"], "Payment declined")

        order = Order.objects.get()
        payment_transaction = Transaction.objects.get()
        self.assertEqual(order.status, Order.Status.FAILED)
        self.assertEqual(payment_transaction.status, Transaction.Status.FAILED)
        self.assertEqual(payment_transaction.bank_response, Transaction.BankResponse.DECLINED)
        self.assertEqual(payment_transaction.bank_reference, "BANK-DECLINED")
