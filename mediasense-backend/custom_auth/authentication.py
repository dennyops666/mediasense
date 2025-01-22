import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

class CustomJWTAuthentication(JWTAuthentication):
    """自定义JWT认证"""

    def get_validated_token(self, raw_token):
        """验证token"""
        try:
            # 验证token
            token = super().get_validated_token(raw_token)
            
            # 检查token是否在黑名单中
            jti = token.get('jti')
            if jti:
                try:
                    outstanding_token = OutstandingToken.objects.get(jti=jti)
                    if BlacklistedToken.objects.filter(token=outstanding_token).exists():
                        logger.warning(f"Token {jti} is blacklisted")
                        raise AuthenticationFailed(
                            detail={"message": "令牌已被注销"},
                            code="token_blacklisted"
                        )
                except OutstandingToken.DoesNotExist:
                    logger.warning(f"Token {jti} not found in outstanding tokens")
                    raise AuthenticationFailed(
                        detail={"message": "无效的令牌"},
                        code="token_invalid"
                    )
            
            return token
        except InvalidToken as e:
            logger.error(f"Invalid token error: {str(e)}")
            raise AuthenticationFailed(
                detail={"message": "无效的令牌"},
                code="token_invalid"
            )
        except TokenError as e:
            logger.error(f"Token error: {str(e)}")
            raise AuthenticationFailed(
                detail={"message": "令牌已过期"},
                code="token_expired"
            )
        except AuthenticationFailed as e:
            raise e
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise AuthenticationFailed(
                detail={"message": "认证失败"},
                code="authentication_failed"
            )

    def authenticate(self, request):
        """认证请求"""
        try:
            header = self.get_header(request)
            if header is None:
                logger.warning("No auth header found")
                raise AuthenticationFailed(
                    detail={"message": "未提供认证令牌"},
                    code="no_auth_token"
                )

            raw_token = self.get_raw_token(header)
            if raw_token is None:
                logger.warning("No raw token found in header")
                raise AuthenticationFailed(
                    detail={"message": "无效的令牌格式"},
                    code="invalid_token_format"
                )

            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            
            if not user.is_active:
                logger.warning(f"User {user.username} is disabled")
                raise AuthenticationFailed(
                    detail={"message": "用户账号已被禁用"},
                    code="user_disabled"
                )
            
            return user, validated_token
        
        except AuthenticationFailed as e:
            raise e
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationFailed(
                detail={"message": "认证失败"},
                code="authentication_failed"
            ) 