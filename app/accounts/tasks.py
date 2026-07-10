from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from accounts.models import User
from accounts.services.email_service import EmailService

from audit.models import AuditLog
from datetime import timedelta

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self, user_id):
    """Send welcome email to newly registered user"""
    try:
        user = User.objects.get(id=user_id)
        EmailService.send_welcome_email(user)
        
        logger.info(f"Welcome email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
    except user.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return {'status': 'error', 'message': 'User not found.'}
    
    except Exception as exc:
        logger.error(f"Error sending welcome email to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)
    
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email_task(self, user_id, verification_token):
    """send email verification link"""
    logger.warning(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    logger.warning(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NONE'}")
    logger.warning(f"PASSWORD LENGTH: {len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 0}")
    try:
        user = User.objects.get(id=user_id)
        EmailService.send_verification_email(user, verification_token)
        
        logger.info(f"Verification email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return {'status': 'error', 'message': 'User not found'}
        
    except Exception as exc:
        logger.error(f"Error sending verification email to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)
    
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_task(self, user_id, reset_token):
    """send password reset link"""
    try:
        user = User.objects.get(id=user_id)
        EmailService.send_password_reset_email(user, reset_token)
        
        logger.info(f"Password reset email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return {'status': 'error', 'message': 'User not found'}
        
    except Exception as exc:
        logger.error(f"Error sending password reset email to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)
    
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_suspicious_activity_alert_task(self, user_id, activity_details):
    """Send suspicious activity alert"""
    
    try:
        user = User.objects.get(id=user_id)
        EmailService.send_suspicious_activity_alert(user, activity_details)
        
        logger.warning(f"Suspicious activity alert sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return {'status': 'error', 'message': 'User not found'}
        
    except Exception as exc:
        logger.error(f"Error sending suspicious activity alert to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)
    
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_changed_email_task(self, user_id):
    """Send password changed notification"""
    
    try:
        user = User.objects.get(id=user_id)
        EmailService.send_password_changed_email(user)
        
        logger.info(f"Password changed email sent to {user.email}")
        return {'status': 'success', 'email': user.email}
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return {'status': 'error', 'message': 'User not found'}
        
    except Exception as exc:
        logger.error(f"Error sending password changed email to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)
    
@shared_task
def cleanup_expired_tokens_task():
    """Periodic task to clean up expired tokens, Runs daily via Celery Beat"""
    try:
        from accounts.services.token_service import TokenService
        
        TokenService.cleanup_expired_tokens()
        
        logger.info("Expired tokens cleaned up successfully")
        return {'status': 'success', 'timestamp': str(timezone.now())}
        
    except Exception as exc:
        logger.error(f"Error cleaning up expired tokens: {str(exc)}")
        return {'status': 'error', 'message': str(exc)}
    
@shared_task
def cleanup_old_audit_logs_task():
    """
    Periodic task to cleanup old audit logs, Keep logs for 90 days"""
    try:
        cutoff_date = timezone.now() - timedelta(days=90)
        deleted_count, _ = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
        
        logger.info(f"Deleted {deleted_count} old audit log entries")
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as exc:
        logger.error(f"Error cleaning up audit logs: {str(exc)}")
        return {'status': 'error', 'message': str(exc)}