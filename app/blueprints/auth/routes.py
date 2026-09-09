from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.supabase_client import get_supabase, get_supabase_admin

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        full_name = request.form["full_name"].strip()
        role = request.form.get("role", "buyer")  # 'buyer' หรือ 'seller'
        shop_name = request.form.get("shop_name", "").strip()

        supabase = get_supabase()
        try:
            result = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": {"full_name": full_name}},
            })
        except Exception as e:
            flash(f"สมัครสมาชิกไม่สำเร็จ: {e}", "danger")
            return render_template("auth/register.html")

        user = result.user
        if user is None:
            flash("สมัครสมาชิกไม่สำเร็จ กรุณาลองใหม่", "danger")
            return render_template("auth/register.html")

        # อัปเดต role (และ shop_name ถ้าเป็นผู้ขาย) ใน profiles
        # ใช้ admin client เพราะตอนนี้ยังไม่มี session ที่ auth.uid() จะ match กับ RLS
        admin = get_supabase_admin()
        update_data = {"role": role}
        if role == "seller":
            update_data["shop_name"] = shop_name or f"ร้านของ {full_name}"
        admin.table("profiles").update(update_data).eq("id", user.id).execute()

        flash("สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form["email"].strip()
        password = request.form["password"]

        supabase = get_supabase()

        # ถ้าไม่มี @ แสดงว่าผู้ใช้กรอกชื่อมา ไม่ใช่อีเมล -> หาอีเมลจากชื่อก่อน
        if "@" in identifier:
            email = identifier
        else:
            admin = get_supabase_admin()
            match = admin.table("profiles").select("email").eq(
                "full_name", identifier
            ).limit(1).execute().data
            if not match or not match[0].get("email"):
                flash("ไม่พบชื่อผู้ใช้นี้ในระบบ", "danger")
                return render_template("auth/login.html")
            email = match[0]["email"]

        try:
            result = supabase.auth.sign_in_with_password({
                "email": email, "password": password
            })
        except Exception as e:
            flash("ชื่อ/อีเมล หรือรหัสผ่านไม่ถูกต้อง", "danger")
            return render_template("auth/login.html")

        user = result.user
        profile = supabase.table("profiles").select("*").eq("id", user.id).single().execute()
        profile_data = profile.data

        session["user_id"] = user.id
        session["email"] = user.email
        session["access_token"] = result.session.access_token
        session["role"] = profile_data["role"]
        session["full_name"] = profile_data["full_name"]

        flash(f"ยินดีต้อนรับ {profile_data['full_name']}", "success")
        if profile_data["role"] == "seller":
            return redirect(url_for("seller.dashboard"))
        elif profile_data["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("buyer.home"))

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบแล้ว", "info")
    return redirect(url_for("auth.login"))
