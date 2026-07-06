from django.urls import path

from .views import PayView


urlpatterns = [
    path("pay", PayView.as_view())
]
