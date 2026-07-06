from django.urls import path

from .views import BankAuthorizeView


urlpatterns = [
    path("authorize/", BankAuthorizeView.as_view()),
]
