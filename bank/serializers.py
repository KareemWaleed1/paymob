from decimal import Decimal

from rest_framework import serializers


class BankAuthorizeRequestSerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField(min_value=1)
    merchant_id = serializers.IntegerField(min_value=1)
    terminal_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
    )
    currency = serializers.CharField(max_length=3, min_length=3)

    def validate_currency(self, value):
        return value.upper()


class BankAuthorizeResponseSerializer(serializers.Serializer):
    bank_response = serializers.ChoiceField(choices=["APPROVED", "DECLINED"])
    bank_reference = serializers.CharField()
