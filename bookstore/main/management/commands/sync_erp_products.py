from django.core.management.base import BaseCommand, CommandError

from integrations.erp import ErpConfigurationError, sync_erp_products


class Command(BaseCommand):
    help = 'Sync products from the ERP API.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--updated-since',
            dest='updated_since',
            help='ISO-8601 datetime or date for incremental sync.',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Ignore stored sync state and fetch all products.',
        )
        parser.add_argument(
            '--page-size',
            type=int,
            dest='page_size',
            help='Override ERP page size (max 1000).',
        )
        parser.add_argument(
            '--limit',
            type=int,
            dest='limit',
            help='Limit number of products processed (debug).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Do not persist any changes.',
        )

    def handle(self, *args, **options):
        updated_since = options.get('updated_since')
        full = options.get('full')
        page_size = options.get('page_size')
        limit = options.get('limit')
        dry_run = options.get('dry_run')

        try:
            stats = sync_erp_products(
                updated_since=updated_since,
                page_size=page_size,
                dry_run=dry_run,
                limit=limit,
                read_state=not full and not updated_since,
                write_state=not dry_run,
            )
        except ErpConfigurationError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                'ERP sync finished: '
                f"created={stats['created']} updated={stats['updated']} "
                f"skipped={stats['skipped']} errors={stats['errors']}"
            )
        )
