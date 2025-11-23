from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from .migration_cleanup import ensure_custom_user_migration_precedes_admin

        ensure_custom_user_migration_precedes_admin()
