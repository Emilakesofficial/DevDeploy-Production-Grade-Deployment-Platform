"""
Management command to clear user account lockout
"""
from django.core.management.base import BaseCommand
from accounts.services.security_service import SecurityService


class Command(BaseCommand):
    help = 'Clear login lockout for a specific user email'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the locked user'
        )

    def handle(self, *args, **options):
        email = options['email']

        self.stdout.write(f"Clearing lockout for: {email}")

        SecurityService.clear_user_lockout(email)

        # Verify
        is_locked, attempts, ttl = SecurityService.check_login_attempts(email)

        if not is_locked and attempts == 0:
            self.stdout.write(
                self.style.SUCCESS(f"✓ Lockout cleared for {email}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"✗ Could not clear lockout for {email}")
            )