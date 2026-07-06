from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from payment_gateaway.models import Merchant, Order, Terminal, Transaction


class Command(BaseCommand):
    help = "Bulk seed demo orders and transactions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=1_000_000,
            help="Number of orders and transactions to create.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5_000,
            help="Rows to insert per bulk_create batch.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        batch_size = options["batch_size"]

        if count < 1:
            self.stdout.write(self.style.WARNING("Nothing to seed."))
            return

        if not Merchant.objects.exists() or not Terminal.objects.exists():
            call_command("seed")

        merchants = list(Merchant.objects.order_by("id"))
        terminals = list(Terminal.objects.select_related("merchant").order_by("id"))
        if not merchants or not terminals:
            raise RuntimeError("Seed merchants and terminals before seeding transactions.")

        created = 0
        while created < count:
            chunk_size = min(batch_size, count - created)
            orders = []

            for index in range(chunk_size):
                sequence = created + index + 1
                merchant = merchants[sequence % len(merchants)]
                success = sequence % 5 != 0
                amount = Decimal("100.00") + Decimal(sequence % 9000)
                orders.append(
                    Order(
                        merchant=merchant,
                        amount=amount,
                        currency="EGP",
                        status=Order.Status.PAID if success else Order.Status.FAILED,
                    )
                )

            with transaction.atomic():
                created_orders = Order.objects.bulk_create(orders, batch_size=batch_size)
                transactions = []
                for index, order in enumerate(created_orders):
                    sequence = created + index + 1
                    terminal = self.terminal_for_order(order, terminals, sequence)
                    success = order.status == Order.Status.PAID
                    transactions.append(
                        Transaction(
                            order=order,
                            merchant=order.merchant,
                            terminal=terminal,
                            amount=order.amount,
                            status=(
                                Transaction.Status.SUCCESS
                                if success
                                else Transaction.Status.FAILED
                            ),
                            bank_response=(
                                Transaction.BankResponse.APPROVED
                                if success
                                else Transaction.BankResponse.DECLINED
                            ),
                            bank_reference=f"SEED-BANK-{sequence:012d}",
                        )
                    )
                Transaction.objects.bulk_create(transactions, batch_size=batch_size)

            created += chunk_size
            self.stdout.write(f"Seeded {created:,}/{count:,} transactions...")

        self.stdout.write(self.style.SUCCESS(f"Seeded {count:,} transactions."))

    def terminal_for_order(self, order, terminals, sequence):
        merchant_terminals = [
            terminal for terminal in terminals if terminal.merchant_id == order.merchant_id
        ]
        if not merchant_terminals:
            raise RuntimeError(f"Merchant {order.merchant_id} has no terminals.")
        return merchant_terminals[sequence % len(merchant_terminals)]
