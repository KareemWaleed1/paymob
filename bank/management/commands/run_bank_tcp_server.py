from django.conf import settings
from django.core.management.base import BaseCommand

from bank.tcp import serve


class Command(BaseCommand):
    help = "Run the bank TCP socket server."

    def add_arguments(self, parser):
        parser.add_argument("--host", default=settings.BANK_TCP_HOST)
        parser.add_argument("--port", default=settings.BANK_TCP_PORT, type=int)

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]
        self.stdout.write(f"Bank TCP server listening on {host}:{port}")
        serve(host, port)
