"""
ตัวช่วยเรื่อง session / การตรวจสิทธิ์
เราเก็บ user_id, role, access_token, full_name ไว้ใน Flask session
หลังจากล็อกอินสำเร็จผ่าน Supabase Auth
"""
from functools import wraps
from flask import session, redirect, url_for, flash, g
from app.supabase_client import get_supabase


def current_user():
    if "user_id" not in session:
        return None
    return {
        "id": session.get("user_id"),
        "role": session.get("role"),
        "full_name": session.get("full_name"),
        "email": session.get("email"),
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("กรุณาเข้าสู่ระบบก่อน", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("กรุณาเข้าสู่ระบบก่อน", "warning")
                return redirect(url_for("auth.login"))
            if session.get("role") != role:
                flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้", "danger")
                return redirect(url_for("buyer.home"))
            return view(*args, **kwargs)
        return wrapped
    return decorator
