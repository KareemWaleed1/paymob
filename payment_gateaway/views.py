from django.db import transaction
from bank.client import BankClientError, authorize_payment
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, Terminal, Transaction
from .permissions import IsMerchantUser
from .serializers import PayRequestSerializer, PayResponseSerializer


class PayView(APIView):
    permission_classes = [IsMerchantUser]

    @transaction.atomic
    def post(self, request):
        serializer = PayRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        merchant = request.user.merchant
        terminal_id = serializer.validated_data["terminal_id"]

        try:
            terminal = Terminal.objects.select_for_update().get(
                id=terminal_id,
                merchant=merchant,
                is_active=True,
            )
        except Terminal.DoesNotExist:
            return Response(
                {"detail": "Terminal not found for this merchant or is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        amount = serializer.validated_data["amount"]
        currency = serializer.validated_data["currency"]

        order = Order.objects.create(
            merchant=merchant,
            amount=amount,
            currency=currency,
            status=Order.Status.PENDING,
        )
        payment_transaction = Transaction.objects.create(
            order=order,
            merchant=merchant,
            terminal=terminal,
            amount=amount,
            status=Transaction.Status.PENDING,
        )

        try:
            bank_result = authorize_payment(payment_transaction)
        except BankClientError:
            return Response(
                {"detail": "Bank service is unavailable."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        bank_response = bank_result["bank_response"]

        if bank_response == Transaction.BankResponse.APPROVED:
            payment_transaction.status = Transaction.Status.SUCCESS
            order.status = Order.Status.PAID
            message = "Payment approved"
        else:
            payment_transaction.status = Transaction.Status.FAILED
            order.status = Order.Status.FAILED
            message = "Payment declined"

        payment_transaction.bank_response = bank_response
        payment_transaction.bank_reference = bank_result["bank_reference"]
        payment_transaction.save(
            update_fields=["status", "bank_response", "bank_reference", "updated_at"]
        )
        order.save(update_fields=["status", "updated_at"])

        response_data = {
            "order_id": order.id,
            "transaction_id": payment_transaction.id,
            "status": payment_transaction.status,
            "bank_response": payment_transaction.bank_response,
            "message": message,
        }
        response_serializer = PayResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
