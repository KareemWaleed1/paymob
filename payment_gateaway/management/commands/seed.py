from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from payment_gateaway.models import Merchant, Terminal


class Command(BaseCommand):
    help = "Seed the local database with demo users, merchants, and terminals."

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()

        admin_user, admin_created = user_model.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if admin_created:
            admin_user.set_password("admin123")
            admin_user.save(update_fields=["password"])

        merchant_one_user = self.create_user(
            user_model,
            username="merchant_one",
            email="merchant1@example.com",
            password="merchant123",
        )
        merchant_two_user = self.create_user(
            user_model,
            username="merchant_two",
            email="merchant2@example.com",
            password="merchant123",
        )

        merchant_one = self.create_merchant(
            user=merchant_one_user,
            name="Cairo Electronics",
            email="payments@cairoelectronics.example",
        )
        merchant_two = self.create_merchant(
            user=merchant_two_user,
            name="Alexandria Market",
            email="payments@alexmarket.example",
        )

        self.create_terminal(
            merchant=merchant_one,
            terminal_code="TERM-CAI-001",
            location="Cairo Branch",
        )
        self.create_terminal(
            merchant=merchant_one,
            terminal_code="TERM-CAI-002",
            location="Nasr City Branch",
        )
        self.create_terminal(
            merchant=merchant_two,
            terminal_code="TERM-ALX-001",
            location="Alexandria Branch",
        )

        self.stdout.write(self.style.SUCCESS("Seed data is ready."))
        self.stdout.write("")
        self.stdout.write("Admin login:")
        self.stdout.write("  username: admin")
        self.stdout.write("  password: admin123")
        self.stdout.write("")
        self.stdout.write("Merchant logins for JWT:")
        self.stdout.write("  username: merchant_one")
        self.stdout.write("  password: merchant123")
        self.stdout.write("  terminal_ids: " + self.terminal_ids_for(merchant_one))
        self.stdout.write("")
        self.stdout.write("  username: merchant_two")
        self.stdout.write("  password: merchant123")
        self.stdout.write("  terminal_ids: " + self.terminal_ids_for(merchant_two))

    def create_user(self, user_model, username, email, password):
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

    def create_merchant(self, user, name, email):
        merchant, _ = Merchant.objects.update_or_create(
            user=user,
            defaults={
                "name": name,
                "email": email,
            },
        )
        return merchant

    def create_terminal(self, merchant, terminal_code, location):
        Terminal.objects.update_or_create(
            terminal_code=terminal_code,
            defaults={
                "merchant": merchant,
                "location": location,
                "is_active": True,
            },
        )

    def terminal_ids_for(self, merchant):
        terminal_ids = merchant.terminals.order_by("id").values_list("id", flat=True)
        return ", ".join(str(terminal_id) for terminal_id in terminal_ids)
