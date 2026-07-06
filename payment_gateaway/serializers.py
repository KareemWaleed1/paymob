from decimal import Decimal

from rest_framework import serializers


class PayRequestSerializer(serializers.Serializer):
    terminal_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    currency = serializers.CharField(max_length=3, min_length=3)

    def validate_currency(self, value):
        return value.upper()


class PayResponseSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    transaction_id = serializers.IntegerField()
    status = serializers.CharField()
    bank_response = serializers.CharField()
    message = serializers.CharField()
