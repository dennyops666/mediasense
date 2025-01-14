import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """自定义 JWT 认证后端，增加黑名单检查"""

    def get_validated_token(self, raw_token):
        """验证 token 并检查黑名单"""
        token = super().get_validated_token(raw_token)
        
        # 检查 token 是否在黑名单中
        jti = token.get('jti')
        logger.debug(f"Checking token with JTI: {jti}")
        
        if jti:
            try:
                outstanding_token = OutstandingToken.objects.get(jti=jti)
                logger.debug(f"Found outstanding token: {outstanding_token}")
                
                if BlacklistedToken.objects.filter(token=outstanding_token).exists():
                    logger.debug(f"Token is blacklisted")
                    raise InvalidToken('Token is blacklisted')
                    
            except OutstandingToken.DoesNotExist:
                # 如果找不到 outstanding token,创建一个新的
                logger.debug(f"Creating new outstanding token")
                outstanding_token = OutstandingToken.objects.create(
                    user_id=token['user_id'],
                    jti=jti,
                    token=raw_token.decode(),
                    created_at=token.current_time,
                    expires_at=token.current_time + token.lifetime
                )
        
        return token

    def authenticate(self, request):
        """认证请求"""
        try:
            return super().authenticate(request)
        except InvalidToken as e:
            logger.debug(f"Token validation failed: {str(e)}")
            raise 