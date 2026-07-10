"""Celery configuration """

import os
from celery import Celery
from decouple import config
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Get environment 
ENVIRONMENT = config('ENVIRONMENT', default='development')

app = Celery('financial_auth_service')

# Load configuration from Django settings, using a namespace to avoid conflicts
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto discover tasks in all installed apps
app.autodiscover_tasks()

# Celery beat schedule
app.conf.beat_schedule = {
    'clean-expired-tokens-daily': {
        'task': 'accounts.tasks.cleanup_expired_tokens_task',
        'schedule': crontab(hour=2, minute=0), # 2am daily
    },
    'cleanup-old-audit-logs-weekly': {
        'task': 'accounts.tasks.cleanup_old_audit_logs_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Run at 3 AM every Sunday
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing celery"""
    print(f'Request: {self.request!r}')