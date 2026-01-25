import requests
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session

from config import Config
from models.database import get_db
from utils.auth import generate_token
from utils.user_service import UserService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _exchange_code_for_session(code: str):
    """调用微信接口换取 openid 与 session_key"""
    if not Config.WECHAT_APP_ID or not Config.WECHAT_APP_SECRET:
        if Config.DEBUG:
            # 开发模式下允许使用假数据，便于本地调试
            return {
                "openid": f"debug_{code}",
                "session_key": "debug-session-key",
                "unionid": None,
            }
        raise ValueError("WECHAT_APP_ID 或 WECHAT_APP_SECRET 未配置")

    try:
        print(f"[AUTH] 调用微信 code2Session，appid: {Config.WECHAT_APP_ID[:8]}...")
        resp = requests.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": Config.WECHAT_APP_ID,
                "secret": Config.WECHAT_APP_SECRET,
                "js_code": code,
                "grant_type": "authorization_code",
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"[AUTH] 微信 API 响应: {data}")
    except requests.RequestException as exc:
        print(f"[AUTH] ❌ 微信登录接口调用失败: {exc}")
        raise ValueError(f"微信登录接口调用失败: {exc}") from exc

    if data.get("errcode"):
        errcode = data.get("errcode")
        errmsg = data.get("errmsg", "unknown error")
        rid = data.get("rid", "")
        error_detail = f"微信登录失败: {errmsg}"
        if errcode:
            error_detail += f" (errcode: {errcode})"
        if rid:
            error_detail += f", rid: {rid}"
        
        # 常见错误码说明
        if errcode == 40029:
            error_detail += "。code 已过期或已使用，请重新获取"
        elif errcode == 40163:
            error_detail += "。code 已被使用，请重新获取"
        elif errcode == 45011:
            error_detail += "。API 调用太频繁，请稍后再试"
        
        print(f"[AUTH] ❌ {error_detail}")
        raise ValueError(error_detail)

    print(f"[AUTH] ✅ 成功获取 openid: {data.get('openid', '')[:10]}...")
    return data


@auth_bp.route("/login", methods=["POST"])
def wechat_login():
    payload = request.get_json() or {}
    code = payload.get("code")
    user_info = payload.get("user_info") or {}

    if not code:
        return jsonify({
            "success": False,
            "error": "code 为必填项"
        }), 400

    try:
        session_data = _exchange_code_for_session(code)
    except ValueError as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
        }), 400

    openid = session_data.get("openid")
    session_key = session_data.get("session_key")
    unionid = session_data.get("unionid")

    if not openid:
        return jsonify({
            "success": False,
            "error": "未获取到openid"
        }), 400

    db: Session = next(get_db())
    user_service = UserService(db)
    user = user_service.upsert_wechat_user(
        openid=openid,
        session_key=session_key,
        unionid=unionid,
        profile=user_info,
    )

    token = generate_token(user.id)
    contact_stats = user_service.get_contact_stats(user.id)

    return jsonify({
        "success": True,
        "data": {
            "token": token,
            "expires_in": Config.AUTH_TOKEN_EXPIRES,
            "user": user_service.serialize_user(user),
            "contact_stats": contact_stats,
        }
    })






