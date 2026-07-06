from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    BankAuthorizeRequestSerializer,
    BankAuthorizeResponseSerializer,
)
from .services import simulate_authorization


class BankAuthorizeView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = BankAuthorizeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bank_result = simulate_authorization()
        response_serializer = BankAuthorizeResponseSerializer(bank_result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
