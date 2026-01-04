from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

SECRET_KEY = "c038fmrv02xw02302ejdioc" # Thay bằng chuỗi ngẫu nhiên
# Thuật toán sinh token
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Đối tượng dùng để băm mật khẩu (hash password)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """Verify mật khẩu khi người dùng đăng nhập"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Băm mật khẩu để lưu vào database khi người dùng đăng ký"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tạo access token cho người dùng trong phiên truy cập"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
