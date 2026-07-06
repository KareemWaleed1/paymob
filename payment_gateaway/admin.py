from django.contrib import admin

from .models import Merchant, Order, Terminal, Transaction


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "user", "created_at")
    search_fields = ("name", "email", "user__username")


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    list_display = ("id", "terminal_code", "merchant", "location", "is_active", "created_at")
    list_filter = ("is_active", "merchant")
    search_fields = ("terminal_code", "location", "merchant__name")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "amount", "currency", "status", "created_at", "updated_at")
    list_filter = ("status", "currency", "merchant")
    search_fields = ("merchant__name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "merchant",
        "terminal",
        "amount",
        "status",
        "bank_response",
        "bank_reference",
        "created_at",
    )
    list_filter = ("status", "bank_response", "merchant", "terminal")
    search_fields = ("bank_reference", "merchant__name", "terminal__terminal_code")
