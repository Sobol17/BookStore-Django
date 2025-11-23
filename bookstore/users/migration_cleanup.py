import logging
from typing import Iterable, Tuple

from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.recorder import MigrationRecorder
from django.db.utils import OperationalError, ProgrammingError


logger = logging.getLogger(__name__)


def ensure_custom_user_migration_precedes_admin() -> None:
    """Reset admin migrations if they were applied before the users app.

    Deploying the project with the default User model and later switching to a
    custom one leaves ``admin.0001_initial`` recorded while
    ``users.0001_initial`` was never applied. Django rightfully treats this as
    an inconsistent history which blocks ``manage.py migrate``. When this state
    is detected we drop the admin log table (it is recreated automatically) and
    mark all admin migrations as unapplied so that Django can re-run them after
    ``users``.
    """

    connection = connections[DEFAULT_DB_ALIAS]

    try:
        recorder = MigrationRecorder(connection)
        recorder.ensure_schema()
        applied: Iterable[Tuple[str, str]] = recorder.applied_migrations()
    except (OperationalError, ProgrammingError):
        # Database isn't ready yet (e.g. migrations for a brand new DB). The
        # inconsistency can't exist in that case, so we can safely stop here.
        return

    applied_set = set(applied)
    admin_initial_applied = ('admin', '0001_initial') in applied_set
    users_is_pending = ('users', '0001_initial') not in applied_set

    if not admin_initial_applied or not users_is_pending:
        return

    logger.warning(
        "Detected admin migrations applied before users. Resetting admin"
        " migration history so that migrate can proceed."
    )

    _drop_admin_tables(connection)

    admin_migrations = sorted(
        [name for app, name in applied_set if app == 'admin'],
        reverse=True,
    )

    for migration_name in admin_migrations:
        try:
            recorder.record_unapplied('admin', migration_name)
        except (OperationalError, ProgrammingError) as exc:
            logger.error(
                "Failed to mark admin migration %s as unapplied: %s",
                migration_name,
                exc,
            )
            break


def _drop_admin_tables(connection) -> None:
    drop_statement = 'DROP TABLE IF EXISTS django_admin_log'
    if connection.vendor == 'postgresql':
        drop_statement += ' CASCADE'
    drop_statement += ';'

    try:
        with connection.cursor() as cursor:
            cursor.execute(drop_statement)
    except (OperationalError, ProgrammingError) as exc:
        logger.error("Failed to drop django_admin_log table: %s", exc)
