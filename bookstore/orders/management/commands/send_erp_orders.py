from django.core.management.base import BaseCommand, CommandError

from integrations.erp import ErpConfigurationError, send_order_to_erp, require_erp_client
from orders.models import Order


class Command(BaseCommand):
    help = 'Send pending orders to the ERP API.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            dest='order_ids',
            action='append',
            type=int,
            help='Send only the specified order id (can be repeated).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            dest='limit',
            help='Limit number of orders processed.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only show which orders would be sent.',
        )

    def handle(self, *args, **options):
        try:
            require_erp_client()
        except ErpConfigurationError as exc:
            raise CommandError(str(exc)) from exc

        order_ids = options.get('order_ids') or []
        limit = options.get('limit')
        dry_run = options.get('dry_run')

        queryset = Order.objects.filter(erp_acknowledged_at__isnull=True).order_by('created_at')
        if order_ids:
            queryset = queryset.filter(pk__in=order_ids)
        if limit:
            queryset = queryset[:limit]

        sent = 0
        errors = 0
        for order in queryset:
            if dry_run:
                self.stdout.write(f'Would send order {order.pk}')
                continue
            try:
                send_order_to_erp(order)
                sent += 1
            except Exception as exc:  # pylint: disable=broad-except
                errors += 1
                self.stderr.write(f'Failed to send order {order.pk}: {exc}')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('Dry run completed.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'ERP order push finished: sent={sent} errors={errors}')
            )
