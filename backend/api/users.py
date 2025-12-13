from flask import Blueprint, request, jsonify, g
from sqlalchemy.orm import Session

from models.database import get_db
from utils.auth import login_required
from utils.database import PropertyService
from utils.user_service import UserService

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("/me", methods=["GET"])
@login_required
def current_user():
    db: Session = next(get_db())
    user_service = UserService(db)
    user = user_service.get_user_by_id(g.current_user_id)

    if not user:
        return jsonify({
            "success": False,
            "error": "用户不存在"
        }), 404

    contact_stats = user_service.get_contact_stats(user.id)

    return jsonify({
        "success": True,
        "data": {
            "user": user_service.serialize_user(user),
            "contact_stats": contact_stats,
        }
    })


@users_bp.route("/contact-link", methods=["POST"])
@login_required
def contact_link():
    payload = request.get_json() or {}
    property_id = payload.get("property_id")

    if not property_id:
        return jsonify({
            "success": False,
            "error": "property_id 为必填项"
        }), 400

    db: Session = next(get_db())
    property_service = PropertyService(db)
    user_service = UserService(db)

    user = user_service.get_user_by_id(g.current_user_id)
    if not user:
        return jsonify({
            "success": False,
            "error": "用户不存在"
        }), 404

    property_obj = property_service.get_property_by_id(property_id)
    if not property_obj:
        return jsonify({
            "success": False,
            "error": "房源不存在"
        }), 404

    if not property_obj.url:
        return jsonify({
            "success": False,
            "error": "该房源缺少原始链接"
        }), 400

    contact_stats = user_service.get_contact_stats(user.id)
    if contact_stats["remaining"] <= 0:
        return jsonify({
            "success": False,
            "error": "今日联系次数已用完",
            "contact_stats": contact_stats
        }), 403

    user_service.log_contact_action(user.id, property_obj.id, property_obj.url)
    updated_stats = user_service.get_contact_stats(user.id)

    return jsonify({
        "success": True,
        "data": {
            "contact_url": property_obj.url,
            "property": {
                "id": property_obj.id,
                "title": property_obj.title,
            },
            "contact_stats": updated_stats
        }
    })




