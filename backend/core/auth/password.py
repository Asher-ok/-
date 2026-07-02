"""
密码加密和验证
"""
from passlib.context import CryptContext

# 使用 pbkdf2_sha256 作为备用方案，更兼容
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # 使用 pbkdf2_sha256 方案，更稳定
    return pwd_context.hash(password, scheme="pbkdf2_sha256")
