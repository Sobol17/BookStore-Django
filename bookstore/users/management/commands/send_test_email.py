from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP configuration'

    def add_arguments(self, parser):
        parser.add_argument('to_email', type=str, help='Recipient email address')
        parser.add_argument('--subject', type=str, default='Test email from BookStore')
        parser.add_argument('--message', type=str, default='This is a test email to verify SMTP settings.')

    def handle(self, *args, **options):
        to_email = options['to_email']
        subject = options['subject']
        message = options['message']

        self.stdout.write(self.style.NOTICE(
            f"Sending test email to {to_email} using backend={getattr(settings, 'EMAIL_BACKEND', None)} "
            f"host={getattr(settings, 'EMAIL_HOST', None)} port={getattr(settings, 'EMAIL_PORT', None)} "
            f"use_tls={getattr(settings, 'EMAIL_USE_TLS', None)} use_ssl={getattr(settings, 'EMAIL_USE_SSL', None)} "
            f"from={getattr(settings, 'DEFAULT_FROM_EMAIL', None)}"
        ))
        try:
            sent = send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@bookstore.local'),
                [to_email],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f"Failed to send email: {exc}")

        if sent:
            self.stdout.write(self.style.SUCCESS('Test email sent successfully.'))
        else:
            raise CommandError('send_mail returned 0 (not sent).')

