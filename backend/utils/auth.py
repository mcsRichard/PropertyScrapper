from functools import wraps
from typing import Optional

from flask import request, jsonify, g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from config import Config

_serializer: Optional[URLSafeTimedSerializer] = None


def _get_serializer() -> URLSafeTimedSerializer:
    global _serializer
    if _serializer is None:
        _serializer = URLSafeTimedSerializer(
            secret_key=Config.SECRET_KEY,
            salt="miniapp-auth",
        )
    return _serializer


def generate_token(user_id: int) -> str:
    return _get_serializer().dumps({"user_id": user_id})


def verify_token(token: str) -> int:
    data = _get_serializer().loads(token, max_age=Config.AUTH_TOKEN_EXPIRES)
    return data["user_id"]


def extract_token() -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    token = request.headers.get("X-Auth-Token")
    if token:
        return token.strip()
    return request.args.get("token")


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = extract_token()
        if not token:
            return _unauthorized("Missing authentication token")
        try:
            user_id = verify_token(token)
        except SignatureExpired:
            return _unauthorized("Token expired, please log in again")
        except BadSignature:
            return _unauthorized("Invalid token, please log in again")

        g.current_user_id = user_id
        return func(*args, **kwargs)

    return wrapper


def _unauthorized(message: str):
    return jsonify({
        "success": False,
        "error": message
    }), 401






