from datetime import datetime, timedelta
import jwt
from django.conf import settings
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
import logging

logger = logging.getLogger(__name__)

class TokenRefreshMiddleware:
    """Token自动刷新中间件"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # 设置token刷新阈值为过期前2小时
        self.refresh_threshold = timedelta(hours=2)
        # 设置缓存时间为5分钟
        self.cache_timeout = 300
        self.jwt_auth = JWTAuthentication()

    def _is_token_blacklisted(self, jti):
        """检查token是否在黑名单中"""
        cache_key = f'token_blacklist_{jti}'
        is_blacklisted = cache.get(cache_key)
        
        if is_blacklisted is None:
            is_blacklisted = BlacklistedToken.objects.filter(
                token__jti=jti
            ).exists()
            cache.set(cache_key, is_blacklisted, self.cache_timeout)
            
        return is_blacklisted

    def _should_refresh_token(self, exp_datetime, now):
        """判断是否应该刷新token"""
        # 检查是否在刷新阈值内
        if exp_datetime - now < self.refresh_threshold:
            return True
        return False

    def _get_cached_token(self, user_id, exp_timestamp):
        """从缓存获取token"""
        cache_key = f'user_token_{user_id}_{exp_timestamp}'
        return cache.get(cache_key)

    def _cache_token(self, user_id, exp_timestamp, token):
        """缓存token"""
        cache_key = f'user_token_{user_id}_{exp_timestamp}'
        cache.set(cache_key, token, self.cache_timeout)

    def _set_token_response(self, response, new_access_token, exp_datetime):
        """设置token响应"""
        # 设置标准的Authorization响应头
        response['Authorization'] = f'Bearer {new_access_token}'
        # 设置token过期时间
        response['Token-Expires-At'] = exp_datetime.isoformat()
        
        # 如果启用了Cookie认证,也更新Cookie
        if hasattr(settings, 'SIMPLE_JWT') and settings.SIMPLE_JWT.get('AUTH_COOKIE'):
            response.set_cookie(
                settings.SIMPLE_JWT['AUTH_COOKIE'],
                new_access_token,
                expires=exp_datetime,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly=settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                path=settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
            )
        
        return response

    def __call__(self, request):
        # 获取当前token
        try:
            header = self.jwt_auth.get_header(request)
            if header is None:
                return self.get_response(request)

            raw_token = self.jwt_auth.get_raw_token(header)
            if raw_token is None:
                return self.get_response(request)

            validated_token = self.jwt_auth.get_validated_token(raw_token)
            
            # 检查token是否在黑名单中
            if self._is_token_blacklisted(validated_token['jti']):
                logger.warning(f"Blacklisted token attempted to access: {validated_token['jti']}")
                return self.get_response(request)
            
            # 检查token是否需要刷新
            exp_timestamp = validated_token['exp']
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            
            if self._should_refresh_token(exp_datetime, now):
                try:
                    # 获取用户
                    user = self.jwt_auth.get_user(validated_token)
                    if user:
                        # 检查缓存中是否已有新token
                        cached_token = self._get_cached_token(user.id, exp_timestamp)
                        if cached_token:
                            response = self.get_response(request)
                            return self._set_token_response(response, cached_token, exp_datetime)
                        
                        # 生成新token
                        refresh = RefreshToken.for_user(user)
                        new_access_token = str(refresh.access_token)
                        
                        # 缓存新token
                        self._cache_token(user.id, exp_timestamp, new_access_token)
                        
                        # 在响应中设置新token
                        response = self.get_response(request)
                        response = self._set_token_response(response, new_access_token, exp_datetime)
                        
                        logger.info(f"Token refreshed for user {user.username}")
                        return response
                except (TokenError, Exception) as e:
                    logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
                    # 如果刷新失败，继续使用原token
                    return self.get_response(request)
            
            return self.get_response(request)
            
        except InvalidToken as e:
            logger.warning(f"Invalid token: {str(e)}")
            return self.get_response(request)
        except Exception as e:
            logger.error(f"Unexpected error in token refresh: {str(e)}", exc_info=True)
            return self.get_response(request) 