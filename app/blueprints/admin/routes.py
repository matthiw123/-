from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.supabase_client import get_supabase_admin
from app.auth_utils import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard")
@role_required("admin")
def dashboard():
    supabase = get_supabase_admin()

    pending_products = supabase.table("products").select(
        "*, profiles(shop_name, full_name), categories(name), product_images(image_url, is_cover)"
    ).eq("status", "pending").order("created_at", desc=True).execute().data

    all_products = supabase.table("products").select("id, status").execute().data
    stats = {
        "pending": len([p for p in all_products if p["status"] == "pending"]),
        "approved": len([p for p in all_products if p["status"] == "approved"]),
        "rejected": len([p for p in all_products if p["status"] == "rejected"]),
        "total": len(all_products),
    }

    return render_template(
        "admin/dashboard.html", pending_products=pending_products, stats=stats
    )


@bp.route("/products")
@role_required("admin")
def all_products():
    supabase = get_supabase_admin()
    status_filter = request.args.get("status")

    query = supabase.table("products").select(
        "*, profiles(shop_name, full_name), categories(name)"
    )
    if status_filter:
        query = query.eq("status", status_filter)

    products = query.order("created_at", desc=True).execute().data
    return render_template("admin/products.html", products=products, status_filter=status_filter)


@bp.route("/products/<product_id>/approve", methods=["POST"])
@role_required("admin")
def approve_product(product_id):
    supabase = get_supabase_admin()
    supabase.table("products").update({"status": "approved"}).eq("id", product_id).execute()
    flash("อนุมัติสินค้าแล้ว", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


@bp.route("/products/<product_id>/reject", methods=["POST"])
@role_required("admin")
def reject_product(product_id):
    supabase = get_supabase_admin()
    supabase.table("products").update({"status": "rejected"}).eq("id", product_id).execute()
    flash("ปฏิเสธสินค้าแล้ว", "info")
    return redirect(request.referrer or url_for("admin.dashboard"))


@bp.route("/products/<product_id>/delete", methods=["POST"])
@role_required("admin")
def delete_product(product_id):
    supabase = get_supabase_admin()
    supabase.table("products").delete().eq("id", product_id).execute()
    flash("ลบสินค้าแล้ว", "info")
    return redirect(request.referrer or url_for("admin.dashboard"))
