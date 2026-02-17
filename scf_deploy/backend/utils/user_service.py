from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from config import Config
from models.database import User, UserContactLog


class UserService:
    """用户与联系记录相关操作"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_openid(self, openid: str) -> Optional[User]:
        if not openid:
            return None
        return self.db.query(User).filter(User.openid == openid).first()

    def upsert_wechat_user(
        self,
        openid: str,
        session_key: Optional[str] = None,
        unionid: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> User:
        """根据 openid 创建或更新微信用户"""
        profile = profile or {}
        user = self.get_user_by_openid(openid)

        nickname = profile.get("nickName") or profile.get("nickname")
        avatar_url = profile.get("avatarUrl") or profile.get("avatar_url")

        if user:
            if session_key:
                user.session_key = session_key
            if unionid:
                user.unionid = unionid
        else:
            user = User(
                openid=openid,
                unionid=unionid,
                session_key=session_key,
            )
            self.db.add(user)

        # 更新常规信息
        if nickname:
            user.nickname = nickname
        if avatar_url:
            user.avatar_url = avatar_url
        if profile.get("country"):
            user.country = profile.get("country")
        if profile.get("province"):
            user.province = profile.get("province")
        if profile.get("city"):
            user.city = profile.get("city")
        if profile.get("gender") is not None:
            user.gender = profile.get("gender")
        if profile.get("language"):
            user.language = profile.get("language")

        user.last_login_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(user)
        return user

    def serialize_user(self, user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "openid": user.openid,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "country": user.country,
            "province": user.province,
            "city": user.city,
            "gender": user.gender,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    def get_contact_stats(self, user_id: int) -> Dict[str, int]:
        """返回今日联系次数和剩余额度。开发者 openid 在白名单内则不受限制（剩余 999）。"""
        user = self.get_user_by_id(user_id)
        if user and getattr(Config, "DEVELOPER_OPENIDS", None) and user.openid in Config.DEVELOPER_OPENIDS:
            return {"limit": 999, "used": 0, "remaining": 999}

        today = datetime.utcnow().date()
        used = (
            self.db.query(func.count(UserContactLog.id))
            .filter(
                UserContactLog.user_id == user_id,
                func.date(UserContactLog.created_at) == today,
            )
            .scalar()
        ) or 0

        limit = Config.DAILY_CONTACT_LIMIT
        remaining = max(0, limit - used)
        return {
            "limit": limit,
            "used": used,
            "remaining": remaining,
        }

    def log_contact_action(self, user_id: int, property_id: int, property_url: Optional[str]) -> UserContactLog:
        """记录联系中介行为"""
        log = UserContactLog(
            user_id=user_id,
            property_id=property_id,
            property_url=property_url,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
