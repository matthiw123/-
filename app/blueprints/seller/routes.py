import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.supabase_client import get_supabase
from app.auth_utils import role_required

bp = Blueprint("seller", __name__, url_prefix="/seller")


@bp.route("/dashboard")
@role_required("seller")
def dashboard():
    supabase = get_supabase()
    seller_id = session["user_id"]

    products = supabase.table("products").select("*").eq(
        "seller_id", seller_id
    ).order("created_at", desc=True).execute().data

    order_items = supabase.table("order_items").select(
        "*, orders(status, created_at), products(name)"
    ).eq("seller_id", seller_id).order("created_at", desc=True).execute().data

    total_sales = sum(oi["quantity"] * oi["unit_price"] for oi in order_items)
    pending_count = len([p for p in products if p["status"] == "pending"])
    approved_count = len([p for p in products if p["status"] == "approved"])

    return render_template(
        "seller/dashboard.html",
        products=products,
        order_items=order_items,
        total_sales=total_sales,
        pending_count=pending_count,
        approved_count=approved_count,
    )


@bp.route("/products")
@role_required("seller")
def my_products():
    supabase = get_supabase()
    products = supabase.table("products").select(
        "*, categories(name), product_images(image_url, is_cover)"
    ).eq("seller_id", session["user_id"]).order("created_at", desc=True).execute().data
    return render_template("seller/products.html", products=products)


@bp.route("/products/add", methods=["GET", "POST"])
@role_required("seller")
def add_product():
    supabase = get_supabase()

    if request.method == "POST":
        name = request.form["name"]
        description = request.form.get("description", "")
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        category_id = request.form.get("category_id") or None
        condition = request.form.get("condition", "used")
        video_url = request.form.get("video_url", "").strip() or None
        discount_percent = int(request.form.get("discount_percent", 0))

        product = supabase.table("products").insert({
            "seller_id": session["user_id"],
            "name": name,
            "description": description,
            "price": price,
            "stock": stock,
            "category_id": category_id,
            "condition": condition,
            "video_url": video_url,
            "discount_percent": discount_percent,
            "status": "pending",  # ต้องรอแอดมินอนุมัติก่อน
        }).execute().data[0]

        # อัปโหลดรูปภาพไปยัง Supabase Storage (bucket ชื่อ "product-images")
        files = request.files.getlist("images")
        upload_failed = 0
        for idx, f in enumerate(files):
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                storage_path = f"{product['id']}/{uuid.uuid4()}{ext}"
                file_bytes = f.read()
                try:
                    supabase.storage.from_("product-images").upload(
                        storage_path, file_bytes, {"content-type": f.mimetype}
                    )
                    public_url = supabase.storage.from_("product-images").get_public_url(storage_path)
                    supabase.table("product_images").insert({
                        "product_id": product["id"],
                        "image_url": public_url,
                        "is_cover": idx == 0,  # รูปแรกที่อัปโหลดเป็นรูปปกอัตโนมัติ
                    }).execute()
                except Exception:
                    upload_failed += 1

        if upload_failed:
            flash(f"บันทึกสินค้าสำเร็จ แต่มีรูปภาพ {upload_failed} รูปอัปโหลดไม่ผ่าน (ไฟล์อาจใหญ่เกินไปหรือเน็ตหลุด) ลองเข้าไปเพิ่มรูปใหม่ที่หน้าแก้ไขสินค้าได้", "warning")
        else:
            flash("เพิ่มสินค้าสำเร็จ รอแอดมินตรวจสอบก่อนขึ้นแสดง", "success")
        return redirect(url_for("seller.my_products"))

    categories = supabase.table("categories").select("*").execute().data
    return render_template("seller/add_product.html", categories=categories)


