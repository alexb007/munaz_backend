from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from rest_framework_simplejwt.tokens import AccessToken
from .models import LoginAttempt
import logging
import json

logger = logging.getLogger(__name__)
User = get_user_model()


class BruteforceProtectedJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        # Получаем IP и user-agent
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Пытаемся получить username из запроса ДО аутентификации
        username = self.get_username_from_request(request)

        try:
            # Пытаемся аутентифицировать пользователя
            user_token = super().authenticate(request)

            if user_token:
                user, token = user_token
                # Логируем успешную попытку
                LoginAttempt.objects.create(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    successful=True
                )
                # Сбрасываем счетчик неудачных попыток при успешном входе
                self.reset_failed_attempts(user)
                return user, token

        except (AuthenticationFailed, InvalidToken) as e:
            # Логируем неудачную попытку
            if username:
                self.handle_failed_attempt(username, ip_address, user_agent, request)
            raise

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_username_from_request(self, request):
        """Извлекает username из тела запроса"""
        if request.method == 'POST' and request.body:
            try:
                # Для JSON запросов
                if request.content_type == 'application/json':
                    body = json.loads(request.body)
                    return body.get('username')
                # Для form-data
                elif 'application/x-www-form-urlencoded' in request.content_type:
                    return request.POST.get('username')
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        return None

    def handle_failed_attempt(self, username, ip_address, user_agent, request):
        """Обрабатывает неудачную попытку входа"""
        try:
            user = User.objects.get(username=username)
            # Логируем неудачную попытку для существующего пользователя
            self.log_failed_attempt(user, ip_address, user_agent)

            # Проверяем количество неудачных попыток
            if self.should_block_user(user):
                self.block_user(user)
                logger.warning(f"User {username} blocked due to too many failed login attempts from IP {ip_address}")
                raise PermissionDenied(
                    "Account temporarily locked due to too many failed login attempts. "
                    "Please try again later or contact administrator."
                )

        except User.DoesNotExist:
            # Логируем попытку входа с несуществующим пользователем
            self.log_failed_attempt_for_nonexistent_user(username, ip_address, user_agent)

    def log_failed_attempt(self, user, ip_address, user_agent):
        """Логирует неудачную попытку входа"""
        LoginAttempt.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            successful=False
        )
        logger.warning(f"Failed login attempt for user {user.username} from IP {ip_address}")

    def log_failed_attempt_for_nonexistent_user(self, username, ip_address, user_agent):
        """Логирует попытку входа для несуществующего пользователя"""
        logger.warning(f"Failed login attempt for non-existent user {username} from IP {ip_address}")
        # Если хотим хранить все попытки, даже для несуществующих пользователей:
        # LoginAttempt.objects.create(
        #     user=None,
        #     ip_address=ip_address,
        #     user_agent=user_agent,
        #     successful=False,
        #     username_attempt=username  # добавить это поле в модель
        # )

    def should_block_user(self, user):
        """Проверяет, нужно ли блокировать пользователя"""
        from django.utils import timezone
        from datetime import timedelta

        time_threshold = timezone.now() - timedelta(minutes=15)
        failed_attempts = LoginAttempt.objects.filter(
            user=user,
            successful=False,
            timestamp__gte=time_threshold
        ).count()

        return failed_attempts >= 3

    def block_user(self, user):
        """Блокирует пользователя"""
        user.is_active = False
        user.save()
        logger.info(f"User {user.username} has been blocked due to too many failed login attempts")

    def reset_failed_attempts(self, user):
        """Сбрасывает счетчик неудачных попыток (опционально)"""
        # Можно реализовать логику сброса при успешном входе
        pass