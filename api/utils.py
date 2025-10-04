from django.utils import timezone
from datetime import timedelta
from .models import LoginAttempt, User


def unblock_user(user):
    """Разблокирует пользователя и очищает историю неудачных попыток"""
    user.is_active = True
    user.save()

    # Очищаем старые неудачные попытки (опционально)
    time_threshold = timezone.now() - timedelta(hours=1)
    LoginAttempt.objects.filter(
        user=user,
        successful=False,
        timestamp__lt=time_threshold
    ).delete()


def get_user_login_stats(user):
    """Возвращает статистику входов пользователя"""
    last_24_hours = timezone.now() - timedelta(hours=24)

    stats = {
        'total_attempts': LoginAttempt.objects.filter(user=user).count(),
        'failed_attempts_24h': LoginAttempt.objects.filter(
            user=user,
            successful=False,
            timestamp__gte=last_24_hours
        ).count(),
        'successful_attempts_24h': LoginAttempt.objects.filter(
            user=user,
            successful=True,
            timestamp__gte=last_24_hours
        ).count(),
        'last_login': LoginAttempt.objects.filter(
            user=user,
            successful=True
        ).first().timestamp if LoginAttempt.objects.filter(user=user, successful=True).exists() else None
    }

    return stats