@bp.route("/products/<product_id>/edit", methods=["GET", "POST"])
@role_required("seller")
def edit_product(product_id):
    supabase = get_supabase()
    product = supabase.table("products").select("*").eq(
        "id", product_id
    ).eq("seller_id", session["user_id"]).single().execute().data

    if not product:
        flash("ไม่พบสินค้า", "danger")
        return redirect(url_for("seller.my_products"))

    if request.method == "POST":
        supabase.table("products").update({
            "name": request.form["name"],
            "description": request.form.get("description", ""),
            "price": float(request.form["price"]),
            "stock": int(request.form["stock"]),
            "category_id": request.form.get("category_id") or None,
            "condition": request.form.get("condition", "used"),
            "video_url": request.form.get("video_url", "").strip() or None,
            "discount_percent": int(request.form.get("discount_percent", 0)),
            "status": "pending",  # แก้ไขแล้วต้องรออนุมัติใหม่
        }).eq("id", product_id).execute()

        # ลบรูปที่ผู้ใช้ติ๊กเลือกลบ
        delete_ids = request.form.getlist("delete_image_ids")
        for image_id in delete_ids:
            supabase.table("product_images").delete().eq("id", image_id).execute()

        # เปลี่ยนรูปปก (ถ้าเลือกไว้)
        cover_id = request.form.get("cover_image_id")
        if cover_id:
            supabase.table("product_images").update({"is_cover": False}).eq(
                "product_id", product_id
            ).execute()
            supabase.table("product_images").update({"is_cover": True}).eq(
                "id", cover_id
            ).execute()

        # เพิ่มรูปใหม่ (ถ้ามี)
        existing_count = supabase.table("product_images").select(
            "id", count="exact"
        ).eq("product_id", product_id).execute().count or 0
        new_files = request.files.getlist("new_images")
        upload_failed = 0
        for idx, f in enumerate(new_files):
            if f and f.filename:
                ext = os.path.splitext(f.filename)[1]
                storage_path = f"{product_id}/{uuid.uuid4()}{ext}"
                file_bytes = f.read()
                try:
                    supabase.storage.from_("product-images").upload(
                        storage_path, file_bytes, {"content-type": f.mimetype}
                    )
                    public_url = supabase.storage.from_("product-images").get_public_url(storage_path)
                    supabase.table("product_images").insert({
                        "product_id": product_id,
                        "image_url": public_url,
                        # ถ้ายังไม่เคยมีรูปเลยมาก่อน ให้รูปแรกที่เพิ่มเป็นปกอัตโนมัติ
                        "is_cover": existing_count == 0 and idx == 0,
                    }).execute()
                except Exception:
                    upload_failed += 1

        if upload_failed:
            flash(f"บันทึกข้อมูลสำเร็จ แต่มีรูปภาพ {upload_failed} รูปอัปโหลดไม่ผ่าน (ไฟล์อาจใหญ่เกินไปหรือเน็ตหลุด) ลองใหม่อีกครั้ง", "warning")
        else:
            flash("แก้ไขสินค้าแล้ว รอแอดมินตรวจสอบอีกครั้ง", "success")
        return redirect(url_for("seller.my_products"))

    categories = supabase.table("categories").select("*").execute().data
    images = supabase.table("product_images").select("*").eq(
        "product_id", product_id
    ).order("is_cover", desc=True).execute().data
    return render_template(
        "seller/edit_product.html", product=product, categories=categories, images=images
    )


@bp.route("/products/<product_id>/delete", methods=["POST"])
@role_required("seller")
def delete_product(product_id):
    supabase = get_supabase()
    try:
        supabase.table("products").delete().eq(
            "id", product_id
        ).eq("seller_id", session["user_id"]).execute()
        flash("ลบสินค้าแล้ว", "info")
    except Exception:
        flash("ลบไม่ได้ เพราะสินค้านี้เคยมีคนสั่งซื้อไปแล้ว (มีประวัติคำสั่งซื้อผูกอยู่)", "danger")
    return redirect(url_for("seller.my_products"))


@bp.route("/orders/<item_id>/status", methods=["POST"])
@role_required("seller")
def update_order_status(item_id):
    """อัปเดตสถานะคำสั่งซื้อ (ผ่าน order_items -> orders)"""
    supabase = get_supabase()
    new_status = request.form["status"]
    order_id = request.form["order_id"]
    supabase.table("orders").update({"status": new_status}).eq("id", order_id).execute()
    flash("อัปเดตสถานะคำสั่งซื้อแล้ว", "success")
    return redirect(url_for("seller.dashboard"))